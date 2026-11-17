import json
from datetime import datetime, timedelta


def get_tickers(fname):

    with open(f"data/{fname}") as f:
        data = json.load(f)

    return data



def calculate_pct_changes(tickers):

    for industry in tickers:
        for ticker in tickers[industry]:

            my_price_list = tickers[industry][ticker]["price"]
            my_mcap_list = tickers[industry][ticker]["mcap"]

            if my_price_list and  my_mcap_list:
                tickers[industry][ticker]["price_change"] = [((my_price_list[i+1]-my_price_list[i])/my_price_list[i])*100 for i in range(len(my_price_list)-1)]
                tickers[industry][ticker]["mcap_change"] = [((my_mcap_list[i+1]-my_mcap_list[i])/my_mcap_list[i])*100 for i in range(len(my_mcap_list)-1)]


    save_my_json(tickers, "5.tickers_with_pct_changes")


def get_industry_market_cap_at_time(tickers, industry, start_time, end_time):

    mcap = []
    
    for ticker in tickers[industry]:
        try:
            if tickers[industry][ticker]["price"][tickers[industry][ticker]["price_time"].index(start_time)]:
                if tickers[industry][ticker]["price"][tickers[industry][ticker]["price_time"].index(end_time)]:
                    if tickers[industry][ticker]["mcap"][tickers[industry][ticker]["mcap_time"].index(start_time)]:
                        mcap.append(tickers[industry][ticker]["mcap"][tickers[industry][ticker]["mcap_time"].index(start_time)])
        except (ValueError, IndexError):
            pass

    return sum(mcap)




def calculate_index(tickers):

    for industry in tickers:
        for ticker in tickers[industry]:
            tickers[industry][ticker]["industry_weighted_return_value"] = []
            tickers[industry][ticker]["industry_weighted_return_time"] = []
    
    for industry in tickers:

        print(industry)

        for ticker in tickers[industry]:

            print(ticker)

            for i in range(len(tickers[industry][ticker]["price"])-1):
                if tickers[industry][ticker]["price"]:
                    if tickers[industry][ticker]["price_time"][i] in tickers[industry][ticker]["mcap_time"]:
                        mcap_index = tickers[industry][ticker]["mcap_time"].index(tickers[industry][ticker]["price_time"][i])
                        total_mcap = get_industry_market_cap_at_time(tickers, industry, tickers[industry][ticker]["price_time"][i], tickers[industry][ticker]["price_time"][i+1])
                        tickers[industry][ticker]["industry_weighted_return_value"].append(tickers[industry][ticker]["price_change"][i]*(tickers[industry][ticker]["mcap"][mcap_index])/total_mcap)
                        tickers[industry][ticker]["industry_weighted_return_time"].append(tickers[industry][ticker]["price_time"][i+1])


    save_my_json(tickers, "6.tickers_with_industry_weighted_returns")






def save_my_json(my_dict, f_name):

    with open(f"data/{f_name}.json", "w", encoding= "utf-8") as f:
        json.dump(my_dict, f, ensure_ascii=False, indent=4)



def main():

    #tickers = calculate_pct_changes(get_tickers("4.tickers_with_prices_trimmed_and_mcap_data_edited.json"))
    tickers = calculate_index(get_tickers("5.tickers_with_pct_changes.json"))

    #tickers = get_tickers("5.tickers_with_pct_changes.json")
    #print(get_industry_market_cap(tickers, "Alternative Asset Managers", "2026-08-13"))

main()

