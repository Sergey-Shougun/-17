import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NewsPaper.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("="*50)
print("Тест отправки email через SMTP")
print(f"Используем сервер: {settings.EMAIL_HOST}")
print(f"Порт: {settings.EMAIL_PORT}")
print(f"Пользователь: {settings.EMAIL_HOST_USER}")
print("="*50)

send_mail(
    'Тест рассылки NewsPortal',
    'Это тестовое сообщение от вашего приложения.',
    settings.DEFAULT_FROM_EMAIL,
    ['Zonanso@yandex.ru'],
    fail_silently=False,
)

print("Тестовое письмо отправлено! Проверьте вашу почту.")