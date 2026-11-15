import json
import pandas as pd
import requests
from dateutil import parser
from datetime import datetime



def get_hood_stock_price(id, secret, trading_dates):

    BASE_URL = "https://data.alpaca.markets/v2/stocks/bars"
    HEADERS = {
        "accept": "application/json",
        "APCA-API-KEY-ID": f"{id}",
        "APCA-API-SECRET-KEY": f"{secret}"
    }

    PARAMS = {
        "symbols" : "HOOD",
        "timeframe" : "1D",
        "start" : f"{trading_dates[0]}",
        "end" : f"{trading_dates[-1]}",
        "limit" : 10000,
        "adjustment" : "all",
    }

    return [{"t": parser.isoparse(elem["t"]).strftime("%Y-%m-%d"), "c": elem["c"]} for elem in requests.get(BASE_URL, params = PARAMS, headers = HEADERS).json()["bars"]["HOOD"]]



def get_daily_changes(lst):

    return [{"t" : lst[i+1]["t"], "c" : ((lst[i+1]["c"]-lst[i]["c"])/lst[i]["c"]) * 100} for i in range(len(lst)-1)]


def get_alpaca_id():

    with open("api_keys/al_api_key.json") as f:
        id = json.load(f)

    return id


def get_trading_days():

    with open(f"data/trading_days.json") as f:
        dates = json.load(f)

    return dates


def add_hood_price(df, hood_prices):

    for data_point in hood_prices:
        df.loc[data_point["t"], "HOOD"] = data_point["c"]


    return df.dropna()


def save_df(df, fname):

    df.to_csv(f"data/{fname}.csv")
    df.to_parquet(f"data/{fname}.parquet")


def main():
    ALPACA_ID, ALPACA_SECRET = get_alpaca_id()["key"], get_alpaca_id()["secret"]
    TRADING_DATES = get_trading_days()
    df_index = pd.read_parquet("data/8.index.parquet")

    #print(get_hood_stock_price(ALPACA_ID, ALPACA_SECRET, TRADING_DATES))

    #print(add_hood_price(df_index, get_daily_changes(get_hood_stock_price(ALPACA_ID, ALPACA_SECRET, TRADING_DATES))))

    save_df(add_hood_price(df_index, get_daily_changes(get_hood_stock_price(ALPACA_ID, ALPACA_SECRET, TRADING_DATES))), "9.index_with_hood")

main()