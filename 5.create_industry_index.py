import json
import pandas as pd
import sys


def get_tickers(fname):

    with open(f"data/{fname}") as f:
        data = json.load(f)

    return data


def find_largest_common_denominator(tickers, industry):

    largest_common_denominator = []

    for ticker in tickers[industry]:
        if len(tickers[industry][ticker]["industry_weighted_return_time"]) > len(largest_common_denominator):
            largest_common_denominator = tickers[industry][ticker]["industry_weighted_return_time"]


    return largest_common_denominator


# def create_dataframe(tickers):

#     index = []

#     for industry in tickers:
#         for ticker in tickers[industry]:
#             index.append([industry, ticker])

#     df = pd.DataFrame(index)
#     df = pd.DataFrame(index = pd.MultiIndex.from_frame(df), columns = ["Date", "Return"])


#     for industry in tickers:
#         for ticker in tickers[industry]:
#             df.at[(industry, ticker), "Date"] = pd.Series(find_largest_common_denominator(tickers, industry))
#             df.at[(industry, ticker), "Return"] = pd.Series(tickers[industry][ticker]["industry_weighted_return_value"])


#     print(df.loc["Alternative Asset Managers", "AAC"])

def main():

    tickers = get_tickers("6.tickers_with_industry_weighted_returns.json")
    create_dataframe(tickers)
    #print(find_largest_common_denominator(tickers, "Alternative Asset Managers"))


main()