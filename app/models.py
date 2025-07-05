from django.db import models

class UserLogin(models.Model):
    telegram_id = models.CharField(primary_key=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    password = models.CharField(max_length=128, blank=True, null=True)
    telegram_first_name = models.CharField(max_length=100, null=True, blank=True)
    telegram_last_name = models.CharField(max_length=100, null=True, blank=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    session = models.JSONField(null=True, blank=True)

    def __str__(self):
        return str(self.telegram_id)