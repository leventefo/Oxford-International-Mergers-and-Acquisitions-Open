import requests
import json
import ast
from collections import defaultdict



def get_metadata(func, api_key, **args):
    
    params = {'api_key': "1c1745445c55481d03fe377d8df790e8"}
    response = requests.get('https://data.businessquant.com/universe', params=params)
    my_response = json.loads(response.content.decode("utf-8"))
    data = my_response["data"]

    return func(data, args)


def get_industry_and_sector(data):

    industries_sector = {}

    for my_dict in data:

        if my_dict["industry"] not in industries_sector.keys():
            industries_sector[my_dict["industry"]] = my_dict["sector"]

    return industries_sector


def get_all_sectors(data, args):

    industries_sector = get_industry_and_sector(data)

    return sorted(list(filter(lambda x: x is not None, set(industries_sector.values()))))


def get_all_industries(data, args):

    industries_sector = get_industry_and_sector(data)

    return sorted(list(filter(lambda x: x is not None, set(industries_sector.keys()))))


def get_industry_by_sector(data, args):

    if set(args.keys()) != set({"sector"}):
        return "Please only pass the 'sector' key."

    else:
        industries_sector = get_industry_and_sector(data)
        response = [my_dict[0] for my_dict in industries_sector.items() if my_dict[1] == list(args.values())[0]]
        return response if not not response else f"{list(args.values())[0]} sector does not exist."


def get_tickers_by_sector_and_industry(data, args):

    if set(args.keys()) != set({"sector", "industry"}):
        return "Please pass 'sector' and 'industry' keys."

    else:

        my_dict = {args["sector"]: {args["industry"]: []}}

        for my_little_dict in data:
            if set({my_little_dict["sector"], my_little_dict["industry"]}) == set(args.values()) and my_little_dict["security_type"] == "Equity":
                my_dict[my_little_dict["sector"]][my_little_dict["industry"]].append(dict(ticker = my_little_dict["ticker"], cik = my_little_dict["cik"], name = my_little_dict["name"]))


        return my_dict
        



def main():

    API_KEY = "1c1745445c55481d03fe377d8df790e8"
    #print(get_metadata(get_all_sectors, API_KEY))
    #print(get_metadata(get_all_industries, API_KEY))
    print(get_metadata(get_industry_by_sector, API_KEY, sector = "Financial Services"))
    #print(get_metadata(get_tickers_by_sector_and_industry, API_KEY, sector = "Financial Services", industry = "Regional Banks"))

main()
    


    