import numpy as np

# =====================================================================
#   HAMILTON LANE (HLNE) - MONTE CARLO DCF, BUILT FOR AN ASSET MANAGER
# =====================================================================
#
#   HOW TO USE THIS FILE
#   1. Read PART 0 once: it explains the whole idea in plain English.
#   2. Fill in the inputs in PART 3 (marked  >>> FILL IN <<<).
#   3. Run the file. It prints the simulated assumptions, then the
#      share-price results and some sanity checks.
#
#   TABLE OF CONTENTS
#   PART 0  The big idea, in plain English
#   PART 1  Settings for the simulation
#   PART 2  Real history (with sources)
#   PART 3  Valuation inputs you must fill in
#           3A  The WACC build (discount rate)
#           3B  Terminal value: growth and exit multiple
#           3C  Equity bridge items and share count
#   PART 4  Turn the history into ratios
#   PART 5  Simulate 10,000 possible futures (Monte Carlo)
#           5A  Business drivers   5B  WACC and terminal inputs
#   PART 6  Turn each future into cash, and cash into value
#   PART 7  Equity bridge: from business value to value per share
#   PART 8  Results and sanity checks
#   PART 9  Known simplifications (read before presenting)
#
# =====================================================================


# =====================================================================
# PART 0  THE BIG IDEA, IN PLAIN ENGLISH
# =====================================================================
#
# WHAT HAMILTON LANE DOES
#   Pension funds, insurers and wealthy individuals give Hamilton Lane
#   money to invest in "private markets": companies that are not on the
#   stock exchange. Hamilton Lane is paid in two ways:
#
#   (A) MANAGEMENT FEES. A small percentage (roughly half a percent) of
#       the money it manages, charged every year whether the
#       investments do well or badly. Like a gym membership: steady
#       and predictable.
#
#   (B) INCENTIVE FEES (also called "carried interest" or "carry").
#       A share of the PROFIT when an investment is sold for more than
#       a minimum return. Like a bonus: big in good years, small in
#       bad years, and nobody knows exactly when it will arrive.
#
# WHY WE VALUE THE TWO STREAMS SEPARATELY
#   1. Investors pay more for income they can count on than for income
#      that might or might not come.
#   2. Management fees are dependable, so they deserve a "full" value.
#   3. Incentive fees are uncertain, so they deserve a LOWER value per
#      dollar. We do this by discounting them at a higher rate
#      (PART 3: INCENTIVE_EXTRA_RISK).
#   4. If we mixed them into one revenue line, the jumpy incentive fees
#      would make the steady part look jumpy too, and we would value the
#      whole company as if all of it were uncertain.
#
# WHAT A DCF IS (Discounted Cash Flow)
#   1. A company is worth the cash it will hand out in the future.
#   2. A dollar next year is worth less than a dollar today (you could
#      invest today's dollar and earn a return in the meantime).
#   3. So we estimate each future year's cash, shrink ("discount") each
#      one back to today's value, and add them up.
#   4. For the years after our forecast, we assume the cash grows at a
#      slow, steady rate forever (the "terminal value").
#
# WHAT THE MONTE CARLO ADDS
#   1. Nobody knows next year's fee growth or margin for sure.
#   2. Instead of guessing ONE future, we let the computer draw 10,000
#      possible futures, each one realistic given the company's history.
#   3. We run a full DCF on every one of them -> 10,000 share prices.
#   4. The middle of those prices is our price target; the spread shows
#      how confident we can be.
#
# WHAT IS SIMULATED AND WHAT IS FIXED (and why)
#   Simulated (they move a lot and drive the value):
#     - growth of management fees
#     - profit margin on management fees (see PART 2)
#     - incentive fees, as a % of management fees
#   Fixed at their historical median (they barely matter here):
#     - D&A, capex, working capital
#   Why fixed? Hamilton Lane's main assets are its people and its client
#   relationships, not factories or shops. It spends only about 1% of
#   revenue on equipment (capex). Simulating something that small adds
#   noise to the result without adding information.
# =====================================================================


# =====================================================================
# PART 1  SETTINGS FOR THE SIMULATION
# =====================================================================
np.random.seed(42)    # fixes the random numbers so every run gives the
                      # same result; change 42 to see a different draw

N_SIMS     = 10000    # number of simulated futures
YEARS      = 5        # forecast years
FIRST_YEAR = 2027     # first forecast year = FY2027 (Apr 2026 - Mar 2027)
SPEED      = 0.5      # each year, close half of the gap to the long-run level
BOOTSTRAP  = True     # True = every simulated future gets its own
                      # "version" of history (explained in PART 5)


