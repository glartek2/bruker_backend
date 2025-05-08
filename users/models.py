from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
        }
