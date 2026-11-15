import requests
import json
import threading
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
import traceback
import time
from collections import Counter
import os
import glob
from dateutil import parser


def collect_price_data(tickers, id, secret):
    
    BASE_URL = "https://data.alpaca.markets/v2/stocks/bars"
    HEADERS = {
        "accept": "application/json",
        "APCA-API-KEY-ID": f"{id}",
        "APCA-API-SECRET-KEY": f"{secret}"
    }


    three_yrs_ago = datetime.now() - relativedelta(years=3)
    three_yrs_ago = three_yrs_ago.strftime("%Y-%m-%d")


    def recursive_link_follow(response):

        try:

            if response[-1]["next_page_token"] == None:
                return response
            else:
                PARAMS["page_token"] = response[-1]["next_page_token"]
                return response + recursive_link_follow([requests.get(BASE_URL, params = PARAMS, headers = HEADERS).json()])

        except:

            PARAMS["symbols"] = PARAMS["symbols"].split(",")
            PARAMS["symbols"].remove(response[0]["message"].split(":")[1][1:])
            PARAMS["symbols"] = ",".join(PARAMS["symbols"])

            return recursive_link_follow([requests.get(BASE_URL, params = PARAMS, headers = HEADERS).json()])


    def connect_pages(tickers, industry, industry_prices):

        for page in industry_prices:
            for ticker in page["bars"]:
                tickers[industry][ticker]["price"].extend(page["bars"][ticker])


    def trim_tickers(tickers):
        for industry in tickers:
            for ticker in tickers[industry]:
                for i in range(len(tickers[industry][ticker]["price"])):
                    tickers[industry][ticker]["price_time"].append(parser.isoparse(tickers[industry][ticker]["price"][i]["t"]).strftime("%Y-%m-%d"))
                    tickers[industry][ticker]["price"][i] = tickers[industry][ticker]["price"][i]["c"]

    

    for industry in tickers:

        my_tickers = ",".join([ticker for ticker in tickers[industry]])

        PARAMS = {
            "symbols" : f"{my_tickers}",
            "timeframe" : "1D",
            "start" : f"{three_yrs_ago}",
            "limit" : 10000,
            "adjustment" : "all",
        }

        if "_".join(industry.split(" ")) + ".json" not in os.listdir("data/prices"):

            industry_prices = recursive_link_follow([requests.get(BASE_URL, params = PARAMS, headers = HEADERS).json()])

            with open(f"data/prices/{"_".join(industry.split(" "))}.json", "w") as f:
                json.dump(industry_prices, f, ensure_ascii=False, indent=4)
        else:

            with open(f"data/prices/{"_".join(industry.split(" "))}.json") as f:
                industry_prices = json.load(f)

        
        connect_pages(tickers, industry, industry_prices)

    #save_my_json(tickers, "2.tickers_with_prices")

    trim_tickers(tickers)

    #save_my_json(tickers, "3.tickers_with_prices_trimmed")

    return tickers


 
def save_my_json(my_dict, f_name):

    with open(f"data/{f_name}.json", "w", encoding= "utf-8") as f:
        json.dump(my_dict, f, ensure_ascii=False, indent=4)

        

def get_tickers():

    with open("data/1.tickers.json") as f:
        data = json.load(f)

    return data


def get_alpaca_id():

    with open("api_keys/al_api_key.json") as f:
        id = json.load(f)

    return id



def main():

    ALPACA_ID, ALPACA_SECRET = get_alpaca_id()["key"], get_alpaca_id()["secret"]
    TICKERS = get_tickers()

    collect_price_data(TICKERS, ALPACA_ID, ALPACA_SECRET)
    

main()

