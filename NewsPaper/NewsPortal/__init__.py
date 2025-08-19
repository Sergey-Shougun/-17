from celery import app as celery_app

default_app_config = 'NewsPortal.apps.NewsPortalConfig'
__all__ = ('celery_app',)