# =====================================================================
# PART 2  REAL HISTORY (with sources)
# =====================================================================
# Hamilton Lane's fiscal year ends on 31 March. "2025" = the year
# from 1 April 2024 to 31 March 2025.
# All amounts in $ millions.

# --- (A) Management and advisory fees ---------------------------------
# Source: 10-K FY2019 (2017-2019), 10-K FY2022 (2020-2022),
#         10-K FY2024 (2023-2024), Q4 FY2026 earnings release (2025-2026)
mgmt_fees = {2017: 172.7, 2018: 195.0, 2019: 217.8, 2020: 244.9,
             2021: 289.4, 2022: 314.2, 2023: 371.9, 2024: 451.9,
             2025: 513.9, 2026: 584.2}

# --- (B) Incentive fees -----------------------------------------------
# Same sources. Excludes the small amount earned by consolidated funds.
# Note how much this jumps around (7 -> 49 -> 34 ... 150 -> 102 -> 198).
incentive_fees = {2017: 7.1, 2018: 49.0, 2019: 34.4, 2020: 29.1,
                  2021: 52.2, 2022: 53.7, 2023: 149.9, 2024: 101.9,
                  2025: 198.3, 2026: 170.6}

# --- Income statement totals (for the margin on management fees) --------
# We need: how much of each dollar of management fees is left as
# operating profit, after ALL running costs (salaries, stock-based pay,
# offices, IT, D&A). PART 4 works it out from these two lines:
#   operating profit = total revenues - total expenses
# Sources: 10-K FY2024 (2023-2024, excluding consolidated funds),
#          Q4 FY2026 earnings release (2025-2026),
#          10-K FY2023 (2022: compensation $129.2m + G&A $68.3m,
#          backed out from the FY2023 changes of +$69.2m and +$21.1m).
total_revenues = {2022: 367.9, 2023: 521.8, 2024: 553.8, 2025: 713.0, 2026: 759.0}
total_expenses = {2022: 197.5, 2023: 287.8, 2024: 307.4, 2025: 396.4, 2026: 434.1}

# WHY NOT USE THE COMPANY'S OWN "FRE MARGIN"?
#   Hamilton Lane reports "Fee Related Earnings" (FRE), its own measure
#   of the steady profit. But from FY2025 it changed the definition:
#   1. FRE now INCLUDES some evergreen-fund performance fees, and
#   2. FRE now appears to EXCLUDE stock-based pay ($51m in FY2026).
#   Both push the reported margin up (to 48-50%), so it is not
#   comparable with earlier years, and it treats stock pay as if it
#   were free. Working from the GAAP income statement keeps every year
#   on the same definition and keeps stock pay as a real cost.

FRE_LAST = 344.5   # FY2026 FRE as REPORTED ($m), only used in PART 8 to
                   # compare with peers, who also report FRE

# --- Share of incentive fees paid out to employees -----------------------
# When Hamilton Lane earns carry, a large part goes to its investment
# staff as bonus. Only the rest is profit for shareholders.
# Source: 10-K FY2024 FRE reconciliation ("incentive fee related
# compensation" vs "incentive fees").
incentive_comp_hist = {2022: 25.4, 2023: 74.4, 2024: 48.4}
incentive_fee_hist  = {2022: 53.7, 2023: 156.9, 2024: 101.9}

# --- D&A, capex (% of total revenue) -----------------------------------
# Source: edgar_pull_hlne.py output (SEC EDGAR, 10-K data)
da_pct_hist    = {2017: 0.0106, 2018: 0.0077, 2019: 0.0118, 2020: 0.0120,
                  2021: 0.0121, 2022: 0.0149, 2023: 0.0141, 2024: 0.0148,
                  2025: 0.0130, 2026: 0.0130}
capex_pct_hist = {2017: 0.0071, 2018: 0.0092, 2019: 0.0213, 2020: 0.0072,
                  2021: 0.0546, 2022: 0.0232, 2023: 0.0090, 2024: 0.0200,
                  2025: 0.0170, 2026: 0.0077}

# --- Unrealized carry -------------------------------------------------
# Carry already "built up" in the funds but not yet paid out, because
# the investments have not been sold yet. $1.5bn at 31 March 2026
# (Q4 FY2026 earnings call). Used only as a sanity check in PART 8.
UNREALIZED_CARRY = 1500


# =====================================================================
# PART 3  VALUATION INPUTS YOU MUST FILL IN   >>> FILL IN <<<
# =====================================================================
# Every value set to None must be filled in before the DCF runs.
# The simulation (PART 5) still runs and prints without them.

