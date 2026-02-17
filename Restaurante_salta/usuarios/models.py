from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    ROLES = (
        ('ADMIN', 'Administrador'),
        ('CAJERO', 'Cajero'),
        ('CLIENTE', 'Cliente'),
        ('COCINERO', 'Cocinero'),
    )

    rol = models.CharField(max_length=10, choices=ROLES, default='CLIENTE')
    is_active = models.BooleanField(default=True)  # Borrado lógico

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"

    def delete(self, *args, **kwargs):  # Sobrescribir el método delete
        self.is_active = False  # Marcar como inactivo
        self.save()

