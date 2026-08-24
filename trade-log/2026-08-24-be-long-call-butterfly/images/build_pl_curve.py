#!/usr/bin/env python3
"""BE Jan 15 '27 260/280/300 Long Call Butterfly — P/L curve.

Light theme: white bg, navy/green/red accents. Three horizons:
- Now (Aug 24, 2026, 144 DTE) — entry, all legs at full premium
- Mid-life (~72 DTE) — after half the time decay
- At expiry (Jan 15, 2027) — the realized P/L curve (single peak at $280)

Math (OptionStrat basis cross-checked at 0.0% vs live yfinance chain, all 3 legs):
- Long 260C basis $30.575 (280C x2 short $26.30, 300C long $22.65)
- Net debit: $0.625/share = $62.50/contract
- Strike widths: $20 lower (260->280), $20 upper (280->300)
- Max profit: $1,937.50/contract (at BE = $280 at expiry)
- Max loss: $62.50/contract (= net debit)
- Lower breakeven: $260.625
- Upper breakeven: $299.375
- Reward:risk: 31:1 (lottery-ticket shape — 144-DTE wings carry time value)
- Spot: $204.02 (BE live from yfinance)
- 30-day HV: 40.34% (annualized, log-returns)
- IV: 94.4-94.9% across strikes (flat — reflects BE's jump-risk pricing)
- PoP (drift-implied, BE > $260.625): 15.3%
- PoP (max-profit zone, $260.625-$299.375): 9.6%

Net delta (HV-based): +0.024/share (near delta-neutral)
Net theta: ~$0.20/contract/day at IV-based BSM theta (near zero)
Net vega: ~-$0.61/contract per 1% IV change (mildly negative)
"""
import math
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from statistics import NormalDist

OUT = os.path.join(os.path.dirname(__file__), "pl-curve.png")

# Trade constants
LONG_LOW = 260.0
SHORT_MID = 280.0
LONG_HIGH = 300.0
SPOT = 204.02
NET_DEBIT_PER_SHARE = 0.625
NET_DEBIT_PER_CONTRACT = NET_DEBIT_PER_SHARE * 100
WIDTH = SHORT_MID - LONG_LOW  # $20
MAX_PROFIT_PER_CONTRACT = WIDTH * 100 - NET_DEBIT_PER_CONTRACT  # $1,937.50
MAX_LOSS_PER_CONTRACT = NET_DEBIT_PER_CONTRACT  # $62.50
LOWER_BE = LONG_LOW + NET_DEBIT_PER_SHARE  # $260.625
UPPER_BE = LONG_HIGH - NET_DEBIT_PER_SHARE  # $299.375
IV = 0.947  # avg of 94.4-94.9% chain IV across strikes
R = 0.045
SIGMA_HV = 0.4034  # 30-day HV (annualized) for drift-implied PoP estimate

ENTRY = "2026-08-24"
EXPIRY = "2027-01-15"
DTE_AT_ENTRY = 144
import datetime as _dt

T_AT_ENTRY = DTE_AT_ENTRY / 365
T_MID = (DTE_AT_ENTRY - 72) / 365  # ~72 DTE remaining at mid-life