# ---------------------------------------------------------------------
# PART 3A  THE WACC BUILD (the discount rate)
# ---------------------------------------------------------------------
# WHAT THE WACC IS
#   1. Hamilton Lane's money comes from two groups: shareholders
#      (equity) and lenders (debt).
#   2. Both want a return. Lenders want interest. Shareholders want
#      more, because they are paid last and carry more risk.
#   3. WACC = the average of the two returns, weighted by how much of
#      the company each group funds:
#        WACC = E/(D+E) x cost of equity + D/(D+E) x cost of debt x (1 - tax)
#      E = market value of equity, D = debt.
#   4. The "(1 - tax)" is there because interest is tax-deductible:
#      every $1 of interest cuts the tax bill, so debt costs less than
#      its interest rate.
#   5. Hamilton Lane borrows very little (~$0.3bn of debt against
#      several $bn of equity), so its WACC is almost exactly its cost
#      of equity. The cost-of-debt inputs barely move the result.
#
# COST OF EQUITY (CAPM):  risk-free rate + beta x equity risk premium
#   - Risk-free rate: what you earn with no risk (US government bond).
#   - Equity risk premium (ERP): the extra return investors demand
#     for owning the whole stock market instead of government bonds.
#   - Beta: how strongly HLNE moves with the market. Beta 1.3 means
#     that when the market moves 1%, HLNE tends to move 1.3%. More
#     movement = more risk = higher required return.
#
# FIXED vs SIMULATED
#   Fixed (observable today, little to argue about): tax rate,
#     risk-free rate, cost of debt.
#   Simulated (estimates with real uncertainty, so each of the 10,000
#     worlds gets its own value): beta, ERP, terminal growth, exit
#     multiple.  How each is drawn is explained in PART 5B.

TAX_RATE = 0.232
#   FIXED. 21% federal + 2.2% state = 23.2%, from the LATEST 10-K
#   (FY2026) tax rate reconciliation: "State and local income tax, net
#   of federal effect" = 2.2%. Earlier years were 2.8% (FY2024),
#   3.4% (FY2023), 3.3% (FY2022), so 24% is a reasonable sensitivity. Use a FULL corporate rate (federal 21% + state taxes), NOT
#   the median effective rate from the 10-K (the McDonald's approach).
#   Why the McDonald's approach does not work here:
#   1. Hamilton Lane is an "Up-C" (see SHARES in PART 3C). Part of its
#      profit belongs to insiders through a partnership, and the
#      company does not pay corporate tax on that part. That pulls the
#      reported effective rate well below the true rate.
#   2. We count those insiders' units as shares.
#   3. So we value ALL the profit as if it belonged to shareholders,
#      and it must be taxed as if it does.
#   Where: 10-K income tax note ("statutory rate" + "state and local
#   taxes" lines of the rate reconciliation).

RISK_FREE = 0.0510
#   FIXED. 10-year US Treasury yield at the close on 13 Nov 2026 =
#   5.10% (FRED series DGS10), the same date as CURRENT_PRICE and the
#   comps (all market data as of the 13 Nov 2026 close).
#   Why the 10-year: our cash flows run for many years, so we compare
#   with a long-term safe investment, not a 3-month bill.

PRE_TAX_COST_OF_DEBT = 0.0526
#   FIXED. What Hamilton Lane pays to borrow, before tax.
#   McDonald's approach (yield on its traded bonds) does not work:
#   Hamilton Lane's notes were sold privately to a few investors
#   ("private placement"), so they do not trade and have no market
#   yield. Instead:
#   - Interest expense / average debt: $14.952m / $284.4m (average of
#     $290.303m and $278.420m, 10-K FY2026) = 5.26%
#   - Cross-check, rates in the 10-K FY2026: senior notes 5.28%
#     (due 2029), term loan 5.50% (prime - 1.25%), 2020 term loan 3.50%.
#   Because debt is only a few % of the company, this number hardly
#   changes the WACC.

BETA    = 1.10
BETA_SE = 0.243
#   SIMULATED. Centre: FactSet 3-year ADJUSTED beta = 1.10 (citable).
#   Cross-check: our own 2-year weekly regression vs the S&P 500
#   (beta_regression.py) gives 1.144 raw, 1.096 adjusted -> same answer.
#   "Adjusted" (Blume) = 2/3 x raw beta + 1/3 x 1.0, because betas tend
#   to drift back towards the market average of 1 over time.
#   BETA_SE comes from our regression (FactSet does not report one):
#   about 95% of simulated betas land within BETA +/- 2 x SE.

