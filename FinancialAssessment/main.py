# MAIN - MATRIX C
from pathlib import Path
import requests
import plotly.graph_objects as go
from matrix_c import discover_companies, run_matrix_c

CAPITOX_NAVY = "#002147"
ROBINHOOD_COLORS = [
    "#CCFF00",
    "#00C805",
    "#008C60",
    "#66FF66",
    "#FFFFFF",
    "#C8CDD2",
    "#8E99A4",
]
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

SECTOR = "Financial Services"


INDUSTRIES = [
    'Consumer Lending',
    'Mortgage REITs',
    'Retail Brokerage', 
    'Alternative Asset Managers', 
    'Specialty Finance', 
    'Regional Banks', 
    'Crypto Exchanges', 
]

REFERENCE_ID = "HOOD"
N_YEARS = 4
N_QUARTERS = 4 * N_YEARS
MIN_TOTAL_COVERAGE = 0.70
MIN_MACRO_COVERAGE = 0.40
MIN_OBSERVATIONS = 6
GROWTH_CATEGORY = "Growth"
SCATTER_TOP_N = 20

OUTPUT_DIR.mkdir(exist_ok=True)

# discover companies
with requests.Session() as session:
    companies = discover_companies(SECTOR, INDUSTRIES, session)
    # terminal check
    print(f"Companies discovered: {len(companies)}")
    print(companies["industry"].value_counts())

# run Matrix C analysis
results = run_matrix_c(
    companies,
    REFERENCE_ID,
    N_QUARTERS,
    MIN_TOTAL_COVERAGE,
    MIN_MACRO_COVERAGE,
    MIN_OBSERVATIONS
)

# terminal check
print(f"\nCompanies in final ranking: {len(results['ranking'])}")
print(results["ranking"]["industry"].value_counts())

# save results to CSV
for name, table in results.items():
    save_index = name in ("ranking", "category_scores", "coverage")
    table.to_csv(OUTPUT_DIR / f"{name}_C.csv", index=save_index)

# prepare scatter plot
ranking = results["ranking"].groupby("industry").head(SCATTER_TOP_N).copy()
ranking["growth_score"] = results["category_scores"][GROWTH_CATEGORY]

if ranking.empty:
    raise ValueError("No targets available for the scatter plot.")

# SCATTER PLOT
fig = go.Figure()
size_reference = 2 / 60 ** 2

for industry in ranking["industry"].unique():
    group = ranking.loc[ranking["industry"] == industry]

    fig.add_scatter(
        x=group["financial_score"],
        y=group["growth_score"],
        mode="markers",
        name=industry,
        text=group["name"],
        marker_size=group["sustainability_score"].fillna(0.20),
        marker_symbol=group["sustainability_score"].isna().map(
            {True: "square", False: "circle"}
        ),
        marker_sizemode="area",
        marker_sizeref=size_reference,
        marker_sizemin=5,
        marker_opacity=0.75,
        customdata=group[["industry", "sustainability_score"]].astype(object).fillna("N/A"),
        hovertemplate=(
            "<b>%{text}</b>"
            "<br>Industry: %{customdata[0]}"
            "<br>Financial Score: %{x:.3f}"
            "<br>Growth Score: %{y:.3f}"
            "<br>Financial Sustainability: %{customdata[1]:.3f}"
            "<extra></extra>"
        ),
    )


fig.update_layout(
    template="plotly_white",
    colorway=ROBINHOOD_COLORS,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",

    font=dict(
        family="Arial",
        size=19,
        color="white"
    ),
    title=dict(
        text=(
            "Matrix C | Financial Screening"
            "<br><sup>Bubble size = Financial Sustainability | Square = N/A</sup>"
        ),
        font=dict(family="Arial", size=27, color="white"),
        x=0.02
    ),
    xaxis=dict(
        title=dict(text="Financial Score", 
        font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(255,255,255,0.25)",        
        zeroline=False
    ),
    yaxis=dict(
        title=dict(text="Growth Score", font=dict(size=22)),
        tickfont=dict(size=18),
        gridcolor="rgba(255,255,255,0.25)",
        zeroline=False
    ),
    width=1100,
    height=700,
    legend=dict(
        title=dict(text="Industry", font=dict(size=20)),
        font=dict(size=18),
        y=0.5,
        yanchor="middle",
        itemsizing="constant",
        bgcolor="rgba(0,0,0,0)"
    )
)

fig.write_image(
    OUTPUT_DIR / "scatter_C.png",
    scale=3
)
fig.write_html(OUTPUT_DIR / "scatter_C.html")
fig.show()
