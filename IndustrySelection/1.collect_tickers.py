import requests
import json


def get_metadata(func, api_key, **args):

    BASE_URL = 'https://data.businessquant.com/universe'
    PARAMS = {'api_key': api_key}
    response = requests.get(BASE_URL, params=PARAMS)
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

        if not isinstance(args["industry"], list):
            args["industry"] = [args["industry"]]

        #my_dict = {industry: [] for industry in args["industry"]}
        my_dict = {industry: {} for industry in args["industry"]}
        save_my_json(my_dict, "blueprint")

        for my_little_dict in data:
            if my_little_dict["sector"] == args["sector"] and my_little_dict["industry"] in args["industry"] and my_little_dict["security_type"] == "Equity" and my_little_dict["cik"] not in [1783879, 2131040]:
                #my_dict[my_little_dict["industry"]].append(dict(ticker = my_little_dict["ticker"], cik = my_little_dict["cik"], name = my_little_dict["name"], exchange = my_little_dict["exchange"]))
                my_dict[my_little_dict["industry"]][my_little_dict["ticker"]] = {"price" : [], "mcap" : [], "price_time": [], "mcap_time": [], "metadata": dict(cik = my_little_dict["cik"], name = my_little_dict["name"], exchange = my_little_dict["exchange"])}


        return my_dict


def get_bq_api_key():

    with open("api_keys/bq_api_key.txt", "r") as f:
        key = f.readline().strip()

    return key


def save_my_json(my_dict, f_name):

    with open(f"data/{f_name}.json", "w", encoding= "utf-8") as f:
        json.dump(my_dict, f, ensure_ascii=False, indent=4)


def main():

    BQ_API_KEY = get_bq_api_key()
    my_data = get_metadata(get_tickers_by_sector_and_industry, BQ_API_KEY, sector = "Financial Services", industry = get_metadata(get_industry_by_sector, BQ_API_KEY, sector = "Financial Services"))
    save_my_json(my_data, "1.tickers")

main()
    


    