import requests
import functools
import asyncio
import json


def parse_response(res, req_type=None):
    if res is None:
        return None
    elif res.status_code == 200:
        obj = json.loads(res.text)
        return obj
    else:
        obj = json.loads(res.text)
        return obj


def request(method, host, url, params=None):
    url = "{}{}".format(host, url)
    res = requests.request(method, url, json=params)
    return parse_response(res)


async def async_maker_server_request(servers, method, url, params=None):
    page = {}
    loop = asyncio.get_event_loop()
    tasks = []
    _servers = []
    for server in servers:
        number = server["number"]
        link = server["link"]

        partial_function = functools.partial(request, method, link, url, params)

        tasks.append(loop.run_in_executor(None, partial_function))
        _servers.append(number)

    results = await asyncio.gather(*tasks)
    for index, number in enumerate(_servers):
        page[number] = results[index]

    return page
