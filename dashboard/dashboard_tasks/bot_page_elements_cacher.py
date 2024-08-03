import asyncio
from django.core.cache import cache
import logging
import traceback

from spread import settings
from exchanges.functions import (
    async_exchange_tickers,
)

logger = logging.getLogger()


class BotPageElementsCacher:
    async def cache_async_exchange_tickers(self, exchanges):
        tickers = await async_exchange_tickers(exchanges)
        cache.set("tickers", tickers, 120 * 120)
        return tickers

    async def main(self, exchanges):
        while True:
            try:
                await self.cache_async_exchange_tickers(exchanges)
                await asyncio.sleep(12)
            except:
                logger.error(traceback.format_exc())
                await asyncio.sleep(12)
                continue

    def run(self):
        exchanges = settings.bot_page_exchanges
        asyncio.run(self.main(exchanges))
