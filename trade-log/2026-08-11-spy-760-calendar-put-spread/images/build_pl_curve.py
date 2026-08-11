#!/usr/bin/env python3
"""SPY Oct 16 / Oct 30 760 Calendar Put Spread — P/L curve.

Light theme: white bg, navy/green/red accents. Three horizons:
- Now (Aug 11, 2026, 66 DTE short) — entry, both legs at full premium, near-flat tent
- Mid (~36 DTE before short expiry = Sep 30, 2026) — front-month accelerating
- At short expiry (Oct 16, 2026) — peak tent at $760 strike

Math:
- Short $760P Oct 16 basis $12.775 (BSM short $12.910, gap -1.0%)
- Long  $760P Oct 30 basis $14.770 (BSM long  $14.385, gap +2.7%)
- Net debit (basis): $1.995/share = $199.50/contract
- Strike: $760 (same both legs — same-strike put calendar)
- Calendar duration: 14 days (Oct 16 → Oct 30)
- Estimated max profit: $237.93/contract (BSM at 16% IV: long residual at $760
  with 14 DTE = $4.374/share; max profit = ($4.374 − $1.995) × 100)
- Max loss: $199.50/contract (= debit)
- Reward:risk: 1.19:1
- Spot $771.91 — strike $760 sits $11.91 below spot (1.54% OTM put)
- VIX 15.27 (SPY IV proxy ~16%)

Net delta ~-0.002/share (essentially neutral — both legs same strike).
Net theta: +$1.36/contract/day (positive theta harvest).
Net vega: +$12.57/contract per 1% IV (long vega).
"""
import math
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from statistics import NormalDist

OUT = os.path.join(os.path.dirname(__file__), "pl-curve.png")

# Trade constants
STRIKE = 760.0
SPOT = 771.91
DEBIT = 1.995  # $1.995/share net debit (basis)
MAX_LOSS = DEBIT * 100  # $199.50/contract
SHORT_BASIS = 12.775
LONG_BASIS = 14.77
IV = 0.16  # SPY IV ~16%
R = 0.045  # risk-free rate

# Expiries
ENTRY = "2026-08-11"
SHORT_EXP = "2026-10-16"  # 66 DTE at entry
LONG_EXP = "2026-10-30"   # 80 DTE at entry
MID_DATE = "2026-09-30"    # 30 days before short expiry
import datetime as _dt
def _d(s):
    return _dt.date.fromisoformat(s)

DTE_SHORT_AT_ENTRY = (_d(SHORT_EXP) - _d(ENTRY)).days  # 66
DTE_LONG_AT_ENTRY = (_d(LONG_EXP) - _d(ENTRY)).days    # 80
DTE_SHORT_AT_MID = (_d(SHORT_EXP) - _d(MID_DATE)).days  # 16
DTE_LONG_AT_MID = (_d(LONG_EXP) - _d(MID_DATE)).days    # 30
DAYS_AFTER_SHORT_EXP = (_d(LONG_EXP) - _d(SHORT_EXP)).days  # 14
DTE_LONG_AT_SHORT_EXP = DAYS_AFTER_SHORT_EXP  # 14 DTE remaining on long

