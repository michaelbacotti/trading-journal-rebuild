#!/usr/bin/env python3
"""SLV Nov 20 '26 60/62 Bull Call Spread — P/L curve.

Light theme: white bg, navy/green/red accents. Three horizons:
- Now (Aug 10, 2026, 102 DTE) — entry, both legs at full premium, small negative P/L
- At expiry (Nov 20, 2026) — the realized P/L curve

Math:
- Long $60C paid $5.075 mid (basis $5.05, 0.49% gap)
- Short $62C received $4.35 mid (basis $4.35, 0.00% gap)
- Net debit (live mid): $0.725/share = $72.50/contract
- Net debit (basis): $0.70/share = $70/contract
- Strike width: $2.00
- Max profit: ($2 - $0.725) × 100 = $127.50/contract (basis: $130)
- Max loss: $72.50/contract
- Lower breakeven: $60.725
- Upper breakeven: N/A (capped at $62, profit flattens)
- Spot: $58.88

Both calls are deep OTM at entry (long +1.90%, short +5.30%).
"""
import math
import os
import sys

import numpy as np
import matplotlib.pyplot as plt

OUT = os.path.join(os.path.dirname(__file__), "pl-curve.png")

# Trade constants
LONG_STRIKE = 60.0
SHORT_STRIKE = 62.0
SPOT = 58.88
DEBIT = 0.725  # live mid basis ($/share)
WIDTH = SHORT_STRIKE - LONG_STRIKE  # $2
MAX_PROFIT = (WIDTH - DEBIT) * 100  # $127.50
MAX_LOSS = DEBIT * 100  # $72.50
LOWER_BE = LONG_STRIKE + DEBIT  # $60.725
IV = 0.46  # ~46% (live chain avg)

# Today (entry) Greeks via BSM
DTE_ENTRY = 102  # Nov 20 - Aug 10
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
SLV_MIN = 56.0
SLV_MAX = 64.0
prices = np.linspace(SLV_MIN, SLV_MAX, 401)

# Today curve: long_call - short_call - debit (per share)
def value_today(slv_price):
    long_val = bs_call(slv_price, LONG_STRIKE, T, R, IV)
    short_val = bs_call(slv_price, SHORT_STRIKE, T, R, IV)
    return (long_val - short_val - DEBIT) * 100  # per contract

today_pl = np.array([value_today(p) for p in prices])

# At expiry: intrinsic-only payoff
def value_at_expiry(slv_price):
    long_intrinsic = max(slv_price - LONG_STRIKE, 0)
    short_intrinsic = max(slv_price - SHORT_STRIKE, 0)
    return (long_intrinsic - short_intrinsic - DEBIT) * 100

expiry_pl = np.array([value_at_expiry(p) for p in prices])

# Plot
plt.figure(figsize=(13.33, 7.5), dpi=100)
fig, ax = plt.subplots(figsize=(13.33, 7.5))

# Light theme
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# Curves
ax.plot(prices, today_pl, color="#1f3a93", linewidth=2.5,
        label=f"Now (Aug 10, {DTE_ENTRY} DTE)")
ax.plot(prices, expiry_pl, color="#2e8b57", linewidth=3.0,
        label="At Expiry (Nov 20, 2026)")

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
ax.text(LONG_STRIKE, -8, f"  Long ${LONG_STRIKE:.0f}", color="#666666",
        fontsize=10, ha="left", va="top", style="italic")

ax.axvline(SHORT_STRIKE, color="#666666", linewidth=1.2, linestyle="--", alpha=0.7)
ax.text(SHORT_STRIKE, -8, f"  Short ${SHORT_STRIKE:.0f}", color="#666666",
        fontsize=10, ha="left", va="top", style="italic")

# Spot line
ax.axvline(SPOT, color="#0b5394", linewidth=1.5, linestyle="-", alpha=0.85)
ax.text(SPOT, MAX_PROFIT + 12, f"  Spot ${SPOT:.2f}", color="#0b5394",
        fontsize=11, ha="left", va="bottom", fontweight="bold")

# Breakeven line
ax.axvline(LOWER_BE, color="#7a3e9d", linewidth=1.2, linestyle=":", alpha=0.8)
ax.text(LOWER_BE, MAX_PROFIT + 25, f"  BE ${LOWER_BE:.2f}", color="#7a3e9d",
        fontsize=10, ha="left", va="bottom", style="italic")