ERP_CURRENT = 0.0441
#   Damodaran's implied ERP for the S&P 500 on 1 November 2026
#   (trailing 12-month cash flows, adjusted payout), from damodaran.com.
#   Why the CURRENT figure: our share price and risk-free rate are
#   today's, so the ERP should be today's too. Using a different ERP
#   would mix a view on HLNE with a view on whether the whole market is
#   mispriced ("market-neutral" valuation, Damodaran's own practice).

ERP_HISTORY = [0.0569, 0.0508, 0.0596, 0.0520, 0.0472,
               0.0424, 0.0594, 0.0460, 0.0433, 0.0423]
#   Damodaran's implied US ERP at the START of 2017, 2018, ... 2026.
#   Used ONLY for the spread of the simulation, not the centre: its
#   standard deviation (~0.7 points) sets how widely the simulated ERP
#   swings around today's 4.41% (see PART 5B).

INCENTIVE_EXTRA_RISK = 0.03
#   Extra discount rate added on top of WACC for INCENTIVE fees only,
#   e.g. 0.03 = 3 percentage points. This is how we "pay less" for the
#   uncertain stream (see PART 0). 0 = treat it as safe as management
#   fees. Pick a number and be ready to defend it, then test a range.


# ---------------------------------------------------------------------
# PART 3B  TERMINAL VALUE: WHAT HAPPENS AFTER 2031
# ---------------------------------------------------------------------
# Two standard methods; the model runs BOTH in every world and blends
# them (PART 7). Seeing both is a check on each other.
#
# METHOD 1 - PERPETUITY GROWTH: cash keeps growing at g forever.
G_LOW, G_MODE, G_HIGH = 0.015, 0.025, 0.035
#   SIMULATED, triangular distribution: any value between 1.5% and
#   3.5%, most often near 2.5%, rarely near the edges.
#   Why 2.5%: ~2% inflation + a little real growth. It must stay below
#   the risk-free rate (4.86%): no company can outgrow the whole
#   economy forever.
#   Safety rule: if WACC - g is under 1 point in a world, g is set to
#   WACC - 1%. (As WACC - g gets close to 0, the formula
#   cash / (WACC - g) shoots towards infinity.)
#
# METHOD 2 - EXIT MULTIPLE: in 2031 the business is "sold" at a
# multiple of its EBITDA, like comparable companies trade.
EXIT_MULTIPLES = [14.04]
#   Set to 14.0x to match the Excel model (Non-Time-Based Assumptions
#   E29): ~Tier 1 peer median (FactSet) and HLNE's own LTM multiple on
#   this model's EBITDA definition (~13.7x). To also test the peer-
#   consistent case, use [14.0, 16.8]: each world then picks one.
#   SIMULATED. A list of Hamilton Lane's EV/EBITDA at each fiscal
#   year-end (up to 10 years, FY2017-FY2026). Each world picks one at
#   random, with replacement.
#   !!! Do NOT copy FactSet's EV/EBITDA directly. It has to use the
#   same definitions as this model, or the multiple does not fit:
#     EV     = (Class A shares + insider units) x share price
#              + debt + TRA liability - cash - investments
#     EBITDA = operating income + D&A  (GAAP, after stock pay)
#   Why: in PART 7 we ADD investments and SUBTRACT the TRA separately.
#   If the multiple already included them, they would count twice.
#   Example format: [18.5, 22.1, 25.0, ...]
#   Leave as None to use the perpetuity method only.

PERPETUITY_WEIGHT = 0.5
#   Weight of method 1 in the final blend (0.5 = 50/50).
#   1.0 = perpetuity only, 0.0 = exit multiple only.

# ---------------------------------------------------------------------
# PART 3C  EQUITY BRIDGE ITEMS AND SHARE COUNT
# ---------------------------------------------------------------------
# Values below are at 30 Sep 2026 (10-Q for Q2 FY2027, condensed
# consolidated balance sheet), the same date as the share count.

CASH = 336.2
#   $m, cash and cash equivalents. Added: shareholders own it.

INVESTMENTS = 854.6
#   $m, the "Investments" line on the balance sheet: Hamilton Lane's
#   OWN money invested in its funds, next to its clients (GP
#   commitments). Added, because:
#   1. Our cash flows only cover fees.
#   2. The gains on this money appear BELOW operating profit, so they
#      are not in our cash flows.
#   3. If we did not add the investments, shareholders would get no
#      credit for assets they own.

DEBT = 268.7
#   $m, total debt (senior notes + term loans drawn). Subtracted:
#   lenders get paid before shareholders. Also used for the WACC
#   weights (book value; close to market value for this debt).

