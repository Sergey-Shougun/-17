from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import PostCategory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from allauth.account.signals import email_confirmed
import logging
from .models import Subscriber
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post
from .tasks import send_new_post_notifications
from celery.exceptions import OperationalError
from django.db import transaction

User = get_user_model()
logger = logging.getLogger(__name__)
logger.info("############################################")
logger.info("### Signals module loaded successfully! ###")
logger.info("############################################")

logger.info("Модуль signals.py загружен! Сигналы должны работать")

# signals.py


@receiver(post_save, sender=Post)
def notify_subscribers(sender, instance, created, **kwargs):
    if created and instance.post_type == 'NW':
        try:
            # Асинхронная отправка
            send_new_post_notifications.delay(instance.id)
        except OperationalError as e:
            logger.error(f"Celery error: {str(e)}")
            logger.info("Falling back to synchronous execution")

            # Синхронная отправка в случае ошибки
            transaction.on_commit(
                lambda: send_new_post_notifications(instance.id)
            )


@receiver(email_confirmed)
def send_welcome_email(request, email_address, **kwargs):
    user = email_address.user
    logger.info(f"Sending welcome email to {user.email}")

    context = {
        'user': user,
        'site_url': settings.SITE_URL,
        'site_name': settings.SITE_NAME
    }

    html_content = render_to_string('email/welcome.html', context)

    msg = EmailMultiAlternatives(
        subject=f"Добро пожаловать на {settings.SITE_NAME}!",
        body='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_content, "text/html")

    try:
        msg.send()
        logger.info(f"Welcome email sent to {user.email}")
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")


@receiver(post_save, sender=User)
def create_subscriber_profile(sender, instance, created, **kwargs):
    if created:
        Subscriber.objects.get_or_create(user=instance)


@receiver(post_save, sender=PostCategory)
def notify_on_category_add(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        category = instance.category

        logger.info(f"Обработчик notify_on_category_add вызван для связи: {post.title} -> {category.name}")

        if post.post_type != 'NW':
            logger.info(f"Пост {post.id} не является новостью - пропускаем")
            return

        subscribers = category.subscribers.all()
        logger.info(f"Найдено подписчиков категории {category.name}: {subscribers.count()}")

        if not subscribers:
            logger.info("Нет подписчиков - пропускаем")
            return

        for user in subscribers:

            if user == post.author.user:
                logger.info(f"Пропускаем автора поста: {user.username}")
                continue

            if user.email:
                try:
                    logger.info(f"Отправляем уведомление для: {user.email}")

                    html_content = render_to_string('email/new_post_notification.html', {
                        'post': post,
                        'username': user.username,
                        'site_url': settings.SITE_URL,
                        'site_name': settings.SITE_NAME
                    })

                    msg = EmailMultiAlternatives(
                        subject=post.title,
                        body='',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[user.email],
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send(fail_silently=False)

                    logger.info(f"Уведомление отправлено на {user.email}")
                except Exception as e:
                    logger.error(f"Ошибка отправки: {str(e)}")
            else:
                logger.warning(f"У пользователя {user.username} нет email")
    else:
        logger.info("Связь не новая - пропускаем")


@receiver(post_save, sender=Post)
def notify_subscribers(sender, instance, created, **kwargs):
    logger.info(f"Сработал сигнал post_save для: {instance.title}")
    logger.info(f"Тип поста: {instance.post_type}, Создан: {created}")

    if created and instance.post_type == 'NW':
        logger.info(f"Обрабатываем новую новость: {instance.title}")

        try:

            post_categories = PostCategory.objects.filter(post=instance)
            categories = [pc.category for pc in post_categories]

            logger.info(f"Найдено категорий: {len(categories)}")

            if not categories:
                logger.warning("У новости нет категорий. Уведомления не отправляются.")
                return

            subscribers = set()
            for category in categories:
                logger.info(f"Обрабатываем категорию: {category.name}")
                subscribers.update(category.subscribers.all())

            logger.info(f"Всего уникальных подписчиков: {len(subscribers)}")

            if not subscribers:
                logger.warning("Нет подписчиков для уведомления")
                return

            for user in subscribers:

                if user == instance.author.user:
                    logger.info(f"Пропускаем автора: {user.username}")
                    continue

                if user.email:
                    try:
                        logger.info(f"Пытаемся отправить письмо для: {user.email}")

                        html_content = render_to_string('email/new_post_notification.html', {
                            'post': instance,
                            'username': user.username,
                            'site_url': settings.SITE_URL,
                            'site_name': settings.SITE_NAME
                        })

                        msg = EmailMultiAlternatives(
                            subject=instance.title,
                            body='',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[user.email],
                        )
                        msg.attach_alternative(html_content, "text/html")

                        msg.send(fail_silently=False)
                        logger.info(f"Письмо отправлено на {user.email}")

                    except Exception as e:
                        logger.error(f"Ошибка отправки письма: {str(e)}", exc_info=True)
                else:
                    logger.warning(f"У пользователя {user.username} нет email")

        except Exception as e:
            logger.error(f"Критическая ошибка в обработчике: {str(e)}", exc_info=True)
    else:
        logger.info("Пост не является новой новостью - пропускаем")


@receiver(post_save, sender=User)
def add_user_to_common_group(sender, instance, created, **kwargs):
    logger.info(f"Обработчик add_user_to_common_group вызван для пользователя {instance.id}")

    if created:
        try:
            common_group, created = Group.objects.get_or_create(name='common')
            instance.groups.add(common_group)
            logger.info(f"Пользователь {instance.username} добавлен в группу 'common'")

            from .models import Author
            Author.objects.get_or_create(user=instance)
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя в группу: {str(e)}")


def send_author_request_email(user):
    subject = f'Новая заявка на статус автора: {user.username}'
    html_message = render_to_string('email/author_request.html', {
        'user': user,
        'admin_url': f'{settings.SITE_URL}/admin/NewsPortal/author/'
    })

    send_mail(
        subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_EMAIL],
        html_message=html_message,
        fail_silently=False
    )
