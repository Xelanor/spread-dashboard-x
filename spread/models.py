from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Exchange(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class ExchangeApi(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    public_key = models.CharField(max_length=255)
    private_key = models.CharField(max_length=255)
    group = models.CharField(max_length=255, blank=True, null=True)
    kyc = models.CharField(max_length=255, default="")

    def __str__(self):
        return f"{self.exchange.name} - {self.kyc}"


class Wallet(models.Model):
    """Wallet model class"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.total} - {self.created_at}"


class SpreadTraderBlacklist(models.Model):
    """Spread Trader Blacklist Tickers"""

    exchange = models.CharField(max_length=255)
    ticker = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["exchange", "ticker"],
                name="Same blacklist ticker-excange cannot be used again",
            )
        ]

    def __str__(self):
        return f"{self.exchange} - {self.ticker}"