TRA_LIABILITY = 219.6
#   $m, "payable to related parties pursuant to tax receivable
#   agreement" (balance sheet). Subtracted, because:
#   1. When insiders swap their partnership units for shares, the
#      company gets a tax saving.
#   2. A contract (the TRA) says it must hand most of that saving back
#      to those insiders.
#   3. So it is money owed, just like debt.

SHARES = 56.283
#   Millions, at 30 Sep 2026 (10-Q, equity note):
#   44,002,633 Class A + 12,280,789 HLA Class B and Class C units = 56.283m
#   (10-Q Q2 FY27, Note 12 EPS, 'Assumed conversion of Class B and Class C units').
#   Class B shares are held by the insiders who own partnership units,
#   so Class A + Class B counts every owner's claim.
#   Why both? Hamilton Lane is an "Up-C":
#   1. Public investors own Class A shares of Hamilton Lane Inc.
#   2. Founders and staff own units of the operating partnership
#      (Hamilton Lane Advisors), which they can swap 1-for-1 into
#      Class A shares.
#   3. Our cash flows are for the WHOLE business, including the
#      insiders' part.
#   4. So we must divide by everyone's claim, not by Class A only.
#      Dividing by Class A only would overstate value per share.

CURRENT_PRICE = 93.73
#   FactSet close, 13 Nov 2026.
#   $, HLNE share price on your valuation date. Also used for the
#   WACC weights: E = SHARES x CURRENT_PRICE.

# --- Fixed working-capital assumption -----------------------------------
NWC_PCT = 0.0
#   Working capital as % of revenue (money tied up in unpaid bills etc.).
#   Set to 0 as a deliberate simplification: fees are billed regularly
#   and EDGAR has no clean receivables line for Hamilton Lane. Change
#   it if you build NWC from the balance sheet.

# --- Optional: replace a history-based long-run level -------------------
# Leave empty to let history decide. Example with a reason:
#   "Mgmt Fee Margin": 0.45,   # e.g. if you expect operating leverage
TARGET_OVERRIDE = {
}


# =====================================================================
# PART 4  TURN THE HISTORY INTO RATIOS
# =====================================================================
# The model forecasts RATIOS, not dollar amounts, because ratios stay
# comparable as the company grows (a $10m change meant more in 2017
# than in 2026).

# Growth of management fees: this year / last year - 1
mgmt_growth = {y: mgmt_fees[y] / mgmt_fees[y - 1] - 1
               for y in mgmt_fees if y - 1 in mgmt_fees}

# Incentive fees as a % of management fees.
# Why tie incentive fees to management fees?
#   1. Carry is earned on the money Hamilton Lane manages.
#   2. More money managed today -> more investments that can earn
#      carry when they are sold in later years.
#   3. So as management fees grow, the "normal" level of incentive
#      fees should grow with them; the ratio captures the lumpiness.
incentive_ratio = {y: incentive_fees[y] / mgmt_fees[y] for y in incentive_fees}

# Share of incentive fees that shareholders keep (after staff bonuses)
payout = np.median([incentive_comp_hist[y] / incentive_fee_hist[y]
                    for y in incentive_comp_hist])
INCENTIVE_KEPT = 1 - payout

# Margin on management fees, from the income statement:
#   1. operating profit = total revenues - total expenses
#   2. part of that profit came from incentive fees:
#      incentive fees x share kept
#   3. the rest came from management fees:
#      operating profit - incentive part
#   4. margin = that rest / management fees
mgmt_margin = {}
for y in total_revenues:
    operating_profit = total_revenues[y] - total_expenses[y]
    incentive_part   = incentive_fees[y] * INCENTIVE_KEPT
    mgmt_margin[y]   = (operating_profit - incentive_part) / mgmt_fees[y]

# Fixed lines: historical median
DA_PCT    = np.median(list(da_pct_hist.values()))
CAPEX_PCT = np.median(list(capex_pct_hist.values()))

MGMT_LAST = mgmt_fees[max(mgmt_fees)]              # FY2026 management fees
TOTAL_REV_LAST = MGMT_LAST + incentive_fees[max(incentive_fees)]

print("=" * 66)
print("PART 4  HISTORY -> RATIOS")
print("=" * 66)
print("Ratio                     Years   Median   Volatility")
drivers = {
    # name:                  (history,          higher_is_good, floor)
    "Mgmt Fee Growth":       (mgmt_growth,      True,  None),
    "Mgmt Fee Margin":       (mgmt_margin,      True,  None),
    "Incentive % Mgmt Fees": (incentive_ratio,  True,  0.0),  # can't go below 0
}
for name, (hist, _, _) in drivers.items():
    v = np.array([hist[y] for y in sorted(hist)])
    print(f"{name:24s} {len(v):5d}   {np.median(v):7.2%}   {v.std():7.2%}")
