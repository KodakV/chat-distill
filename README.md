# Group Chat Summarization Bot

![CI](https://github.com/KodakV/chat-distill/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A self-hosted bot that reads your group chat, groups messages into topics, and keeps a running summary of each discussion — powered by a local LLM, no cloud required.

## Getting started

You'll need Docker, a running LLM server (any OpenAI-compatible API, e.g. [llama.cpp](https://github.com/ggml-org/llama.cpp)), an embedding server, and a bot token from [@BotFather](https://t.me/BotFather).

```bash
cp .env.example .env
# fill in BOT_TOKEN, LOCAL_LLM_MODEL, EMBEDDING_MODEL
docker compose up --build
docker compose exec backend alembic upgrade head
```

Add the bot to a group, grant it message read access — done.

## How it works

Messages are buffered per chat. Once the buffer fills, a pipeline runs: the LLM segments the batch into topic groups, scores each group for relevance (chatter and reactions get dropped), embeds the remainder, and matches against existing topics via vector similarity. Matched topics get their summaries updated; new topics are created. Background tasks periodically merge topics that converge and split ones that grow too broad.

```mermaid
flowchart TD
    MSG([fa:fa-comment Group message]) --> B1

    subgraph BOT["Bot"]
        B1[Receive message] --> B2[POST /v1/messages]
    end

    subgraph API["FastAPI"]
        B2 --> A1[Save message to DB]
        A1 --> A2[process_message_pipeline.delay]
    end

    subgraph STAGE1["Stage 1 · Buffer"]
        A2 --> C1[Add to ChatBuffer]
        C1 --> C2{buffer ≥ 20?}
        C2 -->|yes| C3[process_chat_block.delay]
    end

    subgraph BEAT["Celery Beat · periodic"]
        P1[drain_buffer] -->|every N sec| C3
        P2[merge_topics] -->|every M min| MERGE
        P3[split_topics] -->|every M min| SPLIT
    end

    subgraph STAGE2["Stage 2 · Block Pipeline  —  runs per cluster"]
        C3 --> D1[Lock buffer · fetch messages]
        D1 --> D2[Segmentation LLM\ngroup messages into clusters]
        D2 --> D3[Importance score LLM\n1–10]
        D3 --> D4{score ≥ 6?}
        D4 -->|drop| D2
        D4 -->|keep| D5[Embed cluster\nNomic embed]
        D5 --> D6[Vector search\npgvector cosine sim]
        D6 --> D7{best match?}
        D7 -->|sim ≥ 0.92\nhigh confidence| D8[Topic match LLM\nconfirm]
        D7 -->|0.82–0.92\ncandidates| D8
        D7 -->|sim < 0.82\nno candidates| D9
        D8 -->|match| D10[Update topic\nresummarize LLM]
        D8 -->|no match| D9[New topic\nextract title + summarize LLM]
    end

    subgraph MERGE["Merge Pipeline"]
        M1[Active topics last 24h] --> M2[Vector search ≥ 0.90]
        M2 --> M3[LLM: should_merge?]
        M3 -->|yes| M4[Reassign messages\nclose secondary\nresummarize primary]
    end

    subgraph SPLIT["Split Pipeline"]
        S1[Topics with ≥ 20 msgs] --> S2[LLM: should_split?\nreturn groups]
        S2 -->|yes| S3[Create sub-topics\nextract + summarize each\nclose original]
    end

    STAGE2 --> DB[(PostgreSQL\npgvector)]
    MERGE --> DB
    SPLIT --> DB

    DB --> CA[GET /v1/client/topics\nWebApp auth]
    CA --> UI([Client UI])
```

## Configuration

All settings live in `.env`. The ones you'll actually touch:

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Bot token from BotFather |
| `LOCAL_LLM_BASE_URL` | LLM server URL (OpenAI-compatible) |
| `LOCAL_LLM_MODEL` | Model name as served by the LLM server |
| `EMBEDDING_BASE_URL` | Embedding server URL |
| `EMBEDDING_MODEL` | Embedding model name |
| `TOPIC_MIN_IMPORTANCE` | Importance threshold (1–10) below which groups are dropped |
| `MATCH_CANDIDATE_THRESHOLD` | Cosine similarity for candidate topic lookup |
| `MATCH_HIGH_CONFIDENCE_THRESHOLD` | Cosine similarity for direct assignment (skips LLM confirmation) |

See `.env.example` for all values with defaults.

## Running tests

```bash
pip install pytest
PYTHONPATH=src pytest tests/ -v
```

## Tech

FastAPI · Celery + Redis · PostgreSQL + pgvector · aiogram 3 · Docker Compose
