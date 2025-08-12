from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def add_user_to_common_group(sender, instance, created, **kwargs):
    if created:
        try:
            common_group = Group.objects.get(name='common')
            instance.groups.add(common_group)
            print(f"Пользователь {instance.username} добавлен в группу 'common'")
        except Group.DoesNotExist:
            print("Группа 'common' не найдена. Создайте ее в админке.")
