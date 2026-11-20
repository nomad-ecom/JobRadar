import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings
from app.db import get_sessionmaker, init_db
from app.services.pipeline import crawl_and_match

logger = logging.getLogger("jobradar.scheduler")


def scheduled_crawl() -> None:
    init_db()
    session = get_sessionmaker()()
    try:
        runs = crawl_and_match(session)
        logger.info("crawl finished: %s", [(run.source, run.status, run.jobs_new) for run in runs])
    except Exception:
        logger.exception("scheduled crawl failed")
        session.rollback()
    finally:
        session.close()


def start_scheduler() -> BackgroundScheduler | None:
    settings = get_settings()
    if not settings.scheduler:
        return None
    scheduler = BackgroundScheduler(timezone="UTC")
    first = datetime.now(timezone.utc) + timedelta(minutes=max(settings.crawl_interval_minutes, 1))
    scheduler.add_job(
        scheduled_crawl,
        "interval",
        minutes=max(settings.crawl_interval_minutes, 1),
        next_run_time=first,
        id="crawl",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
