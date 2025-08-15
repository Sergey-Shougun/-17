from django.utils.safestring import mark_safe
from django.conf import settings


def site_info(request):
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'News Portal'),
        'SITE_URL': getattr(settings, 'SITE_URL', 'localhost:8000'),
    }


def site_settings(request):
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_URL': settings.SITE_URL,
    }


def social_login_buttons(request):
    return {
        'social_login_buttons': mark_safe(
            '<a href="/accounts/yandex/login/?process=login" class="btn yandex-btn">'
            '<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Yandex_icon.svg/512px-Yandex_icon'
            '.svg.png"'
            'alt="Yandex" width="20"> Войти через Yandex'
            '</a>'
        )
    }


def author_status(request):
    return {
        'user_is_author': request.user.is_author if request.user.is_authenticated else False
    }
