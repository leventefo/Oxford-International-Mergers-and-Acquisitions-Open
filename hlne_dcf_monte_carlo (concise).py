import numpy as np

# ---------------- Settings ----------------
np.random.seed(42)
N_SIMS     = 10000
YEARS      = 5
FIRST_YEAR = 2027
SPEED      = 0.5
BOOTSTRAP  = True

# ---------------- History ($m, fiscal years ending 31 March) ----------------
mgmt_fees = {2017: 172.7, 2018: 195.0, 2019: 217.8, 2020: 244.9,
             2021: 289.4, 2022: 314.2, 2023: 371.9, 2024: 451.9,
             2025: 513.9, 2026: 584.2}
incentive_fees = {2017: 7.1, 2018: 49.0, 2019: 34.4, 2020: 29.1,
                  2021: 52.2, 2022: 53.7, 2023: 149.9, 2024: 101.9,
                  2025: 198.3, 2026: 170.6}
total_revenues = {2022: 367.9, 2023: 521.8, 2024: 553.8, 2025: 713.0, 2026: 759.0}
total_expenses = {2022: 197.5, 2023: 287.8, 2024: 307.4, 2025: 396.4, 2026: 434.1}
FRE_LAST = 344.5
incentive_comp_hist = {2022: 25.4, 2023: 74.4, 2024: 48.4}
incentive_fee_hist  = {2022: 53.7, 2023: 156.9, 2024: 101.9}
da_pct_hist    = {2017: 0.0106, 2018: 0.0077, 2019: 0.0118, 2020: 0.0120,
                  2021: 0.0121, 2022: 0.0149, 2023: 0.0141, 2024: 0.0148,
                  2025: 0.0130, 2026: 0.0130}
capex_pct_hist = {2017: 0.0071, 2018: 0.0092, 2019: 0.0213, 2020: 0.0072,
                  2021: 0.0546, 2022: 0.0232, 2023: 0.0090, 2024: 0.0200,
                  2025: 0.0170, 2026: 0.0077}
UNREALIZED_CARRY = 1500

# ---------------- Valuation inputs ----------------
TAX_RATE             = 0.232
RISK_FREE            = 0.0510
PRE_TAX_COST_OF_DEBT = 0.0526
BETA                 = 1.10
BETA_SE              = 0.243
ERP_CURRENT          = 0.0441
ERP_HISTORY          = [0.0569, 0.0508, 0.0596, 0.0520, 0.0472,
                        0.0424, 0.0594, 0.0460, 0.0433, 0.0423]
INCENTIVE_EXTRA_RISK = 0.03

G_LOW, G_MODE, G_HIGH = 0.015, 0.025, 0.035
EXIT_MULTIPLES        = [14.04]
PERPETUITY_WEIGHT     = 0.5

CASH          = 336.2
INVESTMENTS   = 854.6
DEBT          = 268.7
TRA_LIABILITY = 219.6
SHARES        = 56.283
CURRENT_PRICE = 93.73
NWC_PCT       = 0.0
TARGET_OVERRIDE = {}

# ---------------- History -> ratios ----------------
mgmt_growth = {y: mgmt_fees[y] / mgmt_fees[y - 1] - 1
               for y in mgmt_fees if y - 1 in mgmt_fees}
incentive_ratio = {y: incentive_fees[y] / mgmt_fees[y] for y in incentive_fees}

payout = np.median([incentive_comp_hist[y] / incentive_fee_hist[y]
                    for y in incentive_comp_hist])
INCENTIVE_KEPT = 1 - payout

mgmt_margin = {}
for y in total_revenues:
    operating_profit = total_revenues[y] - total_expenses[y]
    incentive_part   = incentive_fees[y] * INCENTIVE_KEPT
    mgmt_margin[y]   = (operating_profit - incentive_part) / mgmt_fees[y]

DA_PCT    = np.median(list(da_pct_hist.values()))
CAPEX_PCT = np.median(list(capex_pct_hist.values()))

MGMT_LAST      = mgmt_fees[max(mgmt_fees)]
TOTAL_REV_LAST = MGMT_LAST + incentive_fees[max(incentive_fees)]

print("=" * 66)
print("PART 4  HISTORY -> RATIOS")
print("=" * 66)
print("Ratio                     Years   Median   Volatility")
drivers = {
    "Mgmt Fee Growth":       (mgmt_growth,     True, None),
    "Mgmt Fee Margin":       (mgmt_margin,     True, None),
    "Incentive % Mgmt Fees": (incentive_ratio, True, 0.0),
}
for name, (hist, _, _) in drivers.items():
    v = np.array([hist[y] for y in sorted(hist)])
    print(f"{name:24s} {len(v):5d}   {np.median(v):7.2%}   {v.std():7.2%}")
