from django.contrib import admin

from spread.models import Wallet, SpreadTraderBlacklist

admin.site.register(Wallet)
admin.site.register(SpreadTraderBlacklist)