print()
print(f"Fixed: D&A {DA_PCT:.2%} of revenue | capex {CAPEX_PCT:.2%} | "
      f"NWC {NWC_PCT:.2%}")
print(f"Fixed: shareholders keep {INCENTIVE_KEPT:.0%} of incentive fees "
      f"(staff get {payout:.0%})")


# =====================================================================
# PART 5  SIMULATE 10,000 POSSIBLE FUTURES (Monte Carlo)
# =====================================================================
# --- PART 5A  BUSINESS DRIVERS -----------------------------------------
# For each driver, each simulated future works in two layers:
#
# LAYER 1 - PICK A "WORLD" (once per future)
#   1. We only have 5-10 years of history; that is a small sample, so
#      even the "true" long-run average is uncertain.
#   2. To capture that, each future draws its own version of history:
#      pick years from the real history at random, allowing repeats
#      ("bootstrap"). Some versions will contain more good years, some
#      more bad years.
#   3. The median of that version = the level this world drifts towards.
#      Its spread (standard deviation) = how big the yearly surprises are.
#
# LAYER 2 - LIVE IN THAT WORLD FOR 5 YEARS
#   Each year:  next = current + SPEED * (target - current) + surprise
#   1. Start from the latest real value (FY2026).
#   2. Move half of the way (SPEED = 0.5) towards the long-run level.
#      Why? Unusually high or low values tend to fade back to normal
#      ("mean reversion"), but not instantly.
#   3. Add a random surprise, sized by that world's volatility.

def simulate(history, target_override=None, floor=None):
    """Return an array of N_SIMS rows (futures) x YEARS columns (years)."""
    values = np.array([history[y] for y in sorted(history)])
    latest = values[-1]
    paths = np.zeros((N_SIMS, YEARS))
    for sim in range(N_SIMS):
        # layer 1: pick a world
        sample = np.random.choice(values, size=len(values), replace=True) \
                 if BOOTSTRAP else values
        target = target_override if target_override is not None else np.median(sample)
        volatility = sample.std()
        # layer 2: live in it
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

# Show the simulated assumptions year by year.
# Base = the middle outcome. Bear/bull = 5th / 95th percentile
# (only 5% of futures are worse than "bear", 5% better than "bull").
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


# --- Stop here if valuation inputs are missing --------------------------
missing = [k for k, v in {"TAX_RATE": TAX_RATE, "BETA": BETA, "BETA_SE": BETA_SE,
                          "INCENTIVE_EXTRA_RISK": INCENTIVE_EXTRA_RISK,
                          "CASH": CASH, "INVESTMENTS": INVESTMENTS, "DEBT": DEBT,
                          "TRA_LIABILITY": TRA_LIABILITY, "SHARES": SHARES,
                          "CURRENT_PRICE": CURRENT_PRICE}.items() if v is None]
if missing:
    raise SystemExit("\nBusiness drivers simulated. Fill in these PART 3 inputs to "
                     "run the WACC and DCF: " + ", ".join(missing))


# --- PART 5B  WACC AND TERMINAL INPUTS, ONE SET PER WORLD ---------------
# World 1 uses the 1st value of each list below, world 2 the 2nd, etc.
#
# BETA: bell curve (normal distribution) centred on the regression
#   beta, width = its standard error. Why: the regression gives a best
#   guess AND tells us how unsure it is; this spreads the worlds over
#   that uncertainty instead of pretending the beta is exact.
beta_w = np.random.normal(BETA, BETA_SE, N_SIMS)

# ERP: bell curve centred on today's ERP (ERP_CURRENT), with a width
#   equal to how much Damodaran's ERP has varied over the last 10
#   years (standard deviation of ERP_HISTORY, ~0.7 points). Floored at
#   2%. Why: centred on today's market, but allowing the market's mood
#   to shift by as much as it has before.
erp_w = np.maximum(np.random.normal(ERP_CURRENT, np.std(ERP_HISTORY, ddof=1), N_SIMS), 0.02)

# COST OF EQUITY and WACC per world
E = SHARES * CURRENT_PRICE                 # market value of equity, $m
D = DEBT                                   # debt, $m
w_E, w_D = E / (D + E), D / (D + E)
cost_of_equity_w = RISK_FREE + beta_w * erp_w
after_tax_debt   = PRE_TAX_COST_OF_DEBT * (1 - TAX_RATE)
wacc_w = w_E * cost_of_equity_w + w_D * after_tax_debt