def bs_put(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return max(K - S, 0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return K * math.exp(-r * T) * NormalDist().cdf(-d2) - S * NormalDist().cdf(-d1)


def calc_pl_at(spot_at_eval, dte_short, dte_long):
    """Calculate net P/L per share at given spot and remaining DTEs."""
    # Short leg value at eval: if dte_short <= 0, intrinsic; else BSM
    if dte_short <= 0:
        # Short expires — worth intrinsic if ITM (we sold it; we owe max(K-S,0))
        short_value_per_share = max(STRIKE - spot_at_eval, 0)
    else:
        short_value_per_share = bs_put(spot_at_eval, STRIKE, dte_short / 365, R, IV)

    # Long leg value at eval
    if dte_long <= 0:
        long_value_per_share = max(STRIKE - spot_at_eval, 0)
    else:
        long_value_per_share = bs_put(spot_at_eval, STRIKE, dte_long / 365, R, IV)

    # Net P/L: we paid DEBIT, sold short, bought long
    # P/L = (short_value - long_value) - DEBIT... wait
    # We SOLD short (received SHORT_BASIS), BOUGHT long (paid LONG_BASIS)
    # Net cost at entry: LONG_BASIS - SHORT_BASIS = DEBIT
    # Current value of position: long_value - short_value (we still own long, owe short)
    # P/L = (long_value - short_value) - DEBIT
    pl_per_share = (long_value_per_share - short_value_per_share) - DEBIT
    return pl_per_share


# Spot range
spots = np.linspace(STRIKE - 100, STRIKE + 100, 400)

# Three horizons
pl_now = np.array([calc_pl_at(s, DTE_SHORT_AT_ENTRY, DTE_LONG_AT_ENTRY) for s in spots]) * 100
pl_mid = np.array([calc_pl_at(s, DTE_SHORT_AT_MID, DTE_LONG_AT_MID) for s in spots]) * 100
pl_at_short_exp = np.array([calc_pl_at(s, 0, DTE_LONG_AT_SHORT_EXP) for s in spots]) * 100

# Max profit estimate at strike
max_profit_at_strike = calc_pl_at(STRIKE, 0, DTE_LONG_AT_SHORT_EXP) * 100
print(f"Max profit estimate: ${max_profit_at_strike:.2f}")

# Plot
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Arial", "DejaVu Sans"],
    "axes.edgecolor": "#222222",
    "axes.labelcolor": "#222222",
    "axes.titlecolor": "#222222",
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

fig, ax = plt.subplots(figsize=(11, 6.5), dpi=110)
fig.patch.set_facecolor("#ffffff")
ax.set_facecolor("#ffffff")

# Filled regions
ax.fill_between(spots, pl_now, 0, where=(pl_now > 0), color="#d8f0d8", alpha=0.55, zorder=1)
ax.fill_between(spots, pl_now, 0, where=(pl_now < 0), color="#f7d8d8", alpha=0.55, zorder=1)
ax.fill_between(spots, pl_at_short_exp, 0, where=(pl_at_short_exp > 0), color="#d8f0d8", alpha=0.85, zorder=1)
ax.fill_between(spots, pl_at_short_exp, 0, where=(pl_at_short_exp < 0), color="#f7d8d8", alpha=0.85, zorder=1)

# Curves
ax.plot(spots, pl_now, color="#1f4e79", linewidth=2.0, label=f"Now ({ENTRY}, {DTE_SHORT_AT_ENTRY} DTE short)", zorder=3)
ax.plot(spots, pl_mid, color="#e07b00", linewidth=2.0, linestyle="--",
        label=f"Mid-life ({MID_DATE}, {DTE_SHORT_AT_MID} DTE short)", zorder=3)
ax.plot(spots, pl_at_short_exp, color="#2e7d32", linewidth=2.4, linestyle=":",
        label=f"At short expiry ({SHORT_EXP}, {DTE_LONG_AT_SHORT_EXP} DTE on long)", zorder=4)

# Zero line
ax.axhline(0, color="#666666", linewidth=0.8, zorder=2)

# Strike line
ax.axvline(STRIKE, color="#888888", linewidth=1.0, linestyle=":", alpha=0.8, zorder=2)
ax.text(STRIKE, ax.get_ylim()[1] * 0.95, f"  $760 strike",
        color="#555555", fontsize=9, ha="left", va="top")

# Spot line
ax.axvline(SPOT, color="#cc3333", linewidth=1.2, linestyle="-", alpha=0.85, zorder=3)
ax.text(SPOT, ax.get_ylim()[1] * 0.78, f"  SPY @ ${SPOT:.2f}",
        color="#cc3333", fontsize=9, ha="left", va="top", fontweight="bold")

# Max profit annotation
ax.scatter([STRIKE], [max_profit_at_strike], s=70, color="#2e7d32", zorder=5,
           edgecolor="#ffffff", linewidth=1.4)
ax.annotate(f"Max profit\n~${max_profit_at_strike:.0f}",
            xy=(STRIKE, max_profit_at_strike),
            xytext=(STRIKE + 18, max_profit_at_strike + 60),
            fontsize=9, color="#2e7d32", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#2e7d32", lw=1.0))

# Max loss annotation
ax.scatter([STRIKE - 100], [MAX_LOSS * -1], s=40, color="#a02020", alpha=0.0)  # placeholder

# Labels
ax.set_xlabel("SPY price at evaluation", fontsize=11, fontweight="500")
ax.set_ylabel("P/L per contract ($)", fontsize=11, fontweight="500")
ax.set_title(
    "SPY Oct 16 / Oct 30 760 Calendar Put Spread — P/L at three horizons",
    fontsize=12, fontweight="bold", pad=12, loc="left"
)

# Legend
legend = ax.legend(loc="upper left", fontsize=9.5, frameon=True, framealpha=0.95,
                   edgecolor="#dddddd")
legend.get_frame().set_facecolor("#ffffff")

# Grid
ax.grid(True, color="#e6e6e6", linewidth=0.6, alpha=0.7, zorder=0)
ax.set_axisbelow(True)

# Axis limits
ax.set_xlim(STRIKE - 100, STRIKE + 100)

# Stats box
stats_text = (
    f"Spot ${SPOT:.2f}\n"
    f"Strike $760 (same both legs)\n"
    f"Net debit ${DEBIT:.3f}/sh (${MAX_LOSS:.2f}/contract)\n"
    f"Max profit ~${max_profit_at_strike:.0f}/contract\n"
    f"Max loss ${MAX_LOSS:.2f}/contract (= debit)\n"
    f"Reward:risk {max_profit_at_strike/MAX_LOSS:.2f}:1\n"
    f"DTE short {DTE_SHORT_AT_ENTRY}, long {DTE_LONG_AT_ENTRY}\n"
    f"Calendar span {DAYS_AFTER_SHORT_EXP} days\n"
    f"VIX (IV proxy) 15.27"
)
ax.text(
    0.985, 0.04, stats_text,
    transform=ax.transAxes,
    fontsize=8.8, color="#222222",
    verticalalignment="bottom", horizontalalignment="right",
    bbox=dict(boxstyle="round,pad=0.55", facecolor="#fafafa", edgecolor="#cccccc", linewidth=0.8),
    family="monospace",
)

plt.tight_layout()
plt.savefig(OUT, dpi=130, bbox_inches="tight", facecolor="#ffffff")
print(f"Wrote {OUT}")
print(f"Max profit at strike (BSM): ${max_profit_at_strike:.2f}/contract")