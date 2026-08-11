#!/usr/bin/env python3
"""META Oct 16 '26 605/610 Bull Call Spread — P/L curve.

Light theme: white bg, navy/green/red accents. Two horizons:
- Now (Aug 10, 2026, 67 DTE) — entry, both legs at full premium, near-flat MTM
- At expiry (Oct 16, 2026) — realized P/L curve

Math:
- Long $605C paid $33.70 mid (basis $34.175, 1.41% gap)
- Short $610C received $31.60 mid (basis $32.00, 1.24% gap)
- Net debit (live mid): $2.10/share = $210.00/contract
- Net debit (basis): $2.175/share = $217.50/contract
- Strike width: $5.00
- Max profit (live): ($5 - $2.10) × 100 = $290/contract
- Max profit (basis): $282.50/contract
- Max loss: $210/contract
- Lower breakeven (live): $607.10
- Spot: $593.47

Both calls are deep OTM at entry (long +1.94%, short +2.79%).
"""
import math
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(__file__), "pl-curve.png")

# Trade constants
LONG_STRIKE = 605.0
SHORT_STRIKE = 610.0
SPOT = 593.47
DEBIT = 2.10  # live mid basis ($/share)
WIDTH = SHORT_STRIKE - LONG_STRIKE  # $5
MAX_PROFIT = (WIDTH - DEBIT) * 100  # $290
MAX_LOSS = DEBIT * 100  # $210
LOWER_BE = LONG_STRIKE + DEBIT  # $607.10
IV = 0.38  # ~38% (live chain)

DTE_ENTRY = 67  # Oct 16 - Aug 10
T = DTE_ENTRY / 365
R = 0.045

def bs_call(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0:
        return max(S - K, 0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    N1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))
    N2 = 0.5 * (1 + math.erf(d2 / math.sqrt(2)))
    return S * N1 - K * math.exp(-r * T) * N2

# Build price grid
META_MIN = 580.0
META_MAX = 625.0
prices = np.linspace(META_MIN, META_MAX, 401)

# Today curve: long_call - short_call - debit (per share, scaled to contract)
def value_today(meta_price):
    long_val = bs_call(meta_price, LONG_STRIKE, T, R, IV)
    short_val = bs_call(meta_price, SHORT_STRIKE, T, R, IV)
    return (long_val - short_val - DEBIT) * 100

today_pl = np.array([value_today(p) for p in prices])

# At expiry: intrinsic-only payoff
def value_at_expiry(meta_price):
    long_intrinsic = max(meta_price - LONG_STRIKE, 0)
    short_intrinsic = max(meta_price - SHORT_STRIKE, 0)
    return (long_intrinsic - short_intrinsic - DEBIT) * 100

expiry_pl = np.array([value_at_expiry(p) for p in prices])

# Plot
fig, ax = plt.subplots(figsize=(13.33, 7.5))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# Curves
ax.plot(prices, today_pl, color="#1f3a93", linewidth=2.5,
        label=f"Now (Aug 10, {DTE_ENTRY} DTE)")
ax.plot(prices, expiry_pl, color="#2e8b57", linewidth=3.0,
        label="At Expiry (Oct 16, 2026)")

# Fill between
ax.fill_between(prices, today_pl, 0, where=(today_pl >= 0),
                color="#2e8b57", alpha=0.10, interpolate=True)
ax.fill_between(prices, today_pl, 0, where=(today_pl < 0),
                color="#a52a2a", alpha=0.10, interpolate=True)
ax.fill_between(prices, expiry_pl, 0, where=(expiry_pl >= 0),
                color="#2e8b57", alpha=0.18, interpolate=True)
ax.fill_between(prices, expiry_pl, 0, where=(expiry_pl < 0),
                color="#a52a2a", alpha=0.18, interpolate=True)

# Zero line
ax.axhline(0, color="#444444", linewidth=1.0, linestyle="-", alpha=0.7)

# Strike lines
ax.axvline(LONG_STRIKE, color="#666666", linewidth=1.2, linestyle="--", alpha=0.7)
ax.text(LONG_STRIKE, -16, f"  Long ${LONG_STRIKE:.0f}", color="#666666",
        fontsize=10, ha="left", va="top", style="italic")

ax.axvline(SHORT_STRIKE, color="#666666", linewidth=1.2, linestyle="--", alpha=0.7)
ax.text(SHORT_STRIKE, -16, f"  Short ${SHORT_STRIKE:.0f}", color="#666666",
        fontsize=10, ha="left", va="top", style="italic")