# Max profit annotation (at short strike, at expiry)
ax.annotate(
    f"Max profit ${MAX_PROFIT:.2f}",
    xy=(SHORT_STRIKE - 0.05, MAX_PROFIT - 2),
    xytext=(SHORT_STRIKE - 0.7, MAX_PROFIT + 22),
    fontsize=11, color="#1b5e20", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#1b5e20", lw=1.5),
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#e8f5e9",
              edgecolor="#1b5e20", linewidth=1.2),
)

# Max loss annotation (at long strike, at expiry)
max_loss_idx = np.argmin(expiry_pl)
ax.annotate(
    f"Max loss ${MAX_LOSS:.2f}",
    xy=(LONG_STRIKE - 0.1, -MAX_LOSS + 2),
    xytext=(LONG_STRIKE - 1.8, -MAX_LOSS - 18),
    fontsize=11, color="#7a0a0a", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#7a0a0a", lw=1.5),
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#ffebee",
              edgecolor="#7a0a0a", linewidth=1.2),
)

# Now-curve peak annotation (today's MTM at short strike)
today_at_short = value_today(SHORT_STRIKE)
ax.annotate(
    f"Now MTM ${today_at_short:.2f}\n(SLV=${SHORT_STRIKE:.0f}, 102 DTE)",
    xy=(SHORT_STRIKE - 0.05, today_at_short - 1),
    xytext=(SHORT_STRIKE - 2.0, today_at_short + 18),
    fontsize=9.5, color="#0b5394", fontweight="bold",
    arrowprops=dict(arrowstyle="->", color="#0b5394", lw=1.2),
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#e3f2fd",
              edgecolor="#0b5394", linewidth=1.0),
)

# Today curve label (italic gray)
today_at_56 = value_today(56.0)
ax.text(56.1, today_at_56 - 8,
        "Now: MTM near flat,\nlegs at full premium,\nno time harvested",
        fontsize=8.5, color="#666666", style="italic", ha="left", va="top")

# Axes / grid
ax.set_xlabel("SLV Price ($)", fontsize=12, fontweight="bold")
ax.set_ylabel("P/L per Contract ($)", fontsize=12, fontweight="bold")
ax.set_title(
    f"SLV Nov 20 '26 60/62 Bull Call Spread\n"
    f"Net Debit ${DEBIT:.3f}/share (${DEBIT*100:.2f}/contract) · "
    f"Max Profit ${MAX_PROFIT:.2f} · Max Loss ${MAX_LOSS:.2f} · "
    f"Lower BE ${LOWER_BE:.2f}",
    fontsize=13, fontweight="bold", pad=14,
)

ax.set_xlim(SLV_MIN, SLV_MAX)
ax.set_ylim(-MAX_LOSS - 25, MAX_PROFIT + 50)
ax.grid(True, alpha=0.25, linestyle=":", linewidth=0.7)
ax.set_axisbelow(True)

# Tick formatting
ax.tick_params(axis="both", labelsize=10)

# Legend
legend = ax.legend(loc="upper left", fontsize=11, frameon=True,
                   facecolor="white", edgecolor="#cccccc")
legend.get_frame().set_linewidth(0.8)

# Source attribution
ax.text(0.99, 0.02,
        "Live chain: yfinance · OptionStrat basis verified · IV ~46%",
        transform=ax.transAxes, fontsize=8.5, color="#888888",
        ha="right", va="bottom", style="italic")

plt.tight_layout()
plt.savefig(OUT, dpi=100, facecolor="white", bbox_inches="tight")
plt.close()

print(f"Saved: {OUT}")
print(f"Net debit: ${DEBIT:.3f}/sh = ${DEBIT*100:.2f}/contract")
print(f"Max profit: ${MAX_PROFIT:.2f}/contract (at SLV >= ${SHORT_STRIKE:.0f} at Nov 20)")
print(f"Max loss: ${MAX_LOSS:.2f}/contract (= net debit)")
print(f"Lower breakeven: ${LOWER_BE:.3f}")
print(f"Reward-to-risk: {MAX_PROFIT/MAX_LOSS:.2f}:1")