# TERMINAL GROWTH: triangular 1.5% / 2.5% / 3.5%, then the safety rule
g_w = np.random.triangular(G_LOW, G_MODE, G_HIGH, size=N_SIMS)
g_w = np.minimum(g_w, wacc_w - 0.01)

# EXIT MULTIPLE: each world picks one value from EXIT_MULTIPLES at random
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


# =====================================================================
# PART 6  TURN EACH FUTURE INTO CASH, AND CASH INTO VALUE
# =====================================================================
# For every future and every year:
#
# STREAM A - STEADY BUSINESS (management fees)
#   1. management fees  = last year's fees x (1 + growth)
#   2. profit           = management fees x management-fee margin
#      (already after salaries, stock pay, offices and D&A)
#   3. after-tax profit = profit x (1 - tax rate)
#   4. cash             = after-tax profit
#                         + D&A     (an accounting cost, not cash leaving)
#                         - capex   (real cash spent on equipment)
#                         - increase in working capital
#
# STREAM B - INCENTIVE FEES
#   1. incentive fees   = management fees x incentive %
#   2. kept by company  = incentive fees x (1 - share paid to staff)
#   3. cash             = kept x (1 - tax rate)
#
# Each stream is discounted at its own rate, using THIS world's WACC:
#   A at WACC;  B at WACC + INCENTIVE_EXTRA_RISK.
#
# TERMINAL VALUE, METHOD 1 (perpetuity growth), per stream:
#   value = next year's cash / (discount rate - terminal growth)
#   For stream A we use the final forecast year's cash.
#   For stream B we use the AVERAGE of the 5 forecast years, because a
#   single year of incentive fees is lumpy: one lucky (or unlucky) year
#   should not be assumed to repeat forever.
#
# TERMINAL VALUE, METHOD 2 (exit multiple):
#   value = 2031 EBITDA x this world's exit multiple, discounted at WACC.
#   EBITDA = stream A profit + D&A (2031) + stream B profit (5-year
#   average, same lumpiness reason as above).
#   Discounted at plain WACC: the multiple is what buyers pay for the
#   whole business, so it already reflects the incentive fees' risk.

g_paths   = sims["Mgmt Fee Growth"]
m_paths   = sims["Mgmt Fee Margin"]
inc_paths = sims["Incentive % Mgmt Fees"]

value_A   = np.zeros(N_SIMS)  # method 1: value today of stream A, per world
value_B   = np.zeros(N_SIMS)  # method 1: value today of stream B, per world
value_ex  = np.zeros(N_SIMS)  # method 2: value today of the whole business
tv_ebitda = np.zeros(N_SIMS)  # 2031 EBITDA used for the exit multiple
tv_perp_2031 = np.zeros(N_SIMS)  # method 1 terminal value, in 2031 dollars

for sim in range(N_SIMS):
    r_A = wacc_w[sim]
    r_B = r_A + INCENTIVE_EXTRA_RISK
    g   = g_w[sim]
    pv_forecast = 0                       # forecast years only, both streams
    mgmt = MGMT_LAST
    prev_rev = TOTAL_REV_LAST
    cash_B_years, kept_B_years = [], []
    for t in range(YEARS):
        discount_A = (1 + r_A) ** (t + 1)
        discount_B = (1 + r_B) ** (t + 1)

        # stream A
        mgmt   = mgmt * (1 + g_paths[sim, t])
        fre    = mgmt * m_paths[sim, t]
        inc    = mgmt * inc_paths[sim, t]
        rev    = mgmt + inc                      # total revenue (for fixed % lines)
        cash_A = (fre * (1 - TAX_RATE)
                  + rev * DA_PCT
                  - rev * CAPEX_PCT
                  - NWC_PCT * (rev - prev_rev))
        prev_rev = rev
        value_A[sim] += cash_A / discount_A
        pv_forecast  += cash_A / discount_A

        # stream B
        cash_B = inc * INCENTIVE_KEPT * (1 - TAX_RATE)
        cash_B_years.append(cash_B)
        kept_B_years.append(inc * INCENTIVE_KEPT)
        value_B[sim] += cash_B / discount_B
        pv_forecast  += cash_B / discount_B

    # METHOD 1: perpetuity growth, per stream
    term_A = cash_A * (1 + g) / (r_A - g)
    term_B = np.mean(cash_B_years) * (1 + g) / (r_B - g)
    value_A[sim] += term_A / (1 + r_A) ** YEARS
    value_B[sim] += term_B / (1 + r_B) ** YEARS
    # (for sanity check 3) stream B's terminal value restated at WACC
    tv_perp_2031[sim] = term_A + term_B * ((1 + r_A) / (1 + r_B)) ** YEARS

    # METHOD 2: exit multiple on 2031 EBITDA
    tv_ebitda[sim] = fre + rev * DA_PCT + np.mean(kept_B_years)
    if mult_w is not None:
        value_ex[sim] = pv_forecast + tv_ebitda[sim] * mult_w[sim] / (1 + r_A) ** YEARS


