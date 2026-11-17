import requests
import json
import sys
import numpy as np
import math


def collect_mcap_data(tickers, api_key):

    BASE_URL = "https://data.businessquant.com/historic"
    params = {
        "slug" : "market-capitalization-daily",
        "ticker" : "",
        "period" : "3y",
        "api_key" : api_key}
    
    for industry in tickers:

        print(industry)

        tickers_split = list(np.array_split(list(tickers[industry]), math.ceil(len(tickers[industry]) / 5)))
        data = []
        for chunk in tickers_split:
            print(chunk)
            params["ticker"] = ",".join(chunk)
            response = requests.get(BASE_URL, params=params)
            for company in response.json()["data"]:
                tickers[industry][company["ticker"]]["mcap"].append(company["value"])
                tickers[industry][company["ticker"]]["mcap_time"].append(company["date"])


            
    save_my_json(tickers, "4.tickers_with_prices_trimmed_and_mcap_data")         


def get_tickers():

    with open("data/3.tickers_with_prices_trimmed.json") as f:
        data = json.load(f)

    return data


def get_bq_api_key():

    with open("api_keys/bq_api_key.txt", "r") as f:
        key = f.readline().strip()

    return key


def save_my_json(my_dict, f_name):

    with open(f"data/{f_name}.json", "w", encoding= "utf-8") as f:
        json.dump(my_dict, f, ensure_ascii=False, indent=4)


def main():

    BQ_API_KEY = get_bq_api_key()
    TICKERS = get_tickers()

    collect_mcap_data(TICKERS, BQ_API_KEY)

    

main()