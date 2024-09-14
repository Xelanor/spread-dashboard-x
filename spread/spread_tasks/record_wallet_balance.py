import logging
import asyncio
import traceback
from datetime import timedelta
from time import sleep

from app.celery import app
from django.core.cache import cache
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime

from spread.models import Wallet, ExchangeApi
from exchanges import api_classes

logger = logging.getLogger()


@app.task
def record_wallet_balance():
    tickers_data = cache.get("tickers")
    if not tickers_data:
        logger.error("tickers data not found in cache")
        return False

    total = 0

    api_objects = ExchangeApi.objects.filter()
    for api_object in api_objects:
        exchange = api_object.exchange.name
        public_key = api_object.public_key
        private_key = api_object.private_key
        group = api_object.group
        kyc = api_object.kyc

        api = api_classes[exchange]("", public_key, private_key, group, kyc)

        try:
            balances = api.get_account_balance()
        except:
            logger.error(traceback.format_exc())
            continue

        exchange_total = 0
        for tick in balances:
            try:
                ticker = f"{tick}/USDT"
                if tick == "USDT":
                    total += balances[tick]["total"]
                    exchange_total += balances[tick]["total"]

                if ticker in tickers_data[exchange]:
                    total += (
                        balances[tick]["total"] * tickers_data[exchange][ticker]["bid"]
                    )
                    exchange_total += (
                        balances[tick]["total"] * tickers_data[exchange][ticker]["bid"]
                    )
            except:
                continue

        logger.info(f"{exchange} total: {exchange_total}")

    try:
        btc_price = tickers_data["Mexc"]["BTC/USDT"]["bid"]
    except:
        btc_price = None

    Wallet.objects.create(total=total, details={"btc": btc_price})
