import logging
import asyncio
import traceback

from app.celery import app
from django.core.cache import cache

from dashboard.utils import async_maker_server_request
from dashboard.models import Server

logger = logging.getLogger()


@app.task
def fetch_bot_details():
    async def async_bot_details(servers):
        url = "/spread"
        data = await async_maker_server_request(servers, "GET", url)
        return data

    try:
        servers = list(Server.objects.filter().values())
        data = asyncio.run(async_bot_details(servers))

        spread_bots = []
        for server in data:
            bots = data[server]["bots"]
            for bot in bots:
                bot_id = bot["settings"]["id"]
                key = f"{server}_{bot_id}"
                bot["settings"]["key"] = key
                bot["settings"]["server"] = server

                spread_bots.append(bot)

        cache.set("botDetails", spread_bots, 120)

    except:
        logger.error(traceback.format_exc())
