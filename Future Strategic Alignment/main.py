# MAIN - MATRIX A
# This script executes the Matrix A analysis, generates a heatmap, and saves the results in the outputs folder
from pathlib import Path
import plotly.graph_objects as go
from matrix_a import run_matrix_a

BASE_DIR = Path(__file__).resolve().parent
SECTOR = "Financial Services"
INDUSTRIES = [
    'Consumer Lending',
    'Retail Brokerage',
    'Alternative Asset Managers',
    'Specialty Finance',
    'Regional Banks',
    'Crypto Exchanges',
    'Mortgage REITs',
]
OUTPUT_DIR = BASE_DIR / "outputs"
REFERENCE_ID = "HOOD"
HEATMAP_TOP_N = 25

OUTPUT_DIR.mkdir(exist_ok=True)  # create output directory

WHITE = "#FFFFFF"
HEATMAP_COLORS = [
    [0.00, "#1C180D"],
    [0.25, "#004022"],
    [0.50, "#0A5A0C"],
    [0.75, "#00C805"],
    [1.00, "#8FE690"],
]


# MATRIX A EXECUTION
# Discover firms, extract and save strategies, then calculate alignment.
results = run_matrix_a(
    sector=SECTOR,
    industries=INDUSTRIES,
    reference_id=REFERENCE_ID,
    output_dir=OUTPUT_DIR
)


# SAVE RESULTS TO CSV
results["ranking"].to_csv(OUTPUT_DIR / "ranking_A.csv")
results["semantic_matrix"].to_csv(OUTPUT_DIR / "alignment_matrix_semantic_A.csv")


# PREPARE HEATMAP
if results["ranking"].empty: # if no targets 
    raise SystemExit("No usable targets. See outputs/excluded_A.csv.")

heatmap_ranking = results["ranking"].head(HEATMAP_TOP_N) # select top N targets
heatmap_matrix = results["semantic_matrix"].loc[heatmap_ranking.index]

# adapt colorscale to results range
SEMANTIC_COLOR_MIN = heatmap_matrix.min().min()
SEMANTIC_COLOR_MAX = heatmap_matrix.max().max()

target_labels = heatmap_ranking["company_name"].tolist()

reference_rows = results["strategic_statements"]
reference_rows = reference_rows.loc[reference_rows["company_id"] == REFERENCE_ID] # filter, onhly HOOD statements
reference_statements = reference_rows["strategic_phrase"].tolist() # column to list

strategy_labels = reference_rows["strategy_label"].tolist()
hover_statements = [reference_statements] * len(heatmap_ranking) # HOOD statement for each target


# CREATE HEATMAP
fig = go.Figure()

fig.add_trace(
    go.Heatmap(
        z=heatmap_matrix.values,
        x=strategy_labels,
        y=target_labels,
        zmin=SEMANTIC_COLOR_MIN,
        zmax=SEMANTIC_COLOR_MAX,
        colorscale=HEATMAP_COLORS,
        colorbar=dict(
            title="Cosine",
            thickness=18,
            x=1.01,
            xanchor="left",
            tickformat=".2f",
            tickfont=dict(color="#FFFFFF"),
            title_font=dict(color="#FFFFFF"),
        ),
        texttemplate="%{z:.2f}",
        textfont_color="white",
        customdata=hover_statements,
        hovertemplate=(
            "<b>%{y}</b>"
            "<br>%{x}<br>"
            "Best-match cosine similarity: %{z:.3f}<br><br>"
            "<b>Full Robinhood strategic statement</b><br>%{customdata}"
            "<extra></extra>"
        ),
    )
)

fig.update_layout(
    title=(
        "Matrix A | " + results["reference_name"] + " Future Strategic Alignment"
        + "<br><sup>Symmetric best-match | Analysis date: " + results["analysis_date"] + "</sup>"
    ),
    title_font_color=WHITE,
    title_font_size=22,
    xaxis_title="Robinhood strategic statements",
    yaxis_title="Targets",
    font_color=WHITE,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    autosize=True,
    height=760,
    margin=dict(l=240, r=140, t=150, b=110),
)

fig.update_xaxes(automargin=True)
fig.update_yaxes(autorange="reversed", automargin=True)


# EXPORT HEATMAP
fig.write_image(OUTPUT_DIR / "heatmap.png", width=1600, height=900, scale=2)

fig.write_html(
    OUTPUT_DIR / "heatmap.html",
    include_plotlyjs=True,  
    config={"displaylogo": False, "responsive": True},
)

# TERMINAL OUTPUT
print(results["ranking"][[
    "company_name", "reference_coverage", "target_relevance", "A_raw", "A_score", "rank"
]])

print("\nA_raw = (reference_coverage + target_relevance) / 2")
print("A_score = 100 * A_raw")
