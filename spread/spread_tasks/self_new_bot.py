import logging
import asyncio
import traceback
from datetime import timedelta
from time import sleep
import statistics
import random

from app.celery import app
from django.core.cache import cache
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime
from django.db.models import F

from dashboard.utils import request, async_maker_server_request
from dashboard.models import Server
from spread.models import FinderScore, HistoricSpread
from exchanges.functions import exchange_functions
from exchanges.mexc.mexc_api import get_allowed_symbols as mexc_allowed_symbols
from spread.spread_tasks.calculate_scores import calculate_historical_data

logger = logging.getLogger()


def add_new_spread_bot(ticker, exchange, server):
    db_server = Server.objects.get(number=server)
    host = db_server.link
    url = "/spread/add-new-bot"
    res = request(
        "POST",
        host,
        url,
        {
            "ticker": ticker,
            "exchange": exchange,
        },
    )
    return True


@app.task
def self_new_bot():
    bots = cache.get("botDetails")
    tickers_data = cache.get("tickers")

    exchanges = ["Mexc"]

    if not (bots and tickers_data):
        logger.error("Bot details or tickers data not found in cache")
        return False

    servers = list(Server.objects.filter().values())
    url = "/spread/historical"
    old_bots_data = asyncio.run(async_maker_server_request(servers, "GET", url))

    historical = calculate_historical_data(old_bots_data)

    for exchange in exchanges:
        added_coin_count = 0

        running_bots = []
        active_coin_counts = {}

        for bot in bots:
            running_bots.append(
                f'{bot["settings"]["ticker"]}-{bot["settings"]["exchange"]}'
            )
            if bot["settings"]["exchange"] == exchange:
                if bot["settings"]["server"] not in active_coin_counts:
                    if exchange == "Mexc":
                        active_coin_counts[bot["settings"]["server"]] = 24

                active_coin_counts[bot["settings"]["server"]] -= 1

        # * Default symbol çek
        allowed_symbols = None
        if exchange == "Mexc":
            allowed_symbols = mexc_allowed_symbols()

        tickers = tickers_data.get(exchange, {})

        # * Gerekirse bunları shuffle yap
        ticker_keys = list(tickers.keys())
        random.shuffle(ticker_keys)

        for ticker in ticker_keys:
            # * Geçmiş çalışma verisini çek son 1 haftada çalıştıysa ekleme
            old_bot_data = historical.get(ticker, {}).get(exchange, {})
            last_transaction = old_bot_data.get("last_transaction", None)
            if last_transaction and last_transaction > now() - timedelta(days=7):
                continue

            tick = ticker.split("/")[0]
            mexc_ticker = f"{tick}USDT"

            # * Default symbolden kontrol et
            if (
                exchange == "Mexc"
                and allowed_symbols
                and mexc_ticker not in allowed_symbols
            ):
                continue

            # * Bizde olan coin filtresi
            if f"{ticker}-{exchange}" in running_bots:
                continue

            try:
                score_obj = FinderScore.objects.get(exchange=exchange, ticker=ticker)
            except:
                continue

            if score_obj.updated_at < now() - timedelta(hours=3):
                continue

            if score_obj.score <= 0:
                continue

            spreads = HistoricSpread.objects.filter(
                exchange=exchange, ticker=ticker
            ).values_list("spread", flat=True)

            if spreads:
                median_spread = statistics.median(spreads)
            else:
                continue

            # *: Historic spread 0.7den küçükse ekleme
            if median_spread < 0.7:
                continue

            # *: En çok yer olan server'a ekle
            max_key = max(active_coin_counts, key=active_coin_counts.get)
            max_value = active_coin_counts[max_key]

            if max_value <= 0:
                # Yer yok
                continue

            try:
                add_new_spread_bot(ticker, exchange, max_key)
                active_coin_counts[max_key] -= 1
                added_coin_count += 1
                logger.info(
                    f"Added new bot in Server: {max_key} - {exchange} - {ticker}"
                )
            except:
                logger.error(traceback.format_exc())
                continue

            if added_coin_count >= 3:
                break
