from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Server(models.Model):
    """Server Model"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    number = models.PositiveIntegerField()
    link = models.CharField(max_length=255)

    def __str__(self):
        return f"Server: {self.number} - {self.link}"