print()
print(f"Fixed: D&A {DA_PCT:.2%} of revenue | capex {CAPEX_PCT:.2%} | "
      f"NWC {NWC_PCT:.2%}")
print(f"Fixed: shareholders keep {INCENTIVE_KEPT:.0%} of incentive fees "
      f"(staff get {payout:.0%})")

# ---------------- Monte Carlo: business drivers ----------------
def simulate(history, target_override=None, floor=None):
    values = np.array([history[y] for y in sorted(history)])
    latest = values[-1]
    paths = np.zeros((N_SIMS, YEARS))
    for sim in range(N_SIMS):
        sample = np.random.choice(values, size=len(values), replace=True) \
                 if BOOTSTRAP else values
        target = target_override if target_override is not None else np.median(sample)
        volatility = sample.std()
        current = latest
        for t in range(YEARS):
            current = current + SPEED * (target - current) \
                      + np.random.normal(0, volatility)
            if floor is not None:
                current = max(current, floor)
            paths[sim, t] = current
    return paths

sims = {name: simulate(hist, TARGET_OVERRIDE.get(name), floor)
        for name, (hist, _, floor) in drivers.items()}

print()
print("=" * 66)
print("PART 5  SIMULATED ASSUMPTIONS (10,000 futures)")
print("=" * 66)
for name, paths in sims.items():
    low, base, high = (np.percentile(paths, p, axis=0) for p in (5, 50, 95))
    print(f"\n{name}")
    print("FY       Bear      Base      Bull")
    for i in range(YEARS):
        print(f"{FIRST_YEAR + i}  {low[i]:7.2%}   {base[i]:7.2%}   {high[i]:7.2%}")

missing = [k for k, v in {"TAX_RATE": TAX_RATE, "BETA": BETA, "BETA_SE": BETA_SE,
                          "INCENTIVE_EXTRA_RISK": INCENTIVE_EXTRA_RISK,
                          "CASH": CASH, "INVESTMENTS": INVESTMENTS, "DEBT": DEBT,
                          "TRA_LIABILITY": TRA_LIABILITY, "SHARES": SHARES,
                          "CURRENT_PRICE": CURRENT_PRICE}.items() if v is None]
if missing:
    raise SystemExit("\nBusiness drivers simulated. Fill in these inputs to "
                     "run the WACC and DCF: " + ", ".join(missing))

# ---------------- Monte Carlo: WACC and terminal inputs ----------------
beta_w = np.random.normal(BETA, BETA_SE, N_SIMS)
erp_w  = np.maximum(np.random.normal(ERP_CURRENT, np.std(ERP_HISTORY, ddof=1), N_SIMS), 0.02)

E = SHARES * CURRENT_PRICE
D = DEBT
w_E, w_D = E / (D + E), D / (D + E)
cost_of_equity_w = RISK_FREE + beta_w * erp_w
after_tax_debt   = PRE_TAX_COST_OF_DEBT * (1 - TAX_RATE)
wacc_w = w_E * cost_of_equity_w + w_D * after_tax_debt

g_w = np.random.triangular(G_LOW, G_MODE, G_HIGH, size=N_SIMS)
g_w = np.minimum(g_w, wacc_w - 0.01)

mult_w = (np.random.choice(EXIT_MULTIPLES, size=N_SIMS, replace=True)
          if EXIT_MULTIPLES else None)

print()
print("=" * 66)
print("PART 5B  WACC (10,000 worlds)")
print("=" * 66)
print(f"Weights: equity {w_E:.1%}  debt {w_D:.1%}   "
      f"| after-tax cost of debt {after_tax_debt:.2%}")
print("                      5th pct    Median   95th pct")
for label, arr in [("Beta", beta_w), ("ERP", erp_w),
                   ("Cost of equity", cost_of_equity_w), ("WACC", wacc_w),
                   ("Terminal growth", g_w)] + \
                  ([("Exit multiple (x)", mult_w)] if mult_w is not None else []):
    lo, mid, hi = np.percentile(arr, [5, 50, 95])
    fmt = (lambda v: f"{v:8.2f}") if label in ("Beta", "Exit multiple (x)") \
          else (lambda v: f"{v:8.2%}")
    print(f"{label:18s} {fmt(lo)}  {fmt(mid)}  {fmt(hi)}")

# ---------------- Cash flows and DCF ----------------
g_paths   = sims["Mgmt Fee Growth"]
m_paths   = sims["Mgmt Fee Margin"]
inc_paths = sims["Incentive % Mgmt Fees"]

value_A      = np.zeros(N_SIMS)
value_B      = np.zeros(N_SIMS)
value_ex     = np.zeros(N_SIMS)
tv_ebitda    = np.zeros(N_SIMS)
tv_perp_2031 = np.zeros(N_SIMS)

