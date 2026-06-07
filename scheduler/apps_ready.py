from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
import logging

logger = logging.getLogger(__name__)
_scheduler = None


def start():
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    from scheduler.jobs import sync_all_users_emails

    _scheduler = BackgroundScheduler(timezone='Asia/Kolkata')
    _scheduler.add_jobstore(DjangoJobStore(), 'default')
    _scheduler.add_job(
        sync_all_users_emails,
        trigger='interval',
        minutes=5,
        id='sync_emails',
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info("APScheduler started — email sync every 5 minutes.")