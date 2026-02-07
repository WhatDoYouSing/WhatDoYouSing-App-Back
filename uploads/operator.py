from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, DjangoJobStore
from django.db import close_old_connections
from .views import update_spotify


def start():
    scheduler=BackgroundScheduler()

    @scheduler.scheduled_job('cron', minute='0', second='0')
    def auto_check():
        close_old_connections()
        update_spotify()

    scheduler.start()