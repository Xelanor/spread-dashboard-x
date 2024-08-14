import logging
import asyncio
import traceback
from datetime import timedelta

from app.celery import app
from django.core.cache import cache
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime


from dashboard.utils import request
from dashboard.models import Server

logger = logging.getLogger()


@app.task
def average_correction():
    bots = cache.get("botDetails")
    tickers_data = cache.get("tickers")

    if not (bots and tickers_data):
        logger.error("Bot details or tickers data not found in cache")
        return False

    for bot in bots:
        try:
            exchange = bot["settings"]["exchange"]
            ticker = bot["settings"]["ticker"]
            average_correction_minutes = bot["settings"]["average_correction_minutes"]
            average_correction_rate = bot["settings"]["average_correction_rate"]
            last_sell_order_date = parse_datetime(
                bot["settings"]["last_sell_order_date"]
            )
            average_price = bot["settings"]["average_price"]
            sellable_quantity = bot["settings"]["sellable_quantity"]
            ask_price = tickers_data[exchange][ticker]["ask"]
        except Exception as e:
            logger.error(f"Bot: {bot['settings']['ticker']} has missing data, {e}")
            continue

        if sellable_quantity * average_price < 6:
            logger.info(
                f"Bot: {bot['settings']['ticker']} has less than 6 USD worth of sellable quantity"
            )
            continue

        if last_sell_order_date + timedelta(minutes=average_correction_minutes) > now():
            logger.info(
                f"Bot: {bot['settings']['ticker']} has not reached average correction time"
            )
            continue

        new_avg_price = ask_price * (1 - average_correction_rate)

        db_server = Server.objects.get(number=bot["settings"]["server"])
        host = db_server.link
        url = "/spread/average-correction"
        res = request(
            "POST",
            host,
            url,
            {
                "bot_id": bot["settings"]["id"],
                "new_average": new_avg_price,
            },
        )
