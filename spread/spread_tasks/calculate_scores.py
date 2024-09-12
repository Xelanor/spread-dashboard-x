import logging
import asyncio
import traceback
from datetime import timedelta
from time import sleep

from app.celery import app
from django.core.cache import cache
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime


from dashboard.utils import request, async_maker_server_request
from dashboard.models import Server
from spread.models import SpreadTraderBlacklist, FinderScore
from exchanges.functions import exchange_functions

logger = logging.getLogger()


def calculate_historical_data(old_bots_data):
    old_bots = []
    for server in old_bots_data:
        for bot in old_bots_data[server]:
            old_bots.append(bot)

    historical = {}
    for bot in old_bots:
        ticker = bot["ticker"]
        exchange = bot["exchange__name"]
        if ticker not in historical:
            historical[ticker] = {}

        if exchange not in historical[ticker]:
            historical[ticker][exchange] = {
                "added_count": 0,
                "total_profit": 0,
                "last_added": None,
                "last_transaction": None,
                "last_profit": 0,
            }

        historical[ticker][exchange]["added_count"] += 1
        historical[ticker][exchange]["total_profit"] += bot["profit"]
        historical[ticker][exchange]["last_added"] = parse_datetime(bot["created_at"])

        if bot["latest_tx"] != None:
            historical[ticker][exchange]["last_transaction"] = parse_datetime(
                bot["latest_tx"]
            )
        else:
            historical[ticker][exchange]["last_transaction"] = parse_datetime(
                bot["created_at"]
            )

        historical[ticker][exchange]["last_profit"] = bot["profit"]
    return historical


def calculate_finder_score(exchange, ticker, ticker_data, historical):
    score = 0
    details = ""

    age_klines = exchange_functions[exchange]["klines"](ticker, age=True)
    age = len(age_klines)
    sleep(0.5)

    if age < 14:
        score += -1000
        details += f"Rule: coin_age_min Value: {age} Threshold: 14 Score: -1000\n"

    if age > 60:
        score += 10
        details += f"Rule: coin_age_over Value: {age} Threshold: 60 Score: 10\n"

    old_bot_data = historical.get(ticker, {}).get(exchange, {})
    if not old_bot_data:
        score += 15
        details += "Rule: not_added_previously Score: 15\n"

    if old_bot_data.get("last_profit", 0) < -10:
        if old_bot_data.get("last_transaction") > now() - timedelta(days=10):
            score += -1000
            details += "Rule: last_loss_in_last_10_days Score: -1000\n"

    if old_bot_data.get("total_profit", 0) > 20:
        score += 10
        details += "Rule: total_profit_over_20 Score: 10\n"

    if ticker_data["volume"] < 100000:
        score += -1000
        details += f"Rule: volume_min Value: {ticker_data['volume']} Threshold: 100000 Score: -1000\n"

    if ticker_data["volume"] > 250000:
        score += 10
        details += f"Rule: volume_over Value: {ticker_data['volume']} Threshold: 250000 Score: 10\n"

    if ticker_data["rate"] > 0.3:
        score += -5
        details += (
            f"Rule: rate_over Value: {ticker_data['rate']} Threshold: 0.3 Score: -5\n"
        )

    if ticker_data["rate"] < -0.3:
        score += 5
        details += (
            f"Rule: rate_under Value: {ticker_data['rate']} Threshold: -0.3 Score: 5\n"
        )

    return score, details


@app.task
def calculate_scores():
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
        tickers = tickers_data.get(exchange, {})

        for ticker, ticker_data in tickers.items():
            if "3S" in ticker or "3L" in ticker or "5S" in ticker or "5L" in ticker:
                continue

            if ticker_data["volume"] < 60000:
                continue

            try:
                score, details = calculate_finder_score(
                    exchange, ticker, ticker_data, historical
                )

                try:
                    finder_score = FinderScore.objects.get(
                        exchange=exchange, ticker=ticker
                    )
                    finder_score.score = score
                    finder_score.details = details
                    finder_score.save()
                except:
                    FinderScore.objects.create(
                        exchange=exchange,
                        ticker=ticker,
                        score=score,
                        details=details,
                    )
            except:
                print(traceback.format_exc())
