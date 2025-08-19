import logging
from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Subscriber, Post

logger = logging.getLogger(__name__)


@shared_task
def send_weekly_digest():
    week_ago = timezone.now() - timedelta(days=7)
    subscribers = Subscriber.objects.filter(
        unsubscribed_at__isnull=True,
        user__email__isnull=False
    ).prefetch_related('categories').distinct()

    total_sent = 0
    errors = 0

    for subscriber in subscribers:
        user = subscriber.user
        categories = subscriber.categories.all()

        if not categories:
            logger.info(f"У подписчика {user.username} нет категорий для рассылки")
            continue

        try:
            posts = Post.objects.filter(
                categories__in=categories,
                created_at__gte=week_ago,
                post_type='NW'
            ).distinct().order_by('-created_at')

            if not posts:
                logger.info(f"Нет новых статей для подписчика {user.username}")
                continue

            context = {
                'posts': posts,
                'user': user,
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
                to=[user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            total_sent += 1
            logger.info(f"Sent weekly digest to {user.email}")
        except Exception as e:
            errors += 1
            logger.error(f"Error sending digest to {user.email}: {str(e)}")

    return f"Рассылка завершена. Отправлено: {total_sent}, ошибок: {errors}"


@shared_task
def send_new_post_notifications(post_id):
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        post = Post.objects.get(id=post_id)
        users = set()

        for category in post.categories.all():
            users.update(category.subscribers.all())

        for user in users:
            if user.email:
                html_content = render_to_string(
                    'email/new_post_notification.html',
                    {'post': post, 'user': user}
                )

                msg = EmailMultiAlternatives(
                    subject=post.title,
                    body='',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                logger.info(f"Sent new post notification to {user.email}")

    except Post.DoesNotExist:
        logger.error(f"Post with id {post_id} does not exist")
    except Exception as e:
        logger.error(f"Error in send_new_post_notifications: {str(e)}")