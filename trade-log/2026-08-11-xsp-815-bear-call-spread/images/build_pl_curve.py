#!/usr/bin/env python3
"""XSP Oct 16 815/820 Bear Call Spread — P/L curve.

Light theme: white bg, navy/green/red accents. Two horizons:
- Now (Aug 11, 2026, 66 DTE) — entry, both legs at full premium
- At expiry (Oct 16, 2026) — the realized P/L curve (capped structure)

Math:
- Short $815C basis $4.17 (BSM at σ=12.08%, gap 0.0%)
- Long  $820C basis $3.265 (BSM at σ=12.08%, gap -2.5%)
- Net credit: $0.905/share = $90.50/contract
- Strike width: $5.00
- Max profit: $90.50 (both legs expire worthless, keep full credit)
- Max loss: $409.50 (XSP > $820 at expiry)
- Upper breakeven: $815.905
- Lower breakeven: N/A (capped structure, profit flattens below $815)
- Reward:risk: 0.22:1 (capped structure by design)
- Spot: $770.53 (XSP ≈ SPY; SPY live from yfinance $770.53)
- VIX: 15.47
- POP (delta-based): ~80%

Net delta -0.031/share (slight short delta — sold higher strike, less delta)
Net theta: +$1.15/contract/day (positive theta harvest — typical short premium)
Net vega: -$9.39/contract per 1% IV (short vega — benefits from IV drop)
"""
import math
import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from statistics import NormalDist

OUT = os.path.join(os.path.dirname(__file__), "pl-curve.png")

# Trade constants
SHORT_STRIKE = 815.0
LONG_STRIKE = 820.0
SPOT = 770.53
NET_CREDIT = 0.905  # $/share
WIDTH = LONG_STRIKE - SHORT_STRIKE  # $5
MAX_PROFIT = NET_CREDIT * 100  # $90.50
MAX_LOSS = (WIDTH - NET_CREDIT) * 100  # $409.50
UPPER_BE = SHORT_STRIKE + NET_CREDIT  # $815.905
IV = 0.1208  # implied IV from BSM solve
R = 0.045

ENTRY = "2026-08-11"
EXPIRY = "2026-10-16"
DTE_AT_ENTRY = 66
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
        # At expiry: short leg intrinsic (we owe), long leg intrinsic (we own)
        short_intrinsic = max(spot_at_eval - SHORT_STRIKE, 0)  # what short is worth
        long_intrinsic = max(spot_at_eval - LONG_STRIKE, 0)
        # We sold short (received), bought long (paid). P/L = credit received - short payout + long value - long cost
        # Simpler: long value - short value, then add credit (received at entry)
        pl_per_share = (long_intrinsic - short_intrinsic) + NET_CREDIT
    else:
        # Pre-expiry: BSM value of each leg minus net debit
        # P/L = (long_value - short_value) + credit_received
        long_value = bs_call(spot_at_eval, LONG_STRIKE, dte_remaining / 365, R, IV)
        short_value = bs_call(spot_at_eval, SHORT_STRIKE, dte_remaining / 365, R, IV)
        pl_per_share = (long_value - short_value) + NET_CREDIT
    return pl_per_share


# Spot range
spots = np.linspace(SHORT_STRIKE - 80, LONG_STRIKE + 80, 400)

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

# Short strike line
ax.axvline(SHORT_STRIKE, color="#cc3333", linewidth=1.2, linestyle="-", alpha=0.7, zorder=2)
ax.text(SHORT_STRIKE, ax.get_ylim()[1] * 0.95, f"  Short strike $815",
        color="#cc3333", fontsize=9, ha="left", va="top", fontweight="bold")

# Long strike line
ax.axvline(LONG_STRIKE, color="#aa5500", linewidth=1.0, linestyle="--", alpha=0.7, zorder=2)
ax.text(LONG_STRIKE, ax.get_ylim()[1] * 0.92, f"  Long strike $820",
        color="#aa5500", fontsize=9, ha="left", va="top")

# Upper breakeven
ax.axvline(UPPER_BE, color="#888888", linewidth=0.8, linestyle=":", alpha=0.6, zorder=2)
ax.text(UPPER_BE, ax.get_ylim()[1] * 0.05 if ax.get_ylim()[1] > 0 else -30,
        f"  BE ${UPPER_BE:.2f}", color="#555555", fontsize=8, ha="left", va="top")

# Spot line
ax.axvline(SPOT, color="#cc3333", linewidth=1.2, linestyle="-", alpha=0.85, zorder=3)
ax.text(SPOT, ax.get_ylim()[1] * 0.78 if ax.get_ylim()[1] > 0 else 0,
        f"  XSP @ ${SPOT:.2f}",
        color="#cc3333", fontsize=9, ha="left", va="top", fontweight="bold")

# Max profit annotation (at left side, below $815)
ax.hlines(MAX_PROFIT, SHORT_STRIKE - 80, SHORT_STRIKE, color="#2e7d32", linewidth=0.8,
          linestyle=":", alpha=0.6, zorder=2)
ax.text(SHORT_STRIKE - 75, MAX_PROFIT + 8, f"Max profit ${MAX_PROFIT:.2f}",
        color="#2e7d32", fontsize=9, fontweight="bold")

# Max loss annotation (above $820)
ax.hlines(-MAX_LOSS, LONG_STRIKE, LONG_STRIKE + 80, color="#a02020", linewidth=0.8,
          linestyle=":", alpha=0.6, zorder=2)
ax.text(LONG_STRIKE + 1, -MAX_LOSS - 12, f"Max loss -${MAX_LOSS:.2f}",
        color="#a02020", fontsize=9, fontweight="bold")

# Labels
ax.set_xlabel("XSP price at evaluation", fontsize=11, fontweight="500")
ax.set_ylabel("P/L per contract ($)", fontsize=11, fontweight="500")
ax.set_title(
    "XSP Oct 16 815/820 Bear Call Spread — capped P/L profile at entry and expiry",
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
ax.set_xlim(SHORT_STRIKE - 80, LONG_STRIKE + 80)

# Stats box
delta_short = NormalDist().cdf((math.log(SPOT/SHORT_STRIKE) + (R + 0.5*IV**2)*T_AT_ENTRY) / (IV * math.sqrt(T_AT_ENTRY)))
pop = 1 - delta_short

stats_text = (
    f"Spot ${SPOT:.2f} (XSP ≈ SPY)\n"
    f"Net credit ${NET_CREDIT:.3f}/sh (${MAX_PROFIT:.2f}/contract)\n"
    f"Max loss -${MAX_LOSS:.2f}/contract (above $820)\n"
    f"Upper BE ${UPPER_BE:.3f}\n"
    f"Reward:risk {NET_CREDIT/(WIDTH-NET_CREDIT):.2f}:1 (capped)\n"
    f"POP (delta-based) ~{pop*100:.0f}%\n"
    f"DTE {DTE_AT_ENTRY}, VIX {15.47:.2f}\n"
    f"Implied IV (solve) {IV*100:.2f}%"
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
print(f"Max profit (capped): ${MAX_PROFIT:.2f}/contract")
print(f"Max loss (capped): -${MAX_LOSS:.2f}/contract")
print(f"POP (delta): ~{pop*100:.0f}%")
