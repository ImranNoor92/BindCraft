#!/usr/bin/env python3
"""Generate the proposed C3-symmetric design workflow diagram for the report."""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from pathlib import Path

OUT = Path("/data/binder_software/BindCraft/runs/15delt3/report_assets/fig_workflow.png")

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Liberation Serif", "DejaVu Serif", "Times New Roman"],
    "font.size": 10,
})

fig, ax = plt.subplots(figsize=(8.0, 10.0))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis("off")

# Color palette
PHASE_COLORS = {
    1: ("#dbe7f4", "#3a6b9a"),  # light blue, dark blue
    2: ("#e3d9f0", "#7b58a8"),  # light purple, dark purple
    3: ("#dceedd", "#3a8a4a"),  # light green, dark green
    4: ("#fae3c8", "#c47225"),  # light orange, dark orange
}

INPUT_COLOR = ("#f5e6e6", "#8a4a4a")
OUTPUT_COLOR = ("#e8e8e8", "#444444")
ACID_COLOR = ("#fde2e2", "#a02020")

def draw_box(x, y, w, h, title, body, face, edge, title_size=10, body_size=9, title_weight="bold"):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.05,rounding_size=0.12",
                         facecolor=face, edgecolor=edge, linewidth=1.3)
    ax.add_patch(box)
    ax.text(x + w/2, y + h - 0.22, title, ha="center", va="top",
            fontsize=title_size, fontweight=title_weight, color=edge)
    if body:
        ax.text(x + w/2, y + h - 0.55, body, ha="center", va="top",
                fontsize=body_size, color="black", wrap=True)

def draw_arrow(x1, y1, x2, y2, label=None, label_xy=None, color="#444444"):
    arr = FancyArrowPatch((x1, y1), (x2, y2),
                          arrowstyle="->, head_width=0.35, head_length=0.45",
                          color=color, linewidth=1.4, mutation_scale=14)
    ax.add_patch(arr)
    if label and label_xy:
        ax.text(label_xy[0], label_xy[1], label, ha="left", va="center",
                fontsize=8.5, style="italic", color="#444444",
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.9))

# ----- Title -----
ax.text(5.0, 13.55, "Proposed workflow: C3-symmetric trimer binder design",
        ha="center", va="top", fontsize=12.5, fontweight="bold")
ax.text(5.0, 13.10, "(executed in /data/binder_software/BindCraft/runs/15delt3/pre-binder/)",
        ha="center", va="top", fontsize=9.5, style="italic", color="#555555")

# ----- Inputs box (top left) -----
draw_box(0.2, 11.1, 3.6, 1.55, "INPUTS",
         "• Target PDB: hexamer (6 chains, 70–150)\n• Hotspots: A105, A107, A109, A111, A114, A115\n• Binder length range: 60–90 aa\n• C3 axis: (0, 0, 180.8) Å (verified)",
         INPUT_COLOR[0], INPUT_COLOR[1])

# Vertical guideline
ax.plot([5, 5], [10.7, 0.9], color="#cccccc", linestyle="--", linewidth=0.6, zorder=1)

# ----- Phase 1: RFdiffusion -----
draw_box(0.8, 9.1, 8.4, 1.5, "Phase 1  ·  RFdiffusion (single-subunit PPI mode)",
         "Design one binder subunit against chain A of the hexamer, with B–F as fixed steric context.\n"
         "No symmetry constraint here; hotspot bias used reliably.\n"
         "Output: 10 backbone PDBs in outputs/01_rfdiffusion_pilot/   ·   wall-time ≈ 2–4 h on 1 GPU",
         PHASE_COLORS[1][0], PHASE_COLORS[1][1])

draw_arrow(5, 11.05, 5, 10.65,
           "Hotspots + target geometry", (5.15, 10.85))

# ----- Phase 2a: C3 replication -----
draw_box(0.8, 7.3, 8.4, 1.5, "Phase 2a  ·  Geometric C3 replication (Python, no ML)",
         "Rotate each Phase 1 backbone by 120° and 240° around the verified C3 axis.\n"
         "Fuse the three copies into one polypeptide with flexible (GGGGS)n linkers.\n"
         "Output: ~10 trimerized PDBs in outputs/02a_trimerized/   ·   wall-time < 1 min",
         PHASE_COLORS[2][0], PHASE_COLORS[2][1])
