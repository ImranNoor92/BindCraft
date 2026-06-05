#!/usr/bin/env python3
"""Generate publication-grade figures for the trial 5 / trial 6 report."""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from math import sqrt
from pathlib import Path

OUT = Path("/data/binder_software/BindCraft/runs/15delt3/report_assets")
OUT.mkdir(exist_ok=True)

# Use serif fonts and tight publication style
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Liberation Serif", "DejaVu Serif", "Times New Roman"],
    "font.size": 11,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "axes.linewidth": 0.8,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# -----------------------------------------------------------
# Figure A: Trajectory funnel comparison (Trial 5 vs Trial 6)
# -----------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.0, 3.6))
stages = ["Trajectories\nstarted", "Stage 1\npLDDT > 0.65", "Reached\nRelaxed", "MPNN\ndesigned", "Accepted\ndesigns"]
trial5 = [42, 0, 0, 0, 0]
trial6 = [71, 22, 1, 0, 0]
x = np.arange(len(stages))
width = 0.36
bars5 = ax.bar(x - width/2, trial5, width, label="Trial 5 (A+F)", color="#b04545", edgecolor="black", linewidth=0.5)
bars6 = ax.bar(x + width/2, trial6, width, label="Trial 6 (A+C+E)", color="#3a6b9a", edgecolor="black", linewidth=0.5)
for bars in (bars5, bars6):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x()+b.get_width()/2, h+1.0, f"{int(h)}", ha="center", va="bottom", fontsize=9)
ax.set_ylabel("Number of designs")
ax.set_xticks(x)
ax.set_xticklabels(stages)
ax.set_ylim(0, max(trial6)*1.15)
ax.legend(frameon=False, loc="upper right")
fig.savefig(OUT/"fig_funnel.png")
plt.close(fig)
print(f"wrote {OUT/'fig_funnel.png'}")

# -----------------------------------------------------------
# Figure B: Hotspot patch geometry (top-down hexamer view)
# -----------------------------------------------------------
PDB = Path("/data/binder_software/BindCraft/runs/15delt3/trial_6_may_20/1lp3_hexamer_trimmed_fixed.pdb")
hot = {}
for line in PDB.read_text().splitlines():
    if line.startswith("ATOM") and line[12:16].strip() == "CA":
        r = int(line[22:26]); c = line[21]
        if 105 <= r <= 115:
            hot.setdefault(c, []).append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
cent = {c: np.mean(p, axis=0) for c, p in hot.items()}

fig, ax = plt.subplots(figsize=(5.5, 5.5))
chain_color = {"A": "#1f77b4", "B": "#ff7f0e", "C": "#2ca02c", "D": "#d62728", "E": "#9467bd", "F": "#8c564b"}
pairs = [("A","E"), ("B","D"), ("C","F")]
for c1,c2 in pairs:
    ax.plot([cent[c1][0], cent[c2][0]], [cent[c1][1], cent[c2][1]],
            "-", color="gray", linewidth=1.4, alpha=0.55, zorder=1)
# Trial 5 anchor (A+F midpoint)
m5 = (cent["A"]+cent["F"])/2
ax.scatter([m5[0]], [m5[1]], s=170, marker="X", color="#b04545", edgecolor="black", linewidth=0.6, zorder=4, label="Trial 5 anchor (A+F midpoint)")
# Trial 6 anchor (A+C+E centroid)
m6 = (cent["A"]+cent["C"]+cent["E"])/3
ax.scatter([m6[0]], [m6[1]], s=170, marker="X", color="#3a6b9a", edgecolor="black", linewidth=0.6, zorder=4, label="Trial 6 anchor (A+C+E centroid)")
# Chains
for c, p in cent.items():
    ax.scatter([p[0]], [p[1]], s=320, color=chain_color[c], edgecolor="black", linewidth=0.7, zorder=3)
    ax.text(p[0], p[1], c, ha="center", va="center", fontsize=11, fontweight="bold", zorder=5)
# 3-fold axis
ax.scatter([0],[0], s=70, marker="+", color="black", zorder=2)
ax.text(0.5, 0.5, "3-fold axis", fontsize=9, color="black", ha="left")
# Distance line A-F (the bridging requirement)
ax.annotate("", xy=(cent["F"][0], cent["F"][1]), xytext=(cent["A"][0], cent["A"][1]),
            arrowprops=dict(arrowstyle="<->", color="#b04545", lw=1.0, alpha=0.7))
ax.text((cent["A"][0]+cent["F"][0])/2 + 1.5, (cent["A"][1]+cent["F"][1])/2,
        f"23.6 Å", fontsize=9, color="#b04545")
# Distance C to trial 5 midpoint
ax.annotate("", xy=(cent["C"][0], cent["C"][1]), xytext=(m5[0], m5[1]),
            arrowprops=dict(arrowstyle="<->", color="darkred", lw=1.0, linestyle="--"))
