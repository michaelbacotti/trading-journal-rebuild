#!/usr/bin/env python3
"""GNRC Dec 18 230/240 Bull Call Spread — P/L curve.

Light theme: white bg, navy/green/red accents. Two horizons:
- Now (Aug 11, 2026, 129 DTE) — entry, both legs at full premium
- At expiry (Dec 18, 2026) — the realized P/L curve (capped structure)

Math:
- Long  $230C basis $24.20 (BSM at σ=57.2%, gap +0.3% with avg IV 57.1%)
- Short $240C basis $20.65 (BSM at σ=56.9%, gap -0.3% with avg IV 57.1%)
- Net debit: $3.55/share = $355/contract
- Strike width: $10
- Max profit: $645/contract (GNRC > $240 at Dec 18, capped)
- Max loss: $355/contract (GNRC < $230 at Dec 18, capped)
- Upper breakeven: $233.55
- Lower breakeven: N/A (capped structure)
- Reward:risk: 1.82:1
- Spot: $214.52 (GNRC live from yfinance)
- IV: ~57% (BSM solve; high IV — single-stock energy/utility name)
- POP (delta-based): ~50% (long ITM needed for profit)

Net delta +0.050/share (+$5/contract per $1 move) — slightly bullish exposure
Net theta: -$0.16/contract/day (slight negative theta — common for long ITM spreads)
Net vega: +$0.33/contract per 1% IV (essentially neutral vega)
"""
import math
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from statistics import NormalDist

OUT = os.path.join(os.path.dirname(__file__), "pl-curve.png")

# Trade constants
LONG_STRIKE = 230.0
SHORT_STRIKE = 240.0
SPOT = 214.52
NET_DEBIT = 3.55  # $/share
WIDTH = SHORT_STRIKE - LONG_STRIKE  # $10
MAX_PROFIT = (WIDTH - NET_DEBIT) * 100  # $645
MAX_LOSS = NET_DEBIT * 100  # $355
UPPER_BE = LONG_STRIKE + NET_DEBIT  # $233.55
IV = 0.571  # average IV solve from basis prices
R = 0.045

ENTRY = "2026-08-11"
EXPIRY = "2026-12-18"
DTE_AT_ENTRY = 129
import datetime as _dt
def _d(s):
    return _dt.date.fromisoformat(s)

T_AT_ENTRY = DTE_AT_ENTRY / 365