# Spot line
ax.axvline(SPOT, color="#0b5394", linewidth=1.5, linestyle="-", alpha=0.85)
ax.text(SPOT, MAX_PROFIT + 30, f"  Spot ${SPOT:.2f}", color="#0b5394",
        fontsize=11, ha="left", va="bottom", fontweight="bold")

# Breakeven line
ax.axvline(LOWER_BE, color="#7a3e9d", linewidth=1.2, linestyle=":", alpha=0.8)
ax.text(LOWER_BE, MAX_PROFIT + 65, f"  BE ${LOWER_BE:.2f}", color="#7a3e9d",
        fontsize=10, ha="left", va="bottom", style="italic")

# Max profit annotation (at short strike, at expiry)
ax.annotate(
    f"Max profit ${MAX_PROFIT:.2f}",
    xy=(SHORT_STRIKE - 0.5, MAX_PROFIT - 5),
    xytext=(SHORT_STRIKE - 8, MAX_PROFIT + 55),
    fontsize=11, color="#1b5e20", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#1b5e20", lw=1.5),
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#e8f5e9",
              edgecolor="#1b5e20", linewidth=1.2),
)

# Max loss annotation (at long strike, at expiry)
ax.annotate(
    f"Max loss ${MAX_LOSS:.2f}",
    xy=(LONG_STRIKE + 0.5, -MAX_LOSS + 5),
    xytext=(LONG_STRIKE - 6, -MAX_LOSS - 38),
    fontsize=11, color="#7a0a0a", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#7a0a0a", lw=1.5),
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#ffebee",
              edgecolor="#7a0a0a", linewidth=1.2),
)

# Now-curve peak annotation (today's MTM at short strike)
today_at_short = value_today(SHORT_STRIKE)
ax.annotate(
    f"Now MTM ${today_at_short:.2f}\n(META=${SHORT_STRIKE:.0f}, 67 DTE)",
    xy=(SHORT_STRIKE - 0.5, today_at_short - 5),
    xytext=(SHORT_STRIKE - 16, today_at_short + 40),
    fontsize=9.5, color="#0b5394", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#0b5394", lw=1.2),
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#e3f2fd",
              edgecolor="#0b5394", linewidth=1.0),
)

# Today curve label (italic gray)
today_at_low = value_today(580.0)
ax.text(580.5, today_at_low - 16,
        "Now: MTM near flat,\nlegs at full premium,\nno time harvested",
        fontsize=8.5, color="#666666", style="italic", ha="left", va="top")

# Axes / grid
ax.set_xlabel("META Price ($)", fontsize=12, fontweight="bold")
ax.set_ylabel("P/L per Contract ($)", fontsize=12, fontweight="bold")
ax.set_title(
    f"META Oct 16 '26 605/610 Bull Call Spread\n"
    f"Net Debit ${DEBIT:.2f}/share (${DEBIT*100:.2f}/contract) · "
    f"Max Profit ${MAX_PROFIT:.2f} · Max Loss ${MAX_LOSS:.2f} · "
    f"Lower BE ${LOWER_BE:.2f}",
    fontsize=13, fontweight="bold", pad=14,
)

ax.set_xlim(META_MIN, META_MAX)
ax.set_ylim(-MAX_LOSS - 60, MAX_PROFIT + 110)
ax.grid(True, alpha=0.25, linestyle=":", linewidth=0.7)
ax.set_axisbelow(True)

ax.tick_params(axis="both", labelsize=10)

legend = ax.legend(loc="upper left", fontsize=11, frameon=True,
                   facecolor="white", edgecolor="#cccccc")
legend.get_frame().set_linewidth(0.8)

# Source attribution
ax.text(0.99, 0.02,
        "Live chain: yfinance · OptionStrat basis verified · IV ~38%",
        transform=ax.transAxes, fontsize=8.5, color="#888888",
        ha="right", va="bottom", style="italic")

plt.tight_layout()
plt.savefig(OUT, dpi=100, facecolor="white", bbox_inches="tight")
plt.close()

print(f"Saved: {OUT}")
print(f"Net debit: ${DEBIT:.3f}/sh = ${DEBIT*100:.2f}/contract")
print(f"Max profit: ${MAX_PROFIT:.2f}/contract (at META >= ${SHORT_STRIKE:.0f} at Oct 16)")
print(f"Max loss: ${MAX_LOSS:.2f}/contract (= net debit)")
print(f"Lower breakeven: ${LOWER_BE:.3f}")
print(f"Reward-to-risk: {MAX_PROFIT/MAX_LOSS:.2f}:1")