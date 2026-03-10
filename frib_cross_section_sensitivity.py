"""
FRIB Minimum Measurable Cross Section - Chart of Nuclides
==========================================================
sigma_min = 1 / (Rate [pps] * target [atoms/cm^2] * time [s])
Assumes: target = 1e20 atoms/cm^2, beam time = 1 week (604800 s)
Result in nanobarns (1 nb = 1e-33 cm^2)
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd

# ── Parameters ────────────────────────────────────────────────────────────────
FRIB_FILE  = "/mnt/c/Users/cbben/Desktop/FRIB_Rates.txt"
TARGET     = 1e20          # atoms/cm^2
BEAM_TIME  = 7 * 24 * 3600  # 1 week in seconds
MIN_RATE   = 1e4           # pps cut (lower bound)
MAX_RATE   = 1e8           # pps cut (upper bound, rates above this are clamped)
BARN_TO_CM2 = 1e-24        # 1 barn = 1e-24 cm^2
MB_TO_CM2  = 1e-27        # 1 millibarn = 1e-27 cm^2

# ── Load data ─────────────────────────────────────────────────────────────────
rows = []
with open(FRIB_FILE) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("!"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            N, Z, rate = int(parts[0]), int(parts[1]), float(parts[2])
        except ValueError:
            continue
        rows.append({"N": N, "Z": Z, "A": N + Z, "rate": rate})

df = pd.DataFrame(rows)
print(f"Total isotopes in file: {len(df)}")

# Apply lower rate cut; keep all above MIN_RATE
df = df[df["rate"] >= MIN_RATE].copy()
print(f"Isotopes with rate >= {MIN_RATE:.0e} pps: {len(df)}")

# Clamp rate at MAX_RATE for sigma calculation — ions above MAX_RATE plotted
# at the MAX_RATE sensitivity (brightest color saturates there)
df["rate_clamped"] = df["rate"].clip(upper=MAX_RATE)
n_clamped = (df["rate"] > MAX_RATE).sum()
print(f"  of which {n_clamped} have rate > {MAX_RATE:.0e} pps (clamped to max color)")

# ── Calculate minimum cross section ──────────────────────────────────────────
# sigma_min [cm^2] = N_min / (rate * target * time)
# sigma_min [nb]   = N_min / (rate * target * time) / NB_TO_CM2
N_MIN = 1e5  # minimum number of detected counts
df["sigma_min_cm2"] = N_MIN / (df["rate_clamped"] * TARGET * BEAM_TIME)
df["sigma_min_mb"]  = df["sigma_min_cm2"] / MB_TO_CM2
df["log10_sigma"]   = np.log10(df["sigma_min_mb"])

print(f"\nCross section sensitivity range:")
print(f"  Min sigma_min = {df['sigma_min_mb'].min():.2e} mb  (highest rate)")
print(f"  Max sigma_min = {df['sigma_min_mb'].max():.2e} mb  (lowest rate ~1e4 pps)")

# ── Load magic numbers for reference lines ────────────────────────────────────
MAGIC = [2, 8, 20, 28, 50, 82, 126]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 10))

# Color scale: log10(sigma_min [nb])
vmin = df["log10_sigma"].min()
vmax = df["log10_sigma"].max()
cmap = plt.cm.plasma_r  # bright = small sigma = better sensitivity

sc = ax.scatter(
    df["N"], df["Z"],
    c=df["log10_sigma"],
    cmap=cmap,
    vmin=vmin, vmax=vmax,
    s=8,
    marker="s",
    linewidths=0,
    zorder=2,
)

# ── Magic number lines ────────────────────────────────────────────────────────
for m in MAGIC:
    ax.axvline(m, color="white", lw=0.5, alpha=0.3, zorder=1)
    ax.axhline(m, color="white", lw=0.5, alpha=0.3, zorder=1)

# ── Stability valley (Z ≈ N for light nuclei, bends for heavy) ───────────────
# Draw diagonal N=Z line
diag_z = np.arange(0, 100)
ax.plot(diag_z, diag_z, "w--", lw=0.8, alpha=0.4, label="N = Z", zorder=1)

# ── Colorbar ──────────────────────────────────────────────────────────────────
cbar = fig.colorbar(sc, ax=ax, pad=0.01, fraction=0.025)
cbar.set_label(r"$\log_{10}(\sigma_{\min}\ [\mathrm{mb}])$", fontsize=13)

# Add human-readable tick labels
tick_vals = np.arange(np.ceil(vmin), np.floor(vmax) + 1)
cbar.set_ticks(tick_vals)
cbar.set_ticklabels([f"$10^{{{int(v)}}}$ mb" for v in tick_vals], fontsize=9)

# ── Axes labels / formatting ──────────────────────────────────────────────────
ax.set_xlabel("Neutron Number  N", fontsize=13)
ax.set_ylabel("Proton Number  Z", fontsize=13)
ax.set_title(
    f"FRIB Minimum Measurable Cross Section\n"
    f"(Rate $\\geq 10^4$ pps, clamped at $10^8$ pps, Target $= 10^{{20}}$ atoms/cm², Beam time = 1 week, $N_{{\\min}} = 10^5$ counts)",
    fontsize=13,
)

# Magic number labels along axes
for m in MAGIC:
    if m <= ax.get_xlim()[1]:
        ax.text(m, ax.get_ylim()[0] + 0.5, str(m), color="white",
                fontsize=7, ha="center", va="bottom", alpha=0.6)
    if m <= ax.get_ylim()[1]:
        ax.text(ax.get_xlim()[0] + 0.5, m, str(m), color="white",
                fontsize=7, ha="left", va="center", alpha=0.6)

ax.set_facecolor("#1a1a2e")
fig.patch.set_facecolor("#0f0f1a")
ax.tick_params(colors="white")
ax.xaxis.label.set_color("white")
ax.yaxis.label.set_color("white")
ax.title.set_color("white")
cbar.ax.yaxis.set_tick_params(color="white")
plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")
cbar.set_label(r"$\log_{10}(\sigma_{\min}\ [\mathrm{mb}])$", fontsize=13, color="white")

ax.legend(loc="upper left", fontsize=9, framealpha=0.3, labelcolor="white")

plt.tight_layout()
out = "/mnt/c/Users/cbben/Desktop/FRIB_sensitivity_chart.png"
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\nSaved to: {out}")
plt.show()
