# MATRIX A - FUTURE STRATEGIC ALIGNMENT
# Business Quant supplies transcripts; OpenAI extracts strategies; Qwen embeds them.

from datetime import date
import json
from pathlib import Path # manage file and folder paths

import pandas as pd
import requests # send HTTP requests to Business Quant
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# API KEYS
import os
from pathlib import Path
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BUSINESSQUANT_API_KEY = os.getenv("BUSINESSQUANT_API_KEY")

# TEMPORARY DEBUG
print("OpenAI found:", bool(OPENAI_API_KEY))
print("Business Quant found:", bool(BUSINESSQUANT_API_KEY))
print("ENV path:", BASE_DIR / ".env")

# CONFIGURATION
BASE_DIR = Path(__file__).resolve().parent
EXTRACTION_MODEL = "gpt-6-luna"
SIMILARITY_MODEL = "Qwen/Qwen3-Embedding-0.6B"
REASONING_EFFORT = "medium" # low, medium, high
MAX_OUTPUT_TOKENS = 12000  
N_CALLS = 4  
UNIVERSE_URL = "https://data.businessquant.com/universe"
TRANSCRIPTS_URL = "https://data.businessquant.com/transcripts"
CACHE_DIR = BASE_DIR / "cache"
REFRESH_CACHE = False  # True downloads and extracts again, even if a saved result exists.


# EXTRACTION PROMPT AND RESPONSE FORMAT
EXTRACTION_PROMPT = (BASE_DIR / "prompt.txt").read_text(encoding="utf-8")
EVIDENCE_SCHEMA = {
    "type": "object", 
    "additionalProperties": False,
    "properties": {"speaker": {"type": "string"}, "quote": {"type": "string"}},
    "required": ["speaker", "quote"],
}
STRATEGY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "label": {"type": "string"},
        "strategy": {"type": "string"},
        "evidence": {"type": "array", "items": EVIDENCE_SCHEMA, "minItems": 1, "maxItems": 2,
        },
    },
    "required": ["label", "strategy", "evidence"],
}
OUTPUT_SCHEMA = {
    "type": "object", 
    "additionalProperties": False,
    "properties": {"initiatives": {"type": "array", "items": STRATEGY_SCHEMA}},
    "required": ["initiatives"],
}


# DISCOVER COMPANIES
def discover_companies(sector, industries, reference_id, session):

    params = {
        "api_key": BUSINESSQUANT_API_KEY,
        "security_type": "Equity"
    }

    response = session.get(UNIVERSE_URL, params=params)
    response.raise_for_status()
    data = response.json()["data"]

    rows = []

    for company in data:
        if company["ticker"] == reference_id or (
            company["sector"] == sector and company["industry"] in industries
        ):
            rows.append([
                company["ticker"],
                company["name"],
                company["industry"]
            ])

    companies = pd.DataFrame(
        rows, columns=["company_id", "company_name", "industry"]
    )

    # remove duplicate companies
    companies = companies.drop_duplicates(subset="company_name")

    return companies


# GET LATEST EARNINGS CALLS
def get_earnings_call(company, session):

    params = {
        "ticker": company["company_id"],
        "api_key": BUSINESSQUANT_API_KEY
    }

    response = session.get(TRANSCRIPTS_URL, params=params)
    response.raise_for_status()

    quarters = response.json()["metadata"]["available_fyq"][:N_CALLS] # get last N available quarters
    if not quarters:
        raise ValueError("No earnings calls available.")

    texts = []

    for quarter in quarters:
        params["fyq"] = quarter

        response = session.get(TRANSCRIPTS_URL, params=params) # get transcript of all quarters
        response.raise_for_status()
        if not response.json()["data"]:
            raise ValueError(f"No transcript available for {quarter}.")

        call = response.json()["data"][0]

        texts.append(
            f"FISCAL QUARTER: {quarter}\n"
            f"COMPANY PARTICIPANTS: {call['participants']}\n\n"
            f"TRANSCRIPT:\n{call['transcript']}"
        )

    return {
        "text": "\n\n".join(texts),
        "quarter": ", ".join(quarters)
    }



# STRATEGIC STATEMENT EXTRACTION
def extract_strategic_statements(transcript, client):
    text = transcript["text"]
    response = client.responses.create( # call the OpenAI Responses API
        model=EXTRACTION_MODEL,
        instructions=EXTRACTION_PROMPT,
        input=text,
        reasoning={"effort": REASONING_EFFORT},
        text={"format": {
            "type": "json_schema", "name": "strategic_initiatives",
            "schema": OUTPUT_SCHEMA, "strict": True,
        }},
        max_output_tokens=MAX_OUTPUT_TOKENS,
        store=False,
    )

    # check completion status 
    if response.status != "completed" or not response.output_text:
        raise ValueError("OpenAI output incomplete or refused.")
    
    output = response.output_text  # get the JSON response as a string
    data = json.loads(output)      # convert the JSON string into a Python dictionary
    initiatives = data["initiatives"]  # extract the list of strategic initiatives

    return initiatives


# CACHE - GET COMPANY STRATEGIES
def get_company_strategies(company, session, client):
    '''
    Retrieve the earnings call transcript and extract strategic statements for a given company.
    If the data is already cached, it will be read from the cache instead of making API calls.
    '''
    # read existing cache
    company_id = company["company_id"].replace("/", "_")
    path = CACHE_DIR / f"{company_id}_businessquant_{N_CALLS}calls.json"
    if path.exists() and not REFRESH_CACHE:
        with open(path, encoding="utf-8") as file:
            saved = json.load(file)

    # otherwise call the APIs
    else:
        transcript = get_earnings_call(company, session)
        initiatives = extract_strategic_statements(transcript, client)
        
        # save call information and initiatives to cache
        saved = {
            "call": {"quarter": transcript["quarter"]},
            "initiatives": initiatives
}

        with open(path, "w", encoding="utf-8") as file:
            json.dump(saved, file, ensure_ascii=False) 

    if not saved["initiatives"]:
        raise ValueError("No strategic initiatives found.")

    return saved["call"], saved["initiatives"]


