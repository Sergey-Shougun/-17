import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.apps import apps
from django.db import DatabaseError
from apscheduler.jobstores.base import JobLookupError

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from django_apscheduler.jobstores import DjangoJobStore, register_events
except ImportError:
    BackgroundScheduler = None
    DjangoJobStore = None
    register_events = None

logger = logging.getLogger(__name__)


def send_weekly_digest():
    try:
        Subscriber = apps.get_model('NewsPortal', 'Subscriber')
        Post = apps.get_model('NewsPortal', 'Post')
    except LookupError as e:
        logger.error(f"Models not found: {str(e)}")
        return "Skipped: Models not available"

    week_ago = timezone.now() - timedelta(days=7)
    subscribers = Subscriber.objects.filter(
        unsubscribed_at__isnull=True
    ).prefetch_related('categories')

    total_sent = 0
    errors = 0

    for subscriber in subscribers:
        user = subscriber.user

        if not user.email:
            logger.info(f"Пропускаем пользователя без email: {user.username}")
            continue

        categories = subscriber.categories.all()

        if not categories:
            logger.info(f"У подписчика {user.username} нет категорий для рассылки")
            continue

        try:
            new_posts = Post.objects.filter(
                categories__in=categories,
                created_at__gte=week_ago,
                created_at__lte=timezone.now()
            ).distinct().order_by('-created_at')
        except DatabaseError as e:
            logger.error(f"Ошибка получения статей: {str(e)}")
            errors += 1
            continue

        if not new_posts:
            logger.info(f"Нет новых статей для подписчика {user.username}")
            continue

        try:
            context = {
                'user': user,
                'new_posts': new_posts,
                'site_url': settings.SITE_URL,
                'site_name': settings.SITE_NAME,
                'week_start': week_ago.date(),
                'week_end': timezone.now().date()
            }

            html_content = render_to_string('email/weekly_digest.html', context)

            msg = EmailMultiAlternatives(
                subject=f'Еженедельная подборка новостей от {settings.SITE_NAME}',
                body='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            subscriber.last_digest_sent = timezone.now()
            subscriber.save()

            total_sent += 1
            logger.info(f"Sent weekly digest to {user.email}")
        except Exception as e:
            errors += 1
            logger.error(f"Error sending digest to {user.email}: {str(e)}")

    return f"Рассылка завершена. Отправлено: {total_sent}, ошибок: {errors}"


def start_scheduler():
    if BackgroundScheduler is None or DjangoJobStore is None:
        logger.warning("APScheduler not installed. Skipping scheduler start.")
        return

    try:
        scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            send_weekly_digest,
            trigger='cron',
            day_of_week='mon',
            hour=9,
            minute=0,
            id='weekly_digest',
            max_instances=1,
            replace_existing=True,
        )

        register_events(scheduler)
        logger.info("Starting scheduler...")
        scheduler.start()
        logger.info("Scheduler started successfully")



    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
