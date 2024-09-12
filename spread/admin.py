from django.contrib import admin

from spread.models import Wallet, SpreadTraderBlacklist, FinderScore, HistoricSpread

admin.site.register(Wallet)
admin.site.register(SpreadTraderBlacklist)
admin.site.register(FinderScore)
admin.site.register(HistoricSpread)
