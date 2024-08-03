from django.urls import path, include

from spread import views

urlpatterns = [
    path("", views.spread_bots_data),
    path("transactions", views.spread_transactions, name="spread_transactions"),
]
