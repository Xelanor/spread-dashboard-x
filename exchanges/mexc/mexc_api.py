from .utils import request


def get_mexc_product_details(ticker):
    url = "/api/v3/exchangeInfo"

    params = {"symbol": ticker}
    res = request("GET", url, params=params)
    res = res["symbols"][0]
    return res


def get_mexc_tickers():
    url = "/api/v3/ticker/24hr"
    res = request("GET", url)

    tickers = {}

    denominator = "USDT"
    for _ticker in res:
        if _ticker["symbol"].endswith(denominator):
            nominator = _ticker["symbol"][: -len(denominator)]

            symbol = f"{nominator}/{denominator}"
            tickers[symbol] = {}

            tickers[symbol]["ask"] = float(_ticker["askPrice"])
            tickers[symbol]["bid"] = float(_ticker["bidPrice"])
            tickers[symbol]["volume"] = float(_ticker["quoteVolume"])
            tickers[symbol]["rate"] = float(_ticker["priceChangePercent"])

    return tickers


def get_mexc_depth(ticker):
    url = "/api/v3/depth"

    params = {"symbol": ticker}
    res = request("GET", url, params=params)
    asks = res["asks"]
    bids = res["bids"]

    return asks, bids


def get_mexc_klines(ticker, age=False):
    url = "/api/v3/klines"

    ticker = f"{ticker.split('/')[0]}{ticker.split('/')[1]}"

    if age:
        params = {"symbol": ticker, "interval": "1d", "limit": 360}

    res = request("GET", url, params=params)
    klines = []

    for kline in res:
        date = kline[0]
        _open = float(kline[1])
        high = float(kline[2])
        low = float(kline[3])
        close = float(kline[4])
        volume = round(float(kline[7]), 2)
        klines.append(
            {
                "date": date,
                "open": _open,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )

    return klines


def get_allowed_symbols():
    url = "/api/v3/defaultSymbols"

    res = request("GET", url)
    res = res["data"]

    return res
