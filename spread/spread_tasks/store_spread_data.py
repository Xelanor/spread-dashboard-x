import logging
import asyncio
import traceback
from datetime import timedelta
from time import sleep

from app.celery import app
from django.core.cache import cache
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime

from spread.models import HistoricSpread

logger = logging.getLogger()


@app.task
def store_spread_data():
    today = now().date()
    four_days_ago = today - timedelta(days=4)
    HistoricSpread.objects.filter(created_at__date__lt=four_days_ago).delete()

    tickers_data = cache.get("tickers")

    if not tickers_data:
        logger.error("tickers data not found in cache")
        return False

    for exchange, tickers in tickers_data.items():
        if exchange not in ["Mexc"]:
            continue

        for ticker, ticker_data in tickers.items():
            ask = ticker_data["ask"]
            bid = ticker_data["bid"]
            try:
                spread = ask / bid - 1
            except:
                continue

            try:
                HistoricSpread.objects.create(
                    exchange=exchange, ticker=ticker, spread=spread
                )
            except Exception as e:
                logger.error(
                    f"Error while storing spread data for {ticker}-{exchange}: {e}"
                )
                continue
