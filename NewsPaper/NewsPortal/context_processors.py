from django.utils.safestring import mark_safe


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
