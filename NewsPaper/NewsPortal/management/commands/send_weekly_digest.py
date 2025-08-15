from django.core.management.base import BaseCommand
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from ...models import Subscriber, Category, Post
from datetime import timedelta


class Command(BaseCommand):
    help = 'Send weekly digest to subscribers'

    def handle(self, *args, **options):

        week_ago = timezone.now() - timedelta(days=7)

        for subscriber in Subscriber.objects.all():
            user = subscriber.user

            if not user.email:
                continue

            subscribed_categories = user.subscribed_categories.all()

            if not subscribed_categories:
                continue

            new_posts = Post.objects.filter(
                categories__in=subscribed_categories,
                created_at__gte=week_ago,
                created_at__lte=timezone.now()
            ).distinct().order_by('-created_at')

            if not new_posts:
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

                self.stdout.write(f"Отправлена рассылка для {user.email}")
            except Exception as e:
                self.stderr.write(f"Ошибка отправки для {user.email}: {str(e)}")