def bs_call(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return max(S - K, 0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * NormalDist().cdf(d1) - K * math.exp(-r * T) * NormalDist().cdf(d2)


def long_call_butterfly_value(s, T_remaining):
    """Mark-to-market value of a long call butterfly at spot s with T_remaining years left."""
    if T_remaining <= 0:
        # At expiry: intrinsic of each leg
        long_low_val = max(s - LONG_LOW, 0)
        short_mid_val = max(s - SHORT_MID, 0)
        long_high_val = max(s - LONG_HIGH, 0)
        # Long +1, Short -2, Long +1
        return long_low_val - 2 * short_mid_val + long_high_val
    # Pre-expiry: BSM value of each leg
    long_low_val = bs_call(s, LONG_LOW, T_remaining, R, IV)
    short_mid_val = bs_call(s, SHORT_MID, T_remaining, R, IV)
    long_high_val = bs_call(s, LONG_HIGH, T_remaining, R, IV)
    return long_low_val - 2 * short_mid_val + long_high_val


def calc_pl_at(spot_at_eval, dte_remaining):
    """Calculate net P/L per share at given spot and remaining DTE."""
    # Current value of the structure (long butterfly)
    val = long_call_butterfly_value(spot_at_eval, dte_remaining / 365)
    # Net P/L = current value - net debit paid
    return val - NET_DEBIT_PER_SHARE


# Spot range — wide enough to show both wings + max loss plateaus
spots = np.linspace(LONG_LOW - 100, LONG_HIGH + 100, 400)

# Three horizons
pl_now = np.array([calc_pl_at(s, DTE_AT_ENTRY) for s in spots]) * 100
pl_mid = np.array([calc_pl_at(s, DTE_AT_ENTRY - 72) for s in spots]) * 100
pl_at_exp = np.array([calc_pl_at(s, 0) for s in spots]) * 100

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

# Filled regions (at-expiry)
ax.fill_between(spots, pl_at_exp, 0, where=(pl_at_exp > 0), color="#d8f0d8", alpha=0.85, zorder=1)
ax.fill_between(spots, pl_at_exp, 0, where=(pl_at_exp < 0), color="#f7d8d8", alpha=0.85, zorder=1)

# Curves
ax.plot(spots, pl_now, color="#1f4e79", linewidth=2.0,
        label=f"Now ({ENTRY}, {DTE_AT_ENTRY} DTE)", zorder=3)
ax.plot(spots, pl_mid, color="#6666aa", linewidth=2.0, linestyle="--",
        label=f"Mid-life (~72 DTE remaining)", zorder=3)
ax.plot(spots, pl_at_exp, color="#aa8800", linewidth=2.4, linestyle=":",
        label=f"At expiry ({EXPIRY}) — single peak at $280", zorder=4)

# Zero line
ax.axhline(0, color="#666666", linewidth=0.8, zorder=2)

# Strike lines
ax.axvline(LONG_LOW, color="#aa5500", linewidth=1.0, linestyle="--", alpha=0.7, zorder=2)
ax.text(LONG_LOW, ax.get_ylim()[1] * 0.92, f"  Long low $260",
        color="#aa5500", fontsize=9, ha="left", va="top")
ax.axvline(SHORT_MID, color="#cc3333", linewidth=1.4, linestyle="-", alpha=0.85, zorder=3)
ax.text(SHORT_MID, ax.get_ylim()[1] * 0.97, f"  Short mid (×2) $280",
        color="#cc3333", fontsize=9.5, ha="left", va="top", fontweight="bold")
ax.axvline(LONG_HIGH, color="#aa5500", linewidth=1.0, linestyle="--", alpha=0.7, zorder=2)
ax.text(LONG_HIGH, ax.get_ylim()[1] * 0.92, f"  Long high $300",
        color="#aa5500", fontsize=9, ha="right", va="top")

# Breakeven lines
ax.axvline(LOWER_BE, color="#888888", linewidth=0.7, linestyle=":", alpha=0.6, zorder=2)
ax.text(LOWER_BE, ax.get_ylim()[1] * 0.05, f"  Lower BE ${LOWER_BE:.2f}",
        color="#555555", fontsize=8, ha="left", va="bottom")
ax.axvline(UPPER_BE, color="#888888", linewidth=0.7, linestyle=":", alpha=0.6, zorder=2)
ax.text(UPPER_BE, ax.get_ylim()[1] * 0.05, f"  Upper BE ${UPPER_BE:.2f}",
        color="#555555", fontsize=8, ha="right", va="bottom")

# Spot line
ax.axvline(SPOT, color="#cc3333", linewidth=1.2, linestyle="-", alpha=0.85, zorder=3)
ax.text(SPOT, ax.get_ylim()[1] * 0.78, f"  BE @ ${SPOT:.2f}",
        color="#cc3333", fontsize=9, ha="left", va="top", fontweight="bold")

# Max profit annotation (gold)
ax.hlines(MAX_PROFIT_PER_CONTRACT, SHORT_MID, SHORT_MID, color="#aa8800", linewidth=0.8,
          linestyle=":", alpha=0.7, zorder=2)
ax.text(SHORT_MID + 0.5, MAX_PROFIT_PER_CONTRACT - 80, f"Max profit +${MAX_PROFIT_PER_CONTRACT:.2f}",
        color="#aa8800", fontsize=10, fontweight="bold", ha="left")

# Max loss annotation (red)
ax.hlines(-MAX_LOSS_PER_CONTRACT, LONG_LOW - 100, LONG_LOW, color="#a02020", linewidth=0.8,
          linestyle=":", alpha=0.6, zorder=2)
ax.text(LONG_LOW - 95, -MAX_LOSS_PER_CONTRACT + 8, f"Max loss -${MAX_LOSS_PER_CONTRACT:.2f}",
        color="#a02020", fontsize=9, fontweight="bold")

# Labels
ax.set_xlabel("BE price at evaluation", fontsize=11, fontweight="500")
ax.set_ylabel("P/L per contract ($)", fontsize=11, fontweight="500")
ax.set_title(
    "BE Jan 15 2027 260/280/300 Long Call Butterfly — lottery-ticket P/L profile at entry, mid-life, and expiry",
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
ax.set_xlim(LONG_LOW - 100, LONG_HIGH + 100)
ax.set_ylim(top=MAX_PROFIT_PER_CONTRACT * 1.1)

# Stats box
pop_lower = NormalDist().cdf((math.log(SPOT/LOWER_BE) + (R - 0.5*SIGMA_HV**2)*T_AT_ENTRY) / (SIGMA_HV*math.sqrt(T_AT_ENTRY)))
pop_upper = NormalDist().cdf((math.log(SPOT/UPPER_BE) + (R - 0.5*SIGMA_HV**2)*T_AT_ENTRY) / (SIGMA_HV*math.sqrt(T_AT_ENTRY)))

stats_text = (
    f"Spot ${SPOT:.2f} (BE live from yfinance)\n"
    f"Net debit ${NET_DEBIT_PER_SHARE:.3f}/sh (${NET_DEBIT_PER_CONTRACT:.2f}/contract)\n"
    f"Max profit +${MAX_PROFIT_PER_CONTRACT:.2f}/contract (at $280)\n"
    f"Max loss -${MAX_LOSS_PER_CONTRACT:.2f}/contract (below $260.62 or above $299.38)\n"
    f"Lower BE ${LOWER_BE:.3f} · Upper BE ${UPPER_BE:.3f}\n"
    f"Reward:risk {MAX_PROFIT_PER_CONTRACT/MAX_LOSS_PER_CONTRACT:.0f}:1 (lottery-ticket)\n"
    f"PoP (any profit, drift-implied): {pop_lower*100:.1f}%\n"
    f"PoP (max-profit zone): {pop_upper*100:.1f}%\n"
    f"DTE {DTE_AT_ENTRY}, IV ~{IV*100:.1f}% (chain), HV {SIGMA_HV*100:.1f}% (30d ann.)"
)
ax.text(
    0.985, 0.04, stats_text,
    transform=ax.transAxes,
    fontsize=8.5, color="#222222",
    verticalalignment="bottom", horizontalalignment="right",
    bbox=dict(boxstyle="round,pad=0.55", facecolor="#fafafa", edgecolor="#cccccc", linewidth=0.8),
    family="monospace",
)

plt.tight_layout()
plt.savefig(OUT, dpi=130, bbox_inches="tight", facecolor="#ffffff")
print(f"Wrote {OUT}")
print(f"Max profit (at $280): +${MAX_PROFIT_PER_CONTRACT:.2f}/contract")
print(f"Max loss (defined): -${MAX_LOSS_PER_CONTRACT:.2f}/contract")
print(f"PoP (any profit, drift-implied, HV-based): {pop_lower*100:.1f}%")
print(f"PoP (max-profit zone): {pop_upper*100:.1f}%")
