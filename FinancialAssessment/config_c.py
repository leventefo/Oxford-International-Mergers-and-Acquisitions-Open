# CONFIGURATION - MATRIX C

# HOW TO ADD RATIOS
# "ratio_name": {
#     "metrics": ["metric_1", "metric_2"], # Business Quant API slugs
#     "formula": "divide",                 # Calculation method
#     "weight": 0.20,                      # Weight within category
#     "direction": 1                       # 1 = higher is better; -1 = lower
# }
# FORMULAS:
# direct                -> use metric_1
# divide                -> metric_1 / metric_2
# yoy                   -> annual growth of metric_1 (%)
# relative_to_reference -> metric_1 / same metric for HOOD
#
# RULES:
# Use exact API slugs.
# Ratio weights inside each category must sum to 1.
# Category weights inside CATEGORIES must sum to 1.
# Financial Sustainability is scored separately.

CATEGORIES = {
    "Profitability": {
        "weight": 0.30,
        "ratios": {
            "net-margin": {
                "metrics": ["net-margin"],
                "formula": "direct",
                "weight": 0.35,
                "direction": 1
            },
            "return_on_equity": {
                "metrics": ["profit-after-tax", "equity-average"],
                "formula": "divide",
                "weight": 0.30,
                "direction": 1
            },
            "return-on-assets-[roa]": {
                "metrics": ["return-on-assets-[roa]"],
                "formula": "direct",
                "weight": 0.25,
                "direction": 1
            },
            "ebt-margin": {
                "metrics": ["ebt-margin"],
                "formula": "direct",
                "weight": 0.10,
                "direction": 1
            },
        },
    },
    "Growth": {
        "weight": 0.25,
        "ratios": {
            "revenue": {
                "metrics": ["revenue"],
                "formula": "yoy",
                "weight": 0.45,
                "direction": 1
            },
            "ebt_growth": {
                "metrics": ["ebt"],
                "formula": "yoy",
                "weight": 0.20,
                "direction": 1
            },
            "diluted_eps_growth": {
                "metrics": ["eps-diluted"],
                "formula": "yoy",
                "weight": 0.20,
                "direction": 1
            },
            "net_income_growth": {
                "metrics": ["net-income"],
                "formula": "yoy",
                "weight": 0.15,
                "direction": 1
            },
        },
    },
    "Operating Efficiency": {
        "weight": 0.15,
        "ratios": {
            "asset-utilization-ratio": {
                "metrics": ["asset-utilization-ratio"],
                "formula": "direct",
                "weight": 0.45,
                "direction": 1
            },
            "operating_cost_ratio": {
                "metrics": ["operating-expenses", "revenue"],
                "formula": "divide",
                "weight": 0.45,
                "direction": -1
            },
            "administrative_cost_ratio": {
                "metrics": ["selling-general-and-administrative", "revenue"],
                "formula": "divide",
                "weight": 0.10,
                "direction": -1
            },
        },
    },
    "Cash Flow Generation": {
        "weight": 0.10,
        "ratios": {
            "fcf-margin": {
                "metrics": ["fcf-margin"],
                "formula": "direct",
                "weight": 0.35,
                "direction": 1
            },
            "operating_cash_flow_margin": {
                "metrics": ["cash-from-operations", "revenue"],
                "formula": "divide",
                "weight": 0.30,
                "direction": 1
            },
            "cash_return_on_assets": {
                "metrics": ["cash-from-operations", "assets-average"],
                "formula": "divide",
                "weight": 0.20,
                "direction": 1
            },
            "cash_conversion": {
                "metrics": ["cash-from-operations", "profit-after-tax"],
                "formula": "divide",
                "weight": 0.15,
                "direction": 1
            },
        },
    },
    "Solvency & Liquidity": {
        "weight": 0.20,
        "ratios": {
            "equity_to_assets": {
                "metrics": ["equity-average", "assets-average"],
                "formula": "divide",
                "weight": 0.40,
                "direction": 1
            },
            "cash_to_assets": {
                "metrics": ["cash-and-equivalents", "assets-average"],
                "formula": "divide",
                "weight": 0.40,
                "direction": 1
            },
            "debt_to_equity": {
                "metrics": ["total-debt", "equity-average"],
                "formula": "divide",
                "weight": 0.10,
                "direction": -1
            },
            "interest-coverage-ratio": {
                "metrics": ["interest-coverage-ratio"],
                "formula": "direct",
                "weight": 0.10,
                "direction": 1
            },
        },
    },
}


# FINANCIAL SUSTAINABILITY / ACQUISITION FEASIBILITY

FINANCIAL_SUSTAINABILITY = {
    "relative_market_cap": {
        "metrics": ["market-capitalization"],
        "formula": "relative_to_reference",
        "weight": 0.80,
        "direction": -1
    },
    "total_debt": {
        "metrics": ["total-debt"],
        "formula": "direct",
        "weight": 0.20,
        "direction": -1
    },
}