def bs_call(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return max(S - K, 0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    return S * NormalDist().cdf(d1) - K * math.exp(-r * T) * NormalDist().cdf(d2)


def calc_pl_at(spot_at_eval, dte_remaining):
    """Calculate net P/L per share at given spot and remaining DTE."""
    if dte_remaining <= 0:
        # At expiry: intrinsic value of each leg minus net debit
        long_intrinsic = max(spot_at_eval - LONG_STRIKE, 0)
        short_intrinsic = max(spot_at_eval - SHORT_STRIKE, 0)
        # We paid debit, bought long, sold short. P/L = long_intrinsic - short_intrinsic - debit
        pl_per_share = (long_intrinsic - short_intrinsic) - NET_DEBIT
    else:
        # Pre-expiry: BSM value of each leg minus net debit
        long_value = bs_call(spot_at_eval, LONG_STRIKE, dte_remaining / 365, R, IV)
        short_value = bs_call(spot_at_eval, SHORT_STRIKE, dte_remaining / 365, R, IV)
        pl_per_share = (long_value - short_value) - NET_DEBIT
    return pl_per_share


# Spot range
spots = np.linspace(LONG_STRIKE - 80, SHORT_STRIKE + 80, 400)

# Two horizons
pl_now = np.array([calc_pl_at(s, DTE_AT_ENTRY) for s in spots]) * 100
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
ax.plot(spots, pl_at_exp, color="#2e7d32", linewidth=2.4, linestyle=":",
        label=f"At expiry ({EXPIRY}) — capped structure", zorder=4)

# Zero line
ax.axhline(0, color="#666666", linewidth=0.8, zorder=2)

# Long strike line
ax.axvline(LONG_STRIKE, color="#1f7a1f", linewidth=1.2, linestyle="-", alpha=0.7, zorder=2)
ax.text(LONG_STRIKE, ax.get_ylim()[1] * 0.95 if ax.get_ylim()[1] > 0 else 50,
        f"  Long strike $230", color="#1f7a1f", fontsize=9, ha="left", va="top", fontweight="bold")

# Short strike line
ax.axvline(SHORT_STRIKE, color="#aa5500", linewidth=1.0, linestyle="--", alpha=0.7, zorder=2)
ax.text(SHORT_STRIKE, ax.get_ylim()[1] * 0.92 if ax.get_ylim()[1] > 0 else 50,
        f"  Short strike $240", color="#aa5500", fontsize=9, ha="left", va="top")

# Upper breakeven
ax.axvline(UPPER_BE, color="#888888", linewidth=0.8, linestyle=":", alpha=0.6, zorder=2)
ax.text(UPPER_BE, ax.get_ylim()[1] * 0.05 if ax.get_ylim()[1] > 0 else -50,
        f"  BE ${UPPER_BE:.2f}", color="#555555", fontsize=8, ha="left", va="top")

# Spot line
ax.axvline(SPOT, color="#cc3333", linewidth=1.2, linestyle="-", alpha=0.85, zorder=3)
ax.text(SPOT, ax.get_ylim()[1] * 0.78 if ax.get_ylim()[1] > 0 else 50,
        f"  GNRC @ ${SPOT:.2f}",
        color="#cc3333", fontsize=9, ha="left", va="top", fontweight="bold")

# Max profit annotation (above $240)
ax.hlines(MAX_PROFIT, SHORT_STRIKE, SHORT_STRIKE + 80, color="#2e7d32", linewidth=0.8,
          linestyle=":", alpha=0.6, zorder=2)
ax.text(SHORT_STRIKE + 1, MAX_PROFIT + 12, f"Max profit ${MAX_PROFIT:.0f}",
        color="#2e7d32", fontsize=9, fontweight="bold")

# Max loss annotation (below $230)
ax.hlines(-MAX_LOSS, LONG_STRIKE - 80, LONG_STRIKE, color="#a02020", linewidth=0.8,
          linestyle=":", alpha=0.6, zorder=2)
ax.text(LONG_STRIKE - 79, -MAX_LOSS - 18, f"Max loss -${MAX_LOSS:.0f}",
        color="#a02020", fontsize=9, fontweight="bold")

# Labels
ax.set_xlabel("GNRC price at evaluation", fontsize=11, fontweight="500")
ax.set_ylabel("P/L per contract ($)", fontsize=11, fontweight="500")
ax.set_title(
    "GNRC Dec 18 230/240 Bull Call Spread — capped P/L profile at entry and expiry",
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
ax.set_xlim(LONG_STRIKE - 80, SHORT_STRIKE + 80)

# Stats box
delta_long = NormalDist().cdf((math.log(SPOT/LONG_STRIKE) + (R + 0.5*IV**2)*T_AT_ENTRY) / (IV * math.sqrt(T_AT_ENTRY)))
delta_short = NormalDist().cdf((math.log(SPOT/SHORT_STRIKE) + (R + 0.5*IV**2)*T_AT_ENTRY) / (IV * math.sqrt(T_AT_ENTRY)))
pop_itm_long = delta_long  # P(expires ITM with long strike below spot)
pop_profit = (delta_long - delta_short) if SPOT > UPPER_BE else None
# Simpler: probability structure finishes ITM and profitable at expiry
# P(S > $233.55) ≈ 1 - Φ(d2)
d2_breakeven = (math.log(SPOT/UPPER_BE) + (R - 0.5*IV**2)*T_AT_ENTRY) / (IV * math.sqrt(T_AT_ENTRY))
prob_profit = 1 - NormalDist().cdf(d2_breakeven)

stats_text = (
    f"Spot ${SPOT:.2f}\n"
    f"Net debit ${NET_DEBIT:.2f}/sh (${NET_DEBIT*100:.0f}/contract)\n"
    f"Max profit ${MAX_PROFIT:.0f} (GNRC > $240)\n"
    f"Max loss -${MAX_LOSS:.0f} (GNRC < $230)\n"
    f"Upper BE ${UPPER_BE:.2f}\n"
    f"Reward:risk {(WIDTH-NET_DEBIT)/NET_DEBIT:.2f}:1\n"
    f"P(profit) ~{prob_profit*100:.0f}% (BSM)\n"
    f"DTE {DTE_AT_ENTRY}, VIX 15.45\n"
    f"Implied IV ~{IV*100:.1f}%"
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
print(f"Max profit (capped): ${MAX_PROFIT:.0f}/contract")
print(f"Max loss (capped): -${MAX_LOSS:.0f}/contract")
print(f"P(profit) BSM ~{prob_profit*100:.0f}%")