ax.text((m5[0]+cent["C"][0])/2 + 0.7, (m5[1]+cent["C"][1])/2 - 1,
        f"7.2 Å (clash)", fontsize=9, color="darkred")
ax.set_aspect("equal")
ax.set_xlabel("X (Å)")
ax.set_ylabel("Y (Å)")
ax.set_title("Hotspot patch geometry (top-down view)")
ax.set_xlim(-25, 25); ax.set_ylim(-22, 18)
ax.grid(True, alpha=0.25, linewidth=0.4)
ax.legend(frameon=False, loc="lower left", fontsize=9)
fig.savefig(OUT/"fig_geometry.png")
plt.close(fig)
print(f"wrote {OUT/'fig_geometry.png'}")

# -----------------------------------------------------------
# Figure C: SASA per residue, 105-115, by chain group
# -----------------------------------------------------------
# Data from earlier SASA analysis (rSASA in hexamer context)
residues = list(range(105, 116))
aa = ["LYS","GLU","VAL","THR","GLN","ASN","ASP","GLY","THR","THR","THR"]
# Group 1 (chains A, D, F) — symmetric class 1
group1 = [0.46, 0.21, 0.50, 0.03, 0.54, 0.00, 0.43, 0.82, 0.29, 0.46, 0.30]
# Group 2 (chains B, C, E) — symmetric class 2
group2 = [0.34, 0.45, 0.59, 0.46, 0.53, 0.54, 0.69, 0.03, 0.05, 0.06, 0.37]

fig, ax = plt.subplots(figsize=(7.0, 3.6))
x = np.arange(len(residues))
width = 0.4
ax.bar(x - width/2, group1, width, color="#a44a4a", edgecolor="black", linewidth=0.5, label="Chains A, D, F")
ax.bar(x + width/2, group2, width, color="#4a7da4", edgecolor="black", linewidth=0.5, label="Chains B, C, E")
ax.axhline(0.30, color="green", linestyle="--", linewidth=0.8, alpha=0.7)
ax.text(len(residues)-0.5, 0.31, "exposed threshold (0.30)", fontsize=8.5, color="green", ha="right")
ax.axhline(0.10, color="darkred", linestyle="--", linewidth=0.8, alpha=0.7)
ax.text(len(residues)-0.5, 0.105, "buried threshold (0.10)", fontsize=8.5, color="darkred", ha="right")
ax.set_xticks(x)
ax.set_xticklabels([f"{r}\n{a}" for r,a in zip(residues,aa)])
ax.set_ylabel("Relative SASA (rSASA)")
ax.set_xlabel("Residue (chain A numbering, with amino acid)")
ax.set_title("Solvent accessibility of residues 105–115 in the hexamer")
ax.set_ylim(0, 0.95)
ax.legend(frameon=False, loc="upper right")
fig.savefig(OUT/"fig_sasa.png")
plt.close(fig)
print(f"wrote {OUT/'fig_sasa.png'}")

# -----------------------------------------------------------
# Figure D: Failure mode pie / breakdown for Trial 6
# -----------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.0, 4.2))
labels = ["Severe clashes\nat relaxation", "Low pLDDT\nat Stage 1", "Reached Relaxed\n(success)"]
values = [68, 47, 1]
# remove overlap: pLDDT-low trajectories are part of clashing pool — so present as stacked source-of-failure
# Use a horizontal bar instead
fig, ax = plt.subplots(figsize=(7.0, 2.4))
y = [0]
ax.barh(y, [22], height=0.5, color="#3a6b9a", edgecolor="black", linewidth=0.5, label="Passed Stage 1 (n=22)")
ax.barh(y, [47], left=[22], height=0.5, color="#b04545", edgecolor="black", linewidth=0.5, label="Failed Stage 1 (n=47)")
ax.barh(y, [2], left=[69], height=0.5, color="#888888", edgecolor="black", linewidth=0.5, label="In progress (n=2)")
# Overlay clash icon
ax.set_xlim(0, 71)
ax.set_yticks([])
ax.set_xlabel("Trajectories started (n=71)")
ax.set_title("Trial 6 trajectory outcomes after 21h 44min")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.35), ncol=3)
# Annotations
ax.annotate("Of 22 that passed Stage 1,\nonly 1 cleared the relaxation step\n(clash-free fold).",
            xy=(11, 0.25), xytext=(11, 0.55), fontsize=9, ha="center",
            arrowprops=dict(arrowstyle="->", lw=0.8))
fig.savefig(OUT/"fig_outcomes.png")
plt.close(fig)
print(f"wrote {OUT/'fig_outcomes.png'}")

print("\nAll figures written to", OUT)
