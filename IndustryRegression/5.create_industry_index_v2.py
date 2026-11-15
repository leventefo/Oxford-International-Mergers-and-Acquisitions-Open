import json
import pandas as pd
import sys
import numpy as np
from math import nan


def get_tickers(fname):

    with open(f"data/{fname}") as f:
        data = json.load(f)

    return data


def find_largest_common_denominator(tickers):

    largest_common_denominator = []

    for industry in tickers:
        for ticker in tickers[industry]:
            if len(tickers[industry][ticker]["price_time"]) > len(largest_common_denominator):
                largest_common_denominator = tickers[industry][ticker]["price_time"]


    save_my_json(largest_common_denominator, "trading_days")



def save_my_json(my_dict, f_name):

    with open(f"data/{f_name}.json", "w", encoding= "utf-8") as f:
        json.dump(my_dict, f, ensure_ascii=False, indent=4)



def get_trading_days():

    with open(f"data/trading_days.json") as f:
        dates = json.load(f)

    return dates


def drop_accumulated_returns(tickers, trading_days):

    for industry in tickers:

        for ticker in tickers[industry]:

            dates_to_remove = []

            for date in tickers[industry][ticker]["price_time"][:-1]:

                trading_day_index = trading_days.index(date)
                my_trading_day_index = tickers[industry][ticker]["price_time"].index(date)

                if tickers[industry][ticker]["price_time"][my_trading_day_index + 1] != trading_days[trading_day_index + 1]:

                    if tickers[industry][ticker]["price_time"][my_trading_day_index + 1] in tickers[industry][ticker]["industry_weighted_return_time"]:
                    
                        dates_to_remove.append(tickers[industry][ticker]["price_time"][my_trading_day_index + 1])


            date_indexes_to_remove = []

            for date in dates_to_remove:
                date_indexes_to_remove.append(tickers[industry][ticker]["industry_weighted_return_time"].index(date))


            tickers[industry][ticker]["industry_weighted_return_time"] = list(np.delete(np.array(tickers[industry][ticker]["industry_weighted_return_time"]), tuple(date_indexes_to_remove)))
            tickers[industry][ticker]["industry_weighted_return_value"] = list(np.delete(np.array(tickers[industry][ticker]["industry_weighted_return_value"]), tuple(date_indexes_to_remove)))



    save_my_json(tickers, "7.tickers_with_industry_weighted_returns_accumulated_returns_removed")       




def create_dataframe(tickers, trading_days):

    df = pd.DataFrame(index=trading_days, columns = [industry for industry in tickers])

    for industry in tickers:

        for date in trading_days:

            returns = []

            for ticker in tickers[industry]:

                try:

                    returns.append(tickers[industry][ticker]["industry_weighted_return_value"][tickers[industry][ticker]["industry_weighted_return_time"].index(date)])

                except ValueError:

                    pass

            if len(returns) == 0:
                df.at[date, industry] = nan
            else:
                df.at[date, industry] = sum(returns)

    df.index.name = "Date"

    return df



def save_df(df, fname):

    df.to_csv(f"data/{fname}.csv")
    df.to_parquet(f"data/{fname}.parquet")


def main():

    tickers = get_tickers("7.tickers_with_industry_weighted_returns_edited.json")
    #find_largest_common_denominator(tickers)
    TRADING_DATES = get_trading_days()
    #drop_accumulated_returns(tickers, TRADING_DATES)

    df = create_dataframe(tickers, TRADING_DATES)
    save_df(df, "8.index")


main()