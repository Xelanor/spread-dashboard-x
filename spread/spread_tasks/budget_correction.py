import logging
import asyncio
import traceback
from datetime import timedelta
import math

from app.celery import app
from django.core.cache import cache
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime


from dashboard.utils import request
from dashboard.models import Server

logger = logging.getLogger()


@app.task
def budget_correction():
    bots = cache.get("botDetails")
    tickers_data = cache.get("tickers")

    if not (bots and tickers_data):
        logger.error("Bot details or tickers data not found in cache")
        return False

    # Todo: Make it Better

    for bot in bots:
        ticker = bot["settings"]["ticker"]
        logger.info(f"Bot: {ticker} is being checked for budget correction")

        try:
            current_budget = bot["settings"]["budget"]
            point = bot["settings"]["point"]
            profit_7 = bot["profits"]["profit_7days"]
            created_at = parse_datetime(bot["settings"]["created_at"])
            bot_age = (now() - created_at).days + 1
            bot_age = min(bot_age, 7)
        except:
            continue

        if point == 3:
            continue

        ideal_budget = None

        # * Variables
        infancy_days = 3
        initial_budget = 50
        zero_budget_loss = -5
        max_budget = 500

        if profit_7 < zero_budget_loss:
            # * Zero Budget Loss
            ideal_budget = 0
            logger.info(f"Bot: {ticker} has zero budget loss")
        else:
            daily_profit = profit_7 / bot_age
            logger.info(f"Bot: {ticker} has daily profit of {daily_profit}")

            if daily_profit < 2:
                # * Low Profit
                ideal_budget = initial_budget
            else:
                # * High Profit
                ideal_budget = daily_profit * 30

        ideal_budget = min(ideal_budget, max_budget)
        logger.info(f"Bot: {ticker} has ideal budget of {ideal_budget}")

        #! Round up budget
        if ideal_budget < 200:
            ideal_budget = int(math.ceil(ideal_budget / 10.0)) * 10
        elif ideal_budget < 500:
            ideal_budget = int(math.ceil(ideal_budget / 50.0)) * 50
        else:
            ideal_budget = int(math.ceil(ideal_budget / 100.0)) * 100

        if ideal_budget == int(current_budget):
            continue

        db_server = Server.objects.get(number=bot["settings"]["server"])
        host = db_server.link
        url = "/spread/budget-update"
        res = request(
            "POST",
            host,
            url,
            {
                "bot_id": bot["settings"]["id"],
                "new_budget": ideal_budget,
            },
        )
