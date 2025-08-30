from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, DjangoJobStore
from .views import update_spotify


def start():
    scheduler=BackgroundScheduler()
    # scheduler.add_jobstore(DjangoJobStore(), 'djangojobstore')
    # register_events(scheduler)

    @scheduler.scheduled_job('cron', minute='0', second='0')
    def auto_check():
        update_spotify()

    scheduler.start()