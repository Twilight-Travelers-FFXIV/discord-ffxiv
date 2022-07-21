from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # initializing scheduler
    scheduler = AsyncIOScheduler()

    # sends "Your Message" at 12PM and 18PM (Local Time)
    scheduler.add_job(func, CronTrigger(minute="*", second="0"))

    # starting the scheduler
    scheduler.start()
