import asyncio
import logging
import os

from celery.signals import worker_process_init

from backend.core.factories.pipeline_factory import (
    build_merge_topics_pipeline,
    build_process_chat_block_pipeline,
    build_process_message_pipeline,
    build_split_topics_pipeline,
)
from backend.db.session import SessionLocal
from backend.db.storages.chat_buffer_storage import ChatBufferStorage
from backend.queue.celery_app import celery_app

logger = logging.getLogger(__name__)


_worker_loop: asyncio.AbstractEventLoop | None = None


@worker_process_init.connect
def _init_worker_loop(**kwargs):
    global _worker_loop
    _worker_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_worker_loop)
    logger.debug("Worker event loop initialized pid=%s", os.getpid())


def _run_async(coro):
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop.run_until_complete(coro)


@celery_app.task(bind=True, max_retries=3)
def process_message_pipeline_task(self, chat_id: int, message_id: int):
    logger.info("Start processing message chat_id=%s message_id=%s", chat_id, message_id)

    db = SessionLocal()

    try:
        pipeline = build_process_message_pipeline(db)
        pipeline.run(chat_id, message_id)
        db.commit()
        logger.info("Message processed successfully chat_id=%s message_id=%s", chat_id, message_id)

    except Exception as exc:
        db.rollback()
        logger.exception("Pipeline failed, retrying...")
        raise self.retry(exc=exc, countdown=5)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def process_chat_block_task(self, chat_id: int, message_thread_id: int | None):
    logger.info("Start processing chat block chat_id=%s", chat_id)

    db = SessionLocal()

    try:
        logger.info("Chat block process start")
        pipeline = build_process_chat_block_pipeline(db)

        _run_async(pipeline.run(chat_id, message_thread_id))

        db.commit()
        logger.info("Chat block processed successfully")

    except Exception as exc:
        db.rollback()
        logger.exception("Block pipeline failed, retrying...")
        raise self.retry(exc=exc, countdown=5)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=1)
def drain_buffer_task(self):
    logger.info("[DRAIN] Buffer drain started")

    db = SessionLocal()
    try:
        pairs = ChatBufferStorage(db).get_active_pairs()
        logger.info("[DRAIN] Found %s pairs to process", len(pairs))

        for chat_id, message_thread_id in pairs:
            process_chat_block_task.delay(chat_id, message_thread_id)
            logger.info("[DRAIN] Dispatched chat_id=%s thread=%s", chat_id, message_thread_id)

    except Exception as exc:
        logger.exception("[DRAIN] Buffer drain failed")
        raise self.retry(exc=exc, countdown=10)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=1)
def merge_topics_task(self):
    logger.info("[MERGE] Task started")

    db = SessionLocal()

    try:
        pipeline = build_merge_topics_pipeline(db)
        _run_async(pipeline.run())
        db.commit()
        logger.info("[MERGE] Task finished successfully")

    except Exception as exc:
        db.rollback()
        logger.exception("[MERGE] Task failed, retrying...")
        raise self.retry(exc=exc, countdown=60)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=1)
def split_topics_task(self):
    logger.info("[SPLIT] Task started")

    db = SessionLocal()

    try:
        pipeline = build_split_topics_pipeline(db)
        _run_async(pipeline.run())
        db.commit()
        logger.info("[SPLIT] Task finished successfully")

    except Exception as exc:
        db.rollback()
        logger.exception("[SPLIT] Task failed, retrying...")
        raise self.retry(exc=exc, countdown=60)

    finally:
        db.close()
