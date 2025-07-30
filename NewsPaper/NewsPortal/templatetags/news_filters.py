from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()


@register.filter(name='censor')
def censor(value):
    # Проверка типа данных
    if not isinstance(value, str):
        raise TypeError(f"Фильтр 'censor' применяется к строке, а не к {type(value)}")

    # Список нежелательных слов
    BAD_WORDS = [
        'анус',
        'аборт',
        'бздун',
        'беспезды',
        'бздюх',
        'бля',
        'блудилище',
        'блядво',
        'блядеха',
        'блядина',
        'блядистка',
        # этот список можно продолжать до бесконечности, но я не буду
    ]

    # Шаблон для поиска слов с учетом границ слов
    pattern = r'\b(' + '|'.join(BAD_WORDS) + r')\b'
    regex = re.compile(pattern, re.IGNORECASE)

    # Функция для замены слова на цензурированную версию
    def replace_match(match):
        word = match.group(0)
        return word[0] + '*' * (len(word) - 1)

    # Применятся замена ко всем найденным словам
    return mark_safe(regex.sub(replace_match, value))