for sim in range(N_SIMS):
    r_A = wacc_w[sim]
    r_B = r_A + INCENTIVE_EXTRA_RISK
    g   = g_w[sim]
    pv_forecast = 0
    mgmt = MGMT_LAST
    prev_rev = TOTAL_REV_LAST
    cash_B_years, kept_B_years = [], []
    for t in range(YEARS):
        discount_A = (1 + r_A) ** (t + 1)
        discount_B = (1 + r_B) ** (t + 1)

        mgmt   = mgmt * (1 + g_paths[sim, t])
        fre    = mgmt * m_paths[sim, t]
        inc    = mgmt * inc_paths[sim, t]
        rev    = mgmt + inc
        cash_A = (fre * (1 - TAX_RATE)
                  + rev * DA_PCT
                  - rev * CAPEX_PCT
                  - NWC_PCT * (rev - prev_rev))
        prev_rev = rev
        value_A[sim] += cash_A / discount_A
        pv_forecast  += cash_A / discount_A

        cash_B = inc * INCENTIVE_KEPT * (1 - TAX_RATE)
        cash_B_years.append(cash_B)
        kept_B_years.append(inc * INCENTIVE_KEPT)
        value_B[sim] += cash_B / discount_B
        pv_forecast  += cash_B / discount_B

    term_A = cash_A * (1 + g) / (r_A - g)
    term_B = np.mean(cash_B_years) * (1 + g) / (r_B - g)
    value_A[sim] += term_A / (1 + r_A) ** YEARS
    value_B[sim] += term_B / (1 + r_B) ** YEARS
    tv_perp_2031[sim] = term_A + term_B * ((1 + r_A) / (1 + r_B)) ** YEARS

    tv_ebitda[sim] = fre + rev * DA_PCT + np.mean(kept_B_years)
    if mult_w is not None:
        value_ex[sim] = pv_forecast + tv_ebitda[sim] * mult_w[sim] / (1 + r_A) ** YEARS

# ---------------- Equity bridge ----------------
bridge = CASH + INVESTMENTS - DEBT - TRA_LIABILITY

business_value = value_A + value_B
prices_perp    = (business_value + bridge) / SHARES

if mult_w is not None:
    prices_exit = (value_ex + bridge) / SHARES
    prices = PERPETUITY_WEIGHT * prices_perp + (1 - PERPETUITY_WEIGHT) * prices_exit
else:
    prices_exit = None
    prices = prices_perp

# ---------------- Results ----------------
print()
print("=" * 66)
print("PART 8  DCF RESULTS (10,000 share prices) - Hamilton Lane")
print("=" * 66)
if prices_exit is not None:
    print("                          Perpetuity   Exit multiple   Blend")
    for label, q in [("Median", 50), ("Bear (10th pct)", 10), ("Bull (90th pct)", 90)]:
        print(f"{label:24s} ${np.percentile(prices_perp, q):8.2f}     "
              f"${np.percentile(prices_exit, q):8.2f}     ${np.percentile(prices, q):8.2f}")
    print(f"Blend = {PERPETUITY_WEIGHT:.0%} perpetuity / {1 - PERPETUITY_WEIGHT:.0%} exit multiple")
    print()
print(f"Price target (median):            ${np.median(prices):8.2f}")
print(f"Bear case (10th percentile):      ${np.percentile(prices, 10):8.2f}")
print(f"Bull case (90th percentile):      ${np.percentile(prices, 90):8.2f}")
print(f"Today's price:                    ${CURRENT_PRICE:8.2f}")
print(f"Probability above today's price:  {(prices > CURRENT_PRICE).mean():.0%}")

share_A = np.median(value_A) / np.median(business_value)
print()
print("Where the value comes from (median future):")
print(f"  Stream A, management fees:  ${np.median(value_A):8,.0f}m  ({share_A:.0%})")
print(f"  Stream B, incentive fees:   ${np.median(value_B):8,.0f}m  ({1 - share_A:.0%})")

print()
print("Sanity checks:")
print(f"  Implied business value / FY2026 FRE:  "
      f"{np.median(business_value) / FRE_LAST:5.1f}x  (compare with peers)")

carry_net = UNREALIZED_CARRY * INCENTIVE_KEPT * (1 - TAX_RATE)
print(f"  Stream B value: ${np.median(value_B):,.0f}m  vs  unrealized carry "
      f"after staff and tax: ${carry_net:,.0f}m")

implied_mult = np.median(tv_perp_2031 / tv_ebitda)
line = f"  Perpetuity method implies a 2031 EV/EBITDA of {implied_mult:4.1f}x"
if mult_w is not None:
    line += f"  vs median exit multiple {np.median(mult_w):4.1f}x"
print(line)
