from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group
from django.dispatch import receiver

@receiver(post_migrate)
def crear_grupos(sender, **kwargs):
    if sender.name == 'usuarios':  # Solo se ejecuta para la app 'usuarios'
        Group.objects.get_or_create(name='Cajero')
        Group.objects.get_or_create(name='Administrador')