draw_arrow(5, 9.1, 5, 8.8, "10 single-subunit backbones", (5.15, 8.95))

# ----- Phase 2b: AF2 validation -----
draw_box(0.8, 5.5, 8.4, 1.5, "Phase 2b  ·  AlphaFold-multimer validation (filter pass 1)",
         "Predict (hexamer + fused trimer); apply 4 filters:\n"
         "binder pLDDT > 0.70   ·   interface pTM > 0.65   ·   per-subunit interface SASA > 200 Å²   ·   RMSD vs design < 3 Å\n"
         "Output: ~3–5 validated trimer backbones in outputs/02b_af2_validated/   ·   wall-time ≈ 2 h",
         PHASE_COLORS[2][0], PHASE_COLORS[2][1])
draw_arrow(5, 7.3, 5, 7.0, "C3-symmetric trimer backbones", (5.15, 7.15))

# ----- Phase 3: MPNN -----
draw_box(0.8, 3.7, 8.4, 1.5, "Phase 3  ·  ProteinMPNN sequence design (tied positions)",
         "Design binder sequences with target chains (A–F) fixed and positions of all 3 subunits tied.\n"
         "Result: each backbone receives ~8 candidate sequences, all preserving the homotrimer symmetry.\n"
         "Output: ~30 sequenced backbones in outputs/03_mpnn_sequences/   ·   wall-time ≈ 30 min",
         PHASE_COLORS[3][0], PHASE_COLORS[3][1])
draw_arrow(5, 5.5, 5, 5.2, "Validated trimer backbones", (5.15, 5.35))

# ----- Phase 4: AF2 re-validation -----
draw_box(0.8, 1.9, 8.4, 1.5, "Phase 4  ·  AlphaFold-multimer re-validation (filter pass 2)",
         "Predict each MPNN sequence against the hexamer; re-apply the same 4 filters.\n"
         "Rank survivors by:  score = i_pTM × pLDDT × (1 / max(RMSD, 0.5)) × (ΣiSASA / 1000)\n"
         "Output: ranked validated designs in outputs/04_final_ranked/   ·   wall-time ≈ 2 h",
         PHASE_COLORS[4][0], PHASE_COLORS[4][1])
draw_arrow(5, 3.7, 5, 3.4, "Trimers with designed sequences", (5.15, 3.55))

# ----- ACID TEST -----
draw_box(0.8, 0.1, 8.4, 1.55, "ACID TEST  ·  Dimer-only specificity re-prediction",
         "Re-predict each Phase 4 survivor against only one dimer pair (chains A + E).\n"
         "REQUIRE  interface pTM drop ≥ 0.15  AND  at least one subunit with interface SASA ≈ 0.\n"
         "Designs that pass: confirmed hexamer-specific binders — proceed to wet-lab.\n"
         "Designs that fail: hexamer + dimer binders — discard.",
         ACID_COLOR[0], ACID_COLOR[1], title_weight="bold")
draw_arrow(5, 1.9, 5, 1.65, "Ranked candidates", (5.15, 1.78))

# ----- Side annotations: funnel counts (right-margin) -----
funnel_x = 9.45
ax.text(funnel_x, 9.85, "10", ha="center", va="center", fontsize=14, fontweight="bold", color=PHASE_COLORS[1][1])
ax.text(funnel_x, 8.05, "~10", ha="center", va="center", fontsize=12, fontweight="bold", color=PHASE_COLORS[2][1])
ax.text(funnel_x, 6.25, "~3–5", ha="center", va="center", fontsize=12, fontweight="bold", color=PHASE_COLORS[2][1])
ax.text(funnel_x, 4.45, "~30", ha="center", va="center", fontsize=12, fontweight="bold", color=PHASE_COLORS[3][1])
ax.text(funnel_x, 2.65, "~5–15", ha="center", va="center", fontsize=12, fontweight="bold", color=PHASE_COLORS[4][1])
ax.text(funnel_x, 0.85, "≥3", ha="center", va="center", fontsize=14, fontweight="bold", color=ACID_COLOR[1])
ax.text(funnel_x, 12.4, "n =", ha="center", va="center", fontsize=9, style="italic", color="#666666")

fig.savefig(OUT, dpi=300, bbox_inches="tight")
print(f"wrote {OUT}")