# CALCULATE STRATEGIC ALIGNMENT
def calculate_alignment(companies, strategies, reference_id):

    reference_statements = strategies[reference_id] # HOOD
    company_info = companies.set_index("company_id") # second company

    ranking_rows = [] # final companies scores
    semantic_rows = [] # per strategy scores

    if len(strategies) > 1:
        model = SentenceTransformer(SIMILARITY_MODEL)
        reference_vectors = model.encode(reference_statements, normalize_embeddings=True, prompt="") # embedding vectors for HOOD statements

        for company_id, target_statements in strategies.items():
            if company_id == reference_id:
                continue # skip HOOD

            target_vectors = model.encode(target_statements, normalize_embeddings=True, prompt="") # embedding
            similarities = cosine_similarity(reference_vectors, target_vectors) # cosine similarity matrix

            # Best matches in both directions
            reference_best = similarities.max(axis=1) # by row
            target_best = similarities.max(axis=0) # ny column

            reference_coverage = float(reference_best.mean()) 
            target_relevance = float(target_best.mean()) 

            a_raw = (reference_coverage + target_relevance) / 2
            a_score = 100 * a_raw

            ranking_rows.append([
                company_id,
                company_info.loc[company_id, "company_name"],
                company_info.loc[company_id, "industry"],
                reference_coverage,
                target_relevance,
                a_raw,
                a_score
            ])

            semantic_rows.append([company_id] + list(reference_best)) # for the heatmap

    # Create ranking
    ranking = pd.DataFrame(ranking_rows, 
        columns=[
            "company_id", "company_name", "industry",
            "reference_coverage", "target_relevance",
            "A_raw", "A_score"
        ]).set_index("company_id")

    # Add rank column and sort
    ranking["rank"] = ranking["A_raw"].rank(ascending=False, method="average") # new column with rank based on A_raw
    ranking = ranking.sort_values(["rank", "company_name"]) # sort by rank and then by company name

    labels = reference_statements # create semantic matrix labels

    # create semantic matrix
    semantic_matrix = pd.DataFrame(
        semantic_rows, columns=["company_id"] + labels
    ).set_index("company_id")

    semantic_matrix = semantic_matrix.loc[ranking.index]

    return ranking, semantic_matrix



# MATRIX A EXECUTION
def run_matrix_a(sector, industries, reference_id="HOOD",
                 output_dir=BASE_DIR / "outputs"):

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    strategies = {} # companies strategies
    statement_rows = [] # detailed info
    excluded_rows = []

    # connect to Business Quant and OpenAI
    with requests.Session() as session, OpenAI(api_key=OPENAI_API_KEY) as client:

        companies = discover_companies(sector, industries, reference_id, session)
        print("Companies discovered:", len(companies))
        print(companies)

        # Extract strategies for each company
        for _, company in companies.iterrows():
            company_id = company["company_id"]
            company_name = company["company_name"]

            print("Extracting:", company_name)

            try:
                call, initiatives = get_company_strategies(company, session, client)
                # call contains the earnings call metadata, initiatives contains the extracted strategies

            except (ValueError, KeyError, requests.RequestException) as error:
                
                # if HOOD is excluded 
                if company_id == reference_id:
                    raise ValueError(f"Reference company: {error}") from error

                # else, append to excluded list and continue
                excluded_rows.append([company_id, company_name, str(error)])
                print("Excluded:", company_name)
                continue

            # prepare dict of strategies for alignment calculation
            company_strategies = []
            for item in initiatives:
                company_strategies.append(item["strategy"])
            strategies[company_id] = company_strategies

            # prepare detailed dict for CSV output
            for initiative in initiatives:
                statement_rows.append([
                    company_id,
                    company_name,
                    company["industry"],
                    "earnings_call",
                    initiative["strategy"],
                    initiative["label"],
                    TRANSCRIPTS_URL,
                    call["quarter"],
                    json.dumps(initiative["evidence"], ensure_ascii=False),
                    EXTRACTION_MODEL,
                    SIMILARITY_MODEL
                ])

    # save extracted strategies dataframe
    extracted = pd.DataFrame(statement_rows, columns=[
    "company_id", "company_name", "industry",
    "field", "strategic_phrase", "strategy_label",
    "source", "source_quarter", "evidence",
    "extraction_model", "similarity_model"
    ])

    # save excluded companies dataframe
    excluded = pd.DataFrame(
        excluded_rows, columns=["company_id", "company_name", "reason"]
    )

    # save to CSV
    extracted.to_csv(output_dir / "strategic_statements_A.csv", index=False)
    excluded.to_csv(output_dir / "excluded_A.csv", index=False)

    # calculate alignment
    ranking, semantic_matrix = calculate_alignment(companies, strategies, reference_id)

    company_info = companies.set_index("company_id")
    reference_name = company_info.loc[reference_id, "company_name"]

    return {
        "ranking": ranking,
        "semantic_matrix": semantic_matrix,
        "strategic_statements": extracted,
        "excluded": excluded,
        "reference_name": reference_name,
        "analysis_date": date.today().isoformat()
    }

