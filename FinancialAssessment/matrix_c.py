# MATRIX C - ONE CATEGORY AT A TIME
from pathlib import Path
import os

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from scipy.stats import norm

from config_c import CATEGORIES, FINANCIAL_SUSTAINABILITY

load_dotenv(Path(__file__).resolve().parent / '.env')
API_KEY = os.getenv('BUSINESSQUANT_API_KEY')
BASE_URL = 'https://data.businessquant.com'


# DISCOVER COMPANIES
def discover_companies(sector, industries, session):
    # API call
    params = {'api_key': API_KEY, 'security_type': 'Equity'}
    response = session.get(BASE_URL + '/universe', params=params)
    response.raise_for_status()
    # companies dataframe
    companies = pd.DataFrame(response.json()['data'])
    selected = (companies['sector'] == sector) & companies['industry'].isin(industries)
    companies = companies.loc[selected, ['ticker', 'name', 'industry']]
    companies = companies.drop_duplicates(subset='name')
    return companies.set_index('ticker')


# GET DATA FOR ONE COMPANY
# Metrics are already selected for the current category.
def get_financial_data(ticker, metrics, session, names):
    rows = []
    # API CALL
    # recall the API accepts max 5 metrics per request
    for j in range(0, len(metrics), 5):
        params = {
            'api_key': API_KEY,
            'ticker': ticker,
            'slug': ','.join(metrics[j:j + 5]),
            'period': 'max',
            'mode': 'original'
        }
        response = session.get(BASE_URL + '/historic', params=params, timeout=60)
        if response.status_code == 404:
            print(f"HTTP 404: {ticker} - {params['slug']}")
            continue # ignore error 404
        response.raise_for_status() # raise other errors

        for record in response.json()['data']:
            rows.append([
                ticker, names[record['metric']], record['date'], record['value']
            ])

    # Prepare quarterly data
    data = pd.DataFrame(rows, columns=['ticker', 'metric', 'date', 'value'])
    if not data.empty:
        data['date'] = pd.to_datetime(data['date']) # convert
        data['quarter'] = data['date'].dt.to_period('Q')
        data['value'] = pd.to_numeric(data['value'], errors='coerce')
        data = data.sort_values('date')

    return data

# GET REFERENCE DATA
def get_reference_data(reference, categories, quarters, session, names):
    metrics = []

    for category in categories.values():
        for settings in category['ratios'].values():
            if settings['formula'] == 'relative_to_reference':
                metrics.extend(settings['metrics'])

    metrics = list(dict.fromkeys(metrics))

    if not metrics:
        return {}

    data = get_financial_data(reference, metrics, session, names)

    if data.empty:
        return {}

    return data.pivot_table(
        index='quarter',
        columns='metric',
        values='value',
        aggfunc='last'
    ).reindex(index=quarters).to_dict('series')


# CALCULATE RATIOS FOR ONE COMPANY
def calculate_ratios(data, ticker, ratios, quarters, n_quarters, reference_data, min_observations):
    rows = data[data['ticker'] == ticker] # extract metrics for the company
    table = rows.pivot_table( # change structure 
        index='quarter', 
        columns='metric', 
        values='value', 
        aggfunc='last'
        ).reindex(index=quarters)

    # calculate ratios
    result = {}
    observations = {}
    for name, settings in ratios.items(): # for each ratio

        formula = settings['formula']
        metrics = settings['metrics']


        if any(metric not in table.columns for metric in metrics):
            observations[name] = 0
            continue

        if formula == 'direct':
            values = table[metrics[0]]

        elif formula == 'divide':
            denominator = table[metrics[1]]
            values = table[metrics[0]] / denominator.where(denominator > 0)

        elif formula == 'yoy':
            values = table[metrics[0]]
            previous = values.shift(4)
            values = 100 * (values / previous.where(previous > 0) - 1)

        elif formula == 'relative_to_reference':
            if metrics[0] not in reference_data:
                observations[name] = 0
                continue
            denominator = reference_data[metrics[0]]
            numerator = table[metrics[0]]
            values = numerator.where(numerator > 0) / denominator.where(denominator > 0)

        values = values.iloc[-n_quarters:]
        values = values.replace([np.inf, -np.inf], np.nan)

        observations[name] = int(values.count())

        if formula == 'relative_to_reference':
            if pd.notna(values.iloc[-1]):
                result[name] = float(values.iloc[-1])

        elif observations[name] >= min_observations:
            result[name] = float(values.mean())

    return result, observations


# NORMALIZE RATIOS 0-1
def ratio_score(values, direction):
    # drop missing values
    values = values.dropna()

    center = values.median() # median
    mad = (values - center).abs().median()
    scale = 1.4826 * mad # Formula: 1.4826 * median(|x - median(x)|)
        # the factor 1.4826 makes MAD comparable to the standard deviation under normal distribution

    # if MAD=0, use mean and standard deviation
    if scale == 0:
        center = values.mean()
        scale = values.std(ddof=0)

    z = pd.Series(0.0, index=values.index) # initializa a series of zeros
    if scale > 0:
        z = (values - center) / scale # Z-SCORE --> (x - center) / scale
    if direction == -1:
        z = -z

    scores = norm.cdf(z) # 0-1 values through normal cumulative distribution
    scores = pd.Series(scores, index=values.index) # array to pandas series

    return scores



