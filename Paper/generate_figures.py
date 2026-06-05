#!/usr/bin/env python
"""Generate journal-style figures for the 3-week progress report."""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Journal style: serif font, black-on-white, thin lines, muted palette
rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "axes.linewidth": 0.8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# Muted palette (Tol / journal-safe)
PAL = {
    "navy":   "#1f3b73",
    "teal":   "#3d7d8a",
    "ochre":  "#c78b3a",
    "red":    "#a02c2c",
    "grey":   "#6c6c6c",
    "light":  "#c9c9c9",
}

OUT = "/data/binder_software/BindCraft/Paper/figures"
os.makedirs(OUT, exist_ok=True)
BASE = "/data/binder_software/BindCraft"


# ---------------------------------------------------------------------------
# Figure 1: Cross-run summary — acceptance across all five attempts
# ---------------------------------------------------------------------------
runs = [
    ("PD-L1\n(reference)",       1362, 101, "validation"),
    ("AAV2 monomer\nrun 1",        64,   0, "monomer"),
    ("AAV2 monomer\nrun 2 (HT)",  252,   0, "monomer"),
    ("AAV2 trimer\n3-fold",        15,   0, "trimer"),
    ("AAV2 dimer\ntrial 2 (βHT)",  37,   0, "dimer"),
    ("AAV2 dimer\ntrial 3 (HT+R)",278,  28, "dimer"),
]
labels  = [r[0] for r in runs]
totals  = [r[1] for r in runs]
accepted= [r[2] for r in runs]
failed  = [t - a for t, a in zip(totals, accepted)]

fig, ax = plt.subplots(figsize=(6.8, 3.2))
x = np.arange(len(labels))
ax.bar(x, failed,   color=PAL["light"], edgecolor="black", linewidth=0.5, label="Rejected trajectories")
ax.bar(x, accepted, bottom=failed, color=PAL["navy"], edgecolor="black", linewidth=0.5, label="Accepted designs")
for i, (t, a) in enumerate(zip(totals, accepted)):
    rate = 100 * a / t if t else 0
    ax.text(i, t + max(totals)*0.02, f"{a}/{t}\n({rate:.1f}%)", ha="center", va="bottom", fontsize=7)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=7.5)
ax.set_ylabel("Number of trajectories")
ax.set_title("Figure 1 | Design attempts and acceptance by target and protocol")
ax.legend(loc="upper left", frameon=False)
ax.set_ylim(0, max(totals) * 1.25)
fig.savefig(os.path.join(OUT, "fig1_run_summary.png"))
plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2: Trial 3 accepted-design metric distributions
# ---------------------------------------------------------------------------
df = pd.read_csv(os.path.join(BASE, "15delt3.pdb/output/final_design_stats.csv"))

metrics = [
    ("Average_i_pTM",            "Interface pTM",          0.50, "higher"),
    ("Average_i_pAE",            "Interface pAE",          0.35, "lower"),
    ("Average_pLDDT",            "Complex pLDDT",          0.80, "higher"),
    ("Average_dG",               "Binding ΔG (REU)",       0.0,  "lower"),
    ("Average_ShapeComplementarity","Shape complementarity", 0.60, "higher"),
    ("Average_Binder_RMSD",      "Binder RMSD (Å)",        3.5,  "lower"),
]
fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.2))
for ax, (col, lab, cut, direction) in zip(axes.flat, metrics):
    vals = df[col].dropna()
    ax.hist(vals, bins=10, color=PAL["teal"], edgecolor="black", linewidth=0.5, alpha=0.85)
    ax.axvline(cut, color=PAL["red"], linestyle="--", linewidth=1, label=f"cutoff = {cut}")
    ax.set_xlabel(lab)
    ax.set_ylabel("Count" if ax in axes[:, 0] else "")
    ax.legend(frameon=False, fontsize=7, loc="best")
fig.suptitle("Figure 2 | Distribution of validation metrics for n = 28 accepted designs (Trial 3)",
             fontsize=10, y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_trial3_metrics.png"))
plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3: The structural-integrity failure — Target_RMSD vs i_pTM
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))

# (a) Histogram of Target_RMSD with cutoff
axes[0].hist(df["Average_Target_RMSD"], bins=12, color=PAL["ochre"],
             edgecolor="black", linewidth=0.5, alpha=0.85)
axes[0].axvline(5.0, color=PAL["red"], linestyle="--", linewidth=1, label="acceptable (<5 Å)")
axes[0].set_xlabel("Target RMSD (Å)")
axes[0].set_ylabel("Count")
axes[0].set_title("(a) Target geometry deviation", fontsize=9)
axes[0].legend(frameon=False, fontsize=7)

# (b) Scatter: i_pTM vs Target_RMSD
axes[1].scatter(df["Average_Target_RMSD"], df["Average_i_pTM"],
                s=20, color=PAL["navy"], edgecolor="black", linewidth=0.4, alpha=0.8)
axes[1].axvline(5.0, color=PAL["red"], linestyle="--", linewidth=1)
axes[1].set_xlabel("Target RMSD (Å)")
axes[1].set_ylabel("Interface pTM")
axes[1].set_title("(b) High confidence masks target collapse", fontsize=9)

fig.suptitle("Figure 3 | All 28 accepted designs show severe target-chain displacement",
             fontsize=10, y=1.04)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_target_rmsd_failure.png"))
plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4: Trajectory outcome breakdown across runs (where designs die)
# ---------------------------------------------------------------------------
# columns: LowConf, Clashing, MPNN-failed, Accepted
outcomes = pd.DataFrame({
    "run": ["Monomer\nrun 1", "Monomer\nrun 2", "Trimer", "Dimer\ntrial 2", "Dimer\ntrial 3"],
    "LowConf":  [33, 108, 11, 12, 83],
    "Clashing": [31, 144,  3, 25, 167],
    "MPNN-filter failed": [0, 0, 1, 0, 0],
    "Accepted": [0, 0, 0, 0, 28],
})
fig, ax = plt.subplots(figsize=(6.8, 3.0))
bottom = np.zeros(len(outcomes))
cols_ = ["LowConf", "Clashing", "MPNN-filter failed", "Accepted"]
colors = [PAL["ochre"], PAL["grey"], PAL["teal"], PAL["navy"]]
for col, c in zip(cols_, colors):
    ax.bar(outcomes["run"], outcomes[col], bottom=bottom,
           color=c, edgecolor="black", linewidth=0.5, label=col)
    bottom = bottom + outcomes[col].values
ax.set_ylabel("Trajectories")
ax.set_title("Figure 4 | Failure mode distribution across AAV2 design runs")
ax.legend(frameon=False, loc="upper left")
fig.savefig(os.path.join(OUT, "fig4_outcomes.png"))
plt.close(fig)

print("Figures written to:", OUT)
for f in sorted(os.listdir(OUT)):
    print(" -", f)