# =====================================================================
# PART 7  EQUITY BRIDGE: FROM BUSINESS VALUE TO VALUE PER SHARE
# =====================================================================
# 1. Business value  = value of stream A + value of stream B
# 2. + cash and own investments  (things shareholders own on top)
# 3. - debt and TRA liability    (claims that come before shareholders)
# 4. = equity value: what belongs to all owners
# 5. / (Class A shares + insider units) = value per share
# Done for each terminal method, then blended with PERPETUITY_WEIGHT.

bridge = CASH + INVESTMENTS - DEBT - TRA_LIABILITY

business_value = value_A + value_B                    # method 1
prices_perp    = (business_value + bridge) / SHARES

if mult_w is not None:
    prices_exit = (value_ex + bridge) / SHARES        # method 2
    prices = PERPETUITY_WEIGHT * prices_perp + (1 - PERPETUITY_WEIGHT) * prices_exit
else:
    prices_exit = None
    prices = prices_perp


# =====================================================================
# PART 8  RESULTS AND SANITY CHECKS
# =====================================================================
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

# Where does the value come from?
share_A = np.median(value_A) / np.median(business_value)
print()
print("Where the value comes from (median future):")
print(f"  Stream A, management fees:  ${np.median(value_A):8,.0f}m  ({share_A:.0%})")
print(f"  Stream B, incentive fees:   ${np.median(value_B):8,.0f}m  ({1 - share_A:.0%})")

# Sanity check 1: implied multiple vs peers.
#   Asset managers are often priced as a multiple of FRE. If our implied
#   multiple is far from listed peers (e.g. StepStone), find out why.
print()
print("Sanity checks:")
print(f"  Implied business value / FY2026 FRE:  "
      f"{np.median(business_value) / FRE_LAST:5.1f}x  (compare with peers)")

# Sanity check 2: incentive stream vs carry already built up.
#   The $1.5bn of unrealized carry, after staff bonuses and tax, is
#   roughly what the funds ALREADY owe Hamilton Lane. Stream B also
#   counts carry on future investments, so it should usually be
#   ABOVE this number. If it is far below, the incentive assumptions
#   may be too harsh.
carry_net = UNREALIZED_CARRY * INCENTIVE_KEPT * (1 - TAX_RATE)
print(f"  Stream B value: ${np.median(value_B):,.0f}m  vs  unrealized carry "
      f"after staff and tax: ${carry_net:,.0f}m")

# Sanity check 3: do the two terminal methods agree?
#   The perpetuity method implies some EV/EBITDA multiple in 2031.
#   If it is far from the exit multiples you entered, one of the two
#   methods is making a strong assumption: find out which.
implied_mult = np.median(tv_perp_2031 / tv_ebitda)
line = f"  Perpetuity method implies a 2031 EV/EBITDA of {implied_mult:4.1f}x"
if mult_w is not None:
    line += f"  vs median exit multiple {np.median(mult_w):4.1f}x"
print(line)


# =====================================================================
# PART 9  KNOWN SIMPLIFICATIONS (read before presenting)
# =====================================================================
# 1. The management-fee margin assumes every year's incentive fees kept
#    53% after staff pay (the FY2022-2024 median). If the true payout
#    differed in a year, that year's margin is slightly off.
# 2. The drivers are simulated independently. In reality a strong
#    market lifts fee growth AND incentive fees at the same time,
#    so true good and bad scenarios are more extreme than shown here.
# 3. Growth falls from ~14% (forecast) to terminal growth (g) in one step after
#    year 5. A longer forecast or a fading period would be smoother.
# 4. Working capital is set to 0 (see NWC_PCT).
# 5. Stock-based compensation is treated as a real cost (it is inside
#    total expenses) and NOT added back, because new shares given to
#    staff dilute existing shareholders.
# 6. Beta from 2 years of weekly data is noisy (the SE says how
#    noisy). Cross-check it against listed peers (e.g. StepStone,
#    Blackstone, KKR, Partners Group); if HLNE's own beta looks odd,
#    say so and consider a peer average.
# 7. WACC weights use book debt and leave out leases ($78m). Both are
#    small next to equity, so the effect is tiny.
# 8. The simulated WACC inputs are independent of the business
#    drivers. In reality a high-ERP (fearful) market usually also
#    means weaker fundraising and fewer exits.