# RUN MATRIX C
def run_matrix_c(companies, reference, n_quarters, min_total_coverage, min_macro_coverage, min_observations):

    companies = companies.drop(index=reference, errors='ignore')

    # Define analysis period
    end = pd.Timestamp.today().to_period('Q') - 1
    quarters = pd.period_range(end=end, periods=n_quarters + 4, freq='Q')

    # terminal check
    print(f"\nAnalyzing {len(companies)} companies")
    print(f"Period: {quarters[-n_quarters]} to {quarters[-1]}")
    
    category_scores = pd.DataFrame(index=companies.index) # creates df with companies as index
    coverage = pd.DataFrame(index=companies.index)
    missing = [] # initialize list to record missing data
    metric_rows = [] # available observations
    ratio_rows = []

    # create shallow copy to add financial sustainability
    categories = CATEGORIES.copy()
    categories['Financial Sustainability'] = {'ratios': FINANCIAL_SUSTAINABILITY}

    with requests.Session() as session: # request library object

        params = {'api_key': API_KEY, 'table': 'historic'}
        response = session.get(BASE_URL + '/metadata', params=params, timeout=60)
        response.raise_for_status()

        names = {}
        for metric in response.json():
            names[metric['metric_full']] = metric['slug']

        # get parent company's metric to compute relative ratios
        reference_data = get_reference_data(reference, categories, quarters, session, names)
        for category_name, category in categories.items():  # for each macroarea and macroarea dict
            # terminal check
            print(f"\nProcessing: {category_name}")
            
            ratios = category['ratios'] # ratios internal dict

            # select required metrics
            metrics = []
            for ratio in ratios.values(): # for each ratio
                metrics.extend(ratio['metrics']) # add necessary metrics

            metrics = list(set(metrics)) # drop duplicates

            values = pd.DataFrame(index=companies.index, columns=ratios, dtype=float) # create pandas df

            # download and calculate one company at a time
            tickers = list(companies.index) # tickers of all companies
            for ticker in tickers: # for each company
                # terminal check
                print(f"  Downloading: {ticker}")
                
                data = get_financial_data(ticker, metrics, session, names)

                # Count available quarters for each metric
                if data.empty:
                    metric_counts = pd.Series(dtype=int)
                else:
                    valid = data.loc[data['quarter'].isin(quarters) & data['value'].notna()]
                    metric_counts = valid.groupby('metric')['quarter'].nunique()

                for metric in metrics:
                    count = int(metric_counts.get(metric, 0))
                    metric_rows.append([ticker, category_name, metric, count])

                    if count == 0:
                        missing.append([ticker, category_name, metric])

                if data.empty:
                    for name in ratios:
                        ratio_rows.append([ticker, category_name, name, 0])
                    continue

                # Calculate ratios and count valid observations
                result, counts = calculate_ratios(
                    data, ticker, ratios, quarters, n_quarters,
                    reference_data, min_observations
                )

                for name in ratios:
                    ratio_rows.append([ticker, category_name, name, counts[name]])

                for name, value in result.items():
                    values.loc[ticker, name] = value

            # normalize ratios
            scores = pd.DataFrame(index=companies.index, columns=ratios, dtype=float) # initialize pandas df
            # create groups of companies
            if category_name == 'Financial Sustainability':
                groups = [companies.index] # list with all companies
            else:
                groups = []
                for industry in companies['industry'].unique():
                    tickers = companies[companies['industry'] == industry].index # list with industry companies
                    groups.append(tickers) 

            for peers in groups: # for each peers group
                for ratio, settings in ratios.items(): # for each ratio and setting
                    # record in scores the normalized score
                    peers_values = values.loc[peers, ratio] # get the initial values
                    scores.loc[peers, ratio] = ratio_score(peers_values, settings['direction']) # record the scores

            # calculate weighted category score
            # get weights
            weights = {}
            for ratio, settings in ratios.items():
                weights[ratio] = settings['weight']
            weights = pd.Series(weights)

            coverage[category_name] = (scores.notna() * weights).sum(axis=1) # get coverage percentage for each company
            # calculate weighted average of available ratio scores, adjusting for missing data
            category_scores[category_name] = (
                (scores * weights).sum(axis=1) /
                coverage[category_name].replace(0, np.nan) # divide by the coverage (handle zero division)
            )

    # FINAL SCORES
    # get macroareas weights
    weights = {}
    for category, settings in CATEGORIES.items(): 
        weights[category] = settings['weight']
    weights = pd.Series(weights)

    # compute financial score
    ranking = companies.copy() # create ranking df
    valid_macro = coverage[weights.index] >= min_macro_coverage # identify valid macroareas
    valid_weights = valid_macro * weights # redistribute macroareas weights

    ranking['financial_score'] = (
        (category_scores[weights.index].where(valid_macro) * weights).sum(axis=1)
        / valid_weights.sum(axis=1).replace(0, np.nan)
    )
    
    # compute sustainability score
    eligible_s = coverage['Financial Sustainability'] >= min_macro_coverage # eligible for sustainability
    ranking['sustainability_score'] = category_scores['Financial Sustainability'][eligible_s] # record if eligible

    # select eligible companies
    total_coverage = coverage[weights.index].mul(weights).sum(axis=1)
    eligible = (
        (total_coverage >= min_total_coverage)
        & (valid_macro.sum(axis=1) >= 4)
    )
    ranking = ranking[eligible] # mantain only if eligible_f

    # Sort ranking
    ranking = ranking.sort_values('financial_score', ascending=False)
    
    missing = pd.DataFrame(missing, columns=['ticker', 'category', 'metric'])

    metric_observations = pd.DataFrame(
        metric_rows,
        columns=['ticker', 'category', 'metric', 'raw_quarters']
    )

    ratio_observations = pd.DataFrame(
        ratio_rows,
        columns=['ticker', 'category', 'ratio', 'valid_quarters']
    )

    return {
        'ranking': ranking,
        'category_scores': category_scores,
        'coverage': coverage,
        'missing_metrics': missing,
        'metric_observations': metric_observations,
        'ratio_observations': ratio_observations
    }
