import asyncio
from datetime import datetime, timedelta

from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.cache import cache
from django.utils.timezone import now

from dashboard.utils import async_maker_server_request
from dashboard.models import Server


@api_view(["GET"])
def spread_bots_data(request):
    if request.method == "GET":
        url = "/spread"
        servers = list(Server.objects.filter().values())

        data = asyncio.run(async_maker_server_request(servers, "GET", url))

        result = {"bots": []}
        for server in data:
            bots = data[server]["bots"]
            for bot in bots:
                bot_id = bot["settings"]["id"]
                key = f"{server}_{bot_id}"
                bot["settings"]["key"] = key
                bot["settings"]["server"] = server

                result["bots"].append(bot)

        return Response(result)


@api_view(["POST"])
def spread_transactions(request):
    body = request.data
    bot_id = body["bot_id"]
    server = body.get("server", None)

    if server:
        servers = list(Server.objects.filter(number=server).values())
    else:
        servers = list(Server.objects.filter().values())

    url = "/spread/transactions"
    data = asyncio.run(
        async_maker_server_request(servers, "POST", url, {"bot_id": bot_id})
    )

    if bot_id == "all-transactions":
        result = {
            "ticker": "All Transactions",
            "total_profit": 0,
            "total_volume": 0,
            "transactions": [],
        }
        for key in data:
            result["transactions"].extend(data[key]["transactions"])
            result["total_profit"] += data[key]["total_profit"]
            result["total_volume"] += data[key]["total_volume"]

        result["transactions"].sort(
            key=lambda x: datetime.fromisoformat(
                x["created_at"].replace("Z", "+00:00")
            ),
            reverse=True,
        )

        return Response(result)

    else:
        return Response(data[server])
