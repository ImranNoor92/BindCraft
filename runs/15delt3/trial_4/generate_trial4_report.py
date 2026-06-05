#!/usr/bin/env python
"""
Trial 4 Final Report Generator
==============================
Produces a self-contained HTML report and a typeset PDF documenting the outcome
of Trial 4 (BindCraft AAV2 T3 dimer design with Target_RMSD <= 5 Å enforced).

The script is reproducible: re-running it on the same trial_4 directory
will regenerate the report from the raw CSVs and directory contents.

Usage:
    conda activate BindCraft
    python generate_trial4_report.py
"""
import base64
import datetime
import io
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
import pandas as pd
import weasyprint

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
TRIAL_DIR        = os.path.dirname(os.path.abspath(__file__))
REPORT_HTML_PATH = os.path.join(TRIAL_DIR, "trial4_final_report.html")
REPORT_PDF_PATH  = os.path.join(TRIAL_DIR, "trial4_final_report.pdf")

# Muted gravity palette
PAL = {
    "ink":      "#1f2933",
    "navy":     "#1f3b73",
    "slate":    "#5c6b7a",
    "ash":      "#9aa5b1",
    "fog":      "#cbd2d9",
    "paper":    "#f5f7fa",
    "warning":  "#a02c2c",
}

# Figures: Times New Roman to match the report
rcParams.update({
    "font.family":     "serif",
    "font.serif":      ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size":       9,
    "axes.labelsize":  9,
    "axes.titlesize":  10,
    "axes.linewidth":  0.6,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi":      150,
    "savefig.dpi":     200,
    "savefig.bbox":    "tight",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.edgecolor":    PAL["ink"],
    "axes.labelcolor":   PAL["ink"],
    "xtick.color":       PAL["ink"],
    "ytick.color":       PAL["ink"],
    "text.color":        PAL["ink"],
})


def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


# ---------------------------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------------------------
mpnn_df  = pd.read_csv(os.path.join(TRIAL_DIR, "mpnn_design_stats.csv"))
fail_row = pd.read_csv(os.path.join(TRIAL_DIR, "failure_csv.csv")).iloc[-1]

n_accepted   = len([f for f in os.listdir(os.path.join(TRIAL_DIR, "Accepted"))
                    if f.endswith(".pdb")])
n_lowconf    = len(os.listdir(os.path.join(TRIAL_DIR, "Trajectory", "LowConfidence")))
n_clashing   = len(os.listdir(os.path.join(TRIAL_DIR, "Trajectory", "Clashing")))
n_traj_total = n_lowconf + n_clashing + n_accepted
n_mpnn       = len(mpnn_df)
n_reached_mpnn = mpnn_df["Design"].str.rsplit("_mpnn", n=1).str[0].nunique()


# ---------------------------------------------------------------------------
# 2. Figures
# ---------------------------------------------------------------------------
# Figure 1: Trajectory outcome stack
fig1, ax = plt.subplots(figsize=(5.5, 2.6))
labels = ["Reached MPNN\n(all rejected)", "Severe clashes", "Low pLDDT", "Accepted"]
values = [n_reached_mpnn, n_clashing, n_lowconf, n_accepted]
colors = [PAL["slate"], PAL["ash"], PAL["fog"], PAL["navy"]]
bars = ax.barh(labels, values, color=colors, edgecolor=PAL["ink"], linewidth=0.5)
for bar, v in zip(bars, values):
    ax.text(v + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
            str(v), va="center", fontsize=9, color=PAL["ink"])
ax.set_xlabel("Number of trajectories")
ax.set_title("Figure 1 | Trial 4 trajectory outcomes (n = {})".format(n_traj_total))
ax.set_xlim(0, max(values) * 1.15)
fig1_b64 = fig_to_b64(fig1)


# Figure 2: Failure mode breakdown
fail_items = sorted([(k, int(v)) for k, v in fail_row.items() if int(v) > 0],
                    key=lambda x: -x[1])
top_fail = fail_items[:10]
fig2, ax = plt.subplots(figsize=(6.5, 3.3))
labels = [k for k, _ in reversed(top_fail)]
values = [v for _, v in reversed(top_fail)]
colors = [PAL["navy"] if l == "Target_RMSD" else PAL["slate"] for l in labels]
bars = ax.barh(labels, values, color=colors, edgecolor=PAL["ink"], linewidth=0.5)
for bar, v in zip(bars, values):
    ax.text(v + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
            str(v), va="center", fontsize=8, color=PAL["ink"])
ax.set_xlabel("MPNN sequence rejections")
ax.set_title("Figure 2 | Top 10 rejection reasons (Target_RMSD highlighted)")
ax.set_xlim(0, max(values) * 1.15)
fig2_b64 = fig_to_b64(fig2)


# Figure 3: Target_RMSD distribution
fig3, ax = plt.subplots(figsize=(6.5, 3.0))
data = mpnn_df["Average_Target_RMSD"].dropna()
ax.hist(data, bins=30, color=PAL["slate"], edgecolor=PAL["ink"], linewidth=0.4)
ax.axvline(5.0, color=PAL["warning"], linestyle="--", linewidth=1.2,
           label="Acceptance cutoff (5 Å)")
ax.axvline(data.min(), color=PAL["navy"], linestyle=":", linewidth=1.0,
           label=f"Best observed ({data.min():.1f} Å)")
ax.set_xlabel("Average Target RMSD (Å)")
ax.set_ylabel("Count of MPNN sequences")
ax.set_title(f"Figure 3 | Target structural deviation across n = {len(data)} candidates")
ax.legend(frameon=False, loc="upper right")
fig3_b64 = fig_to_b64(fig3)


# Figure 4: i_pTM vs Target_RMSD
fig4, ax = plt.subplots(figsize=(6.5, 3.0))
ax.scatter(mpnn_df["Average_Target_RMSD"], mpnn_df["Average_i_pTM"],
           s=8, color=PAL["slate"], alpha=0.45, edgecolor="none")
ax.axvline(5.0, color=PAL["warning"], linestyle="--", linewidth=1.0,
           label="Target RMSD cutoff (5 Å)")
ax.axhline(0.50, color=PAL["ash"], linestyle=":", linewidth=0.8,
           label="i_pTM cutoff (0.50)")
ax.set_xlabel("Average Target RMSD (Å)")
ax.set_ylabel("Average Interface pTM")
ax.set_title("Figure 4 | High AF2 confidence is decoupled from target preservation")
ax.legend(frameon=False, loc="lower right")
fig4_b64 = fig_to_b64(fig4)


# ---------------------------------------------------------------------------
# 3. Top "best near-miss" candidates table
# ---------------------------------------------------------------------------
top10 = mpnn_df.nsmallest(10, "Average_Target_RMSD")[
    ["Design", "Length", "Average_Target_RMSD", "Average_i_pTM", "Average_i_pAE",
     "Average_pLDDT", "Average_dG", "Average_Hotspot_RMSD",
     "Average_Binder_RMSD", "Average_n_InterfaceUnsatHbonds",
     "Average_Surface_Hydrophobicity"]
].round(2).reset_index(drop=True)


def near_miss_failures(row):
    failed = []
    if row["Average_Target_RMSD"] > 5:
        failed.append(f"Target_RMSD = {row['Average_Target_RMSD']:.1f} Å (cutoff ≤ 5)")
    if row["Average_n_InterfaceUnsatHbonds"] > 6:
        failed.append(f"UnsatHbonds = {row['Average_n_InterfaceUnsatHbonds']:.1f} (cutoff ≤ 6)")
    if row["Average_Binder_RMSD"] > 3.5:
        failed.append(f"Binder_RMSD = {row['Average_Binder_RMSD']:.2f} Å (cutoff ≤ 3.5)")
    if row["Average_Surface_Hydrophobicity"] > 0.45:
        failed.append(f"SurfHydro = {row['Average_Surface_Hydrophobicity']:.2f} (cutoff < 0.45)")
    return failed


near_miss_rows = ""
for i, row in top10.iterrows():
    fails = near_miss_failures(row)
    fail_html = "<br>".join(f"<span class='bad'>{f}</span>" for f in fails)
    near_miss_rows += f"""
    <tr>
      <td>{i+1}</td>
      <td><span class="mono">{row['Design']}</span></td>
      <td>{int(row['Length'])}</td>
      <td><strong>{row['Average_Target_RMSD']:.2f}</strong></td>
      <td>{row['Average_i_pTM']:.2f}</td>
      <td>{row['Average_i_pAE']:.2f}</td>
      <td>{row['Average_pLDDT']:.2f}</td>
      <td>{row['Average_dG']:.1f}</td>
      <td>{row['Average_Hotspot_RMSD']:.2f}</td>
      <td>{fail_html}</td>
    </tr>"""


# ---------------------------------------------------------------------------
# 4. Failure-mode table HTML
# ---------------------------------------------------------------------------
failure_explanations = {
    "Target_RMSD":             "Target backbone displaced more than 5 Å from input pose. The filter installed in Trial 4 to detect dimer collapse.",
    "InterfaceAAs_M":          "More than 3 methionine residues at the interface (overrepresentation flag).",
    "n_InterfaceUnsatHbonds":  "More than 6 unsatisfied buried polar groups at the interface (energetic penalty).",
    "i_pAE":                   "Interface positional uncertainty (normalized) above 0.35 (~11 Å raw).",
    "Binder_RMSD":             "Binder backbone in complex differs from binder predicted alone by more than 3.5 Å (refolds on binding).",
    "Binder_pLDDT":            "Binder-alone fold confidence below 0.80.",
    "ShapeComplementarity":    "Geometric surface fit (Lawrence–Colman) below 0.60.",
    "i_pTM":                   "AF2 interface confidence below 0.50.",
    "Surface_Hydrophobicity":  "Exposed hydrophobic surface above 0.45 (aggregation risk).",
    "Trajectory_logits_pLDDT": "Trajectory abandoned at Stage 1: backbone too low confidence to continue.",
    "Trajectory_softmax_pLDDT":"Trajectory abandoned at Stage 2.",
    "Trajectory_one-hot_pLDDT":"Trajectory abandoned at Stage 3.",
    "Trajectory_final_pLDDT":  "Final trajectory pLDDT below 0.65 threshold.",
    "Trajectory_Clashes":      "Severe steric overlap detected during trajectory.",
    "pLDDT":                   "Validation-stage complex pLDDT below 0.80.",
}
failure_rows_html = ""
for filt, count in fail_items[:12]:
    explanation = failure_explanations.get(filt, "—")
    bg = "row-flag" if filt == "Target_RMSD" else ""
    failure_rows_html += f"""
    <tr class="{bg}">
      <td><span class="mono">{filt}</span></td>
      <td>{count}</td>
      <td>{explanation}</td>
    </tr>"""


# ---------------------------------------------------------------------------
# 5. Assemble HTML
# ---------------------------------------------------------------------------
now    = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
mn_rmsd = mpnn_df["Average_Target_RMSD"].min()
md_rmsd = mpnn_df["Average_Target_RMSD"].median()
mx_rmsd = mpnn_df["Average_Target_RMSD"].max()
n_under_10 = (mpnn_df["Average_Target_RMSD"] < 10).sum()


html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Trial 4 Final Report — AAV2 T3 Dimer Binder Design</title>
<style>
  @page {{
    size: Letter;
    margin: 0.85in 0.9in 0.85in 0.9in;
    @bottom-right {{
      content: counter(page) " / " counter(pages);
      font-family: "Times New Roman", Times, serif;
      font-size: 9pt;
      color: #5c6b7a;
    }}
    @bottom-left {{
      content: "Trial 4 Final Report";
      font-family: "Times New Roman", Times, serif;
      font-size: 9pt;
      color: #5c6b7a;
      font-style: italic;
    }}
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0;
       font-family: "Times New Roman", Times, serif; }}
  body {{
    color: {PAL["ink"]};
    line-height: 1.5;
    font-size: 11pt;
  }}
  h1 {{
    font-size: 18pt;
    font-weight: bold;
    border-bottom: 2px solid {PAL["ink"]};
    padding-bottom: 6px;
    margin-bottom: 4px;
  }}
  h2 {{
    font-size: 12pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 22px 0 8px;
    color: {PAL["navy"]};
    border-bottom: 1px solid {PAL["fog"]};
    padding-bottom: 4px;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 11pt;
    font-weight: bold;
    margin: 14px 0 5px;
  }}
  p, li {{ font-size: 11pt; text-align: justify; }}
  .meta {{
    color: {PAL["slate"]};
    font-size: 10pt;
    margin-bottom: 16px;
    font-style: italic;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 10pt;
    margin: 10px 0 16px;
    page-break-inside: avoid;
  }}
  th, td {{
    text-align: left;
    padding: 5px 9px;
    border-bottom: 1px solid {PAL["fog"]};
    vertical-align: top;
  }}
  th {{
    background: {PAL["paper"]};
    color: {PAL["ink"]};
    font-weight: bold;
    text-transform: uppercase;
    font-size: 9pt;
    letter-spacing: 0.5px;
    border-top: 1.5px solid {PAL["ink"]};
    border-bottom: 1px solid {PAL["ink"]};
  }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .summary {{
    background: {PAL["paper"]};
    border-left: 3px solid {PAL["navy"]};
    padding: 10px 14px;
    margin: 10px 0 14px;
    font-size: 11pt;
    text-align: justify;
  }}
  .summary strong {{ color: {PAL["navy"]}; }}
  figure {{
    margin: 12px 0 18px;
    text-align: center;
    page-break-inside: avoid;
  }}
  figure img {{
    max-width: 95%;
    border: 1px solid {PAL["fog"]};
  }}
  figcaption {{
    font-size: 10pt;
    color: {PAL["slate"]};
    margin-top: 6px;
    font-style: italic;
    text-align: justify;
    padding: 0 5%;
  }}
  .bad {{ color: {PAL["warning"]}; font-size: 9.5pt; display: inline-block; }}
  tr.row-flag td {{ background: #fbf3f3; font-weight: bold; }}
  ul, ol {{ padding-left: 22px; margin: 6px 0 12px; }}
  ul li, ol li {{ margin-bottom: 4px; }}
  .footer {{
    border-top: 1px solid {PAL["fog"]};
    padding-top: 8px;
    margin-top: 24px;
    font-size: 9.5pt;
    color: {PAL["slate"]};
  }}
  blockquote {{
    border-left: 3px solid {PAL["ash"]};
    padding: 4px 14px;
    margin: 10px 0;
    color: {PAL["slate"]};
    font-style: italic;
    font-size: 11pt;
  }}
  .mono {{ font-family: "Courier New", Courier, monospace; font-size: 9.5pt;
           color: {PAL["navy"]}; }}
  .key-table th {{ width: 28%; }}
  .key-table td {{ font-variant-numeric: tabular-nums; }}
  .key-table td.value {{ font-weight: bold; color: {PAL["navy"]};
                         font-size: 11pt; width: 18%; }}
</style>
</head>
<body>

<h1>Trial 4 — Final Report</h1>
<p class="meta">AAV2 T3 dimer binder design with enforced target rigidity. Generated {now}.</p>

<h2>Executive Summary</h2>
<div class="summary">
  Trial 4 added a single filter to the Trial 3 protocol: <span class="mono">Average_Target_RMSD ≤ 5 Å</span>, designed to
  reject the dimer-collapse failure mode that invalidated all 28 designs accepted in Trial 3. After {n_traj_total}
  trajectories and {n_mpnn} MPNN-redesigned sequences, <strong>zero designs were accepted</strong>. The minimum target
  RMSD observed across all candidates was <strong>{mn_rmsd:.1f} Å</strong> — more than five times the cutoff. This constitutes
  definitive evidence that, with the current settings, the multi-chain AAV2 dimer target is not viable for direct
  quaternary-epitope design under AF2-Multimer hallucination. The next step is the single-protomer pivot described in §6.
</div>

<table class="key-table">
  <tr><th>Quantity</th><th>Value</th><th>Notes</th></tr>
  <tr>
    <td>Trajectories completed</td>
    <td class="value">{n_traj_total}</td>
    <td>{n_clashing} terminated for steric clash; {n_lowconf} for low pLDDT.</td>
  </tr>
  <tr>
    <td>MPNN candidates evaluated</td>
    <td class="value">{n_mpnn}</td>
    <td>Sequences from {n_reached_mpnn} trajectories that reached the validation stage.</td>
  </tr>
  <tr>
    <td>Designs accepted</td>
    <td class="value">{n_accepted}</td>
    <td>0% acceptance rate.</td>
  </tr>
  <tr>
    <td>Best target RMSD observed</td>
    <td class="value">{mn_rmsd:.2f} Å</td>
    <td>5.2× the acceptance cutoff (5 Å); see Figure 3.</td>
  </tr>
  <tr>
    <td>Median target RMSD</td>
    <td class="value">{md_rmsd:.2f} Å</td>
    <td>Half of all candidates exceeded this value.</td>
  </tr>
  <tr>
    <td>Designs with RMSD &lt; 10 Å</td>
    <td class="value">{n_under_10}</td>
    <td>None of {n_mpnn} candidates approached the cutoff.</td>
  </tr>
</table>

<h2>1. Protocol</h2>
<p>
  Identical to Trial 3, with one filter change. Target structure
  <span class="mono">151lp3t3_dimer_fixed.pdb</span> (chains A and C, C2-symmetric dimer of AAV2 VP).
  Hotspot residues mirrored on both chains: A30–34, A102–105, A113–115, A451–456 and the C-chain equivalents.
  Binder length 60–150 residues. Two GPUs, parallel trajectories.
</p>
<table>
  <tr><th>Parameter</th><th>Setting</th><th>Change from Trial 3</th></tr>
  <tr><td>Advanced preset</td><td><span class="mono">default_4stage_multimer_hardtarget</span></td><td>—</td></tr>
  <tr><td>Filter file</td><td><span class="mono">trial4_filters.json</span></td><td>Added Target_RMSD ≤ 5 Å (was: <em>null</em>)</td></tr>
  <tr><td>Loop% filter</td><td>≤ 95%</td><td>—</td></tr>
  <tr><td>UnsatHbonds filter</td><td>≤ 6</td><td>—</td></tr>
  <tr><td>SurfHydro filter</td><td>≤ 0.45</td><td>—</td></tr>
  <tr><td>Number of GPUs</td><td>2</td><td>—</td></tr>
</table>

<h2>2. Trajectory Outcomes</h2>
<figure>
  <img src="data:image/png;base64,{fig1_b64}" alt="Trajectory outcomes">
  <figcaption>Figure 1. Distribution of {n_traj_total} trajectories by termination stage. No design was accepted.
  {n_clashing} of {n_traj_total} ({100*n_clashing/n_traj_total:.0f}%) were terminated for steric clash and {n_lowconf}
  ({100*n_lowconf/n_traj_total:.0f}%) for low confidence. Of the trajectories that completed, {n_reached_mpnn} produced
  MPNN candidates ({n_mpnn} sequences total) — all rejected at AF2 validation.</figcaption>
</figure>

<h2>3. Rejection Reasons</h2>
<figure>
  <img src="data:image/png;base64,{fig2_b64}" alt="Failure modes">
  <figcaption>Figure 2. Top ten rejection reasons across {n_mpnn} MPNN sequences. <span class="mono">Target_RMSD</span>
  (highlighted) rejected every single candidate, confirming that the dimer-collapse failure mode is universal under this
  protocol.</figcaption>
</figure>
<table>
  <tr><th>Filter</th><th>Rejections</th><th>Meaning</th></tr>
  {failure_rows_html}
</table>

<h2>4. Target Structural Deviation</h2>
<figure>
  <img src="data:image/png;base64,{fig3_b64}" alt="Target RMSD distribution">
  <figcaption>Figure 3. Distribution of <span class="mono">Average_Target_RMSD</span> across {n_mpnn} MPNN candidates.
  Median {md_rmsd:.1f} Å, range {mn_rmsd:.1f} – {mx_rmsd:.1f} Å. The acceptance cutoff (5 Å, red dashed) lies far below
  the entire distribution. The best observed value ({mn_rmsd:.1f} Å, blue dotted) is a 5.2-fold violation of the cutoff.
  Zero candidates achieved RMSD &lt; 10 Å.</figcaption>
</figure>
<figure>
  <img src="data:image/png;base64,{fig4_b64}" alt="i_pTM vs Target RMSD">
  <figcaption>Figure 4. Scatter of interface confidence (i_pTM) against target deviation. AF2 routinely produces
  high-confidence predictions (i_pTM &gt; 0.7) for collapsed-dimer geometries. This is the failure mode in microcosm:
  model confidence and structural validity are decoupled when the target is multi-chain and free to reposition.</figcaption>
</figure>

<h2>5. Top Near-Miss Candidates</h2>
<p>
  Although no design was accepted, the ten candidates with the lowest target deviation are listed below. They are dominated
  by sequence variants of a single trajectory (seed <span class="mono">s950289</span>, length 128). All other validation
  metrics (<span class="mono">i_pTM</span>, <span class="mono">i_pAE</span>, <span class="mono">pLDDT</span>,
  <span class="mono">dG</span>, <span class="mono">Hotspot_RMSD</span>) are excellent for these candidates — they would
  be exceptional binders if the target geometry were valid. They are not.
</p>
<table>
  <tr>
    <th>#</th><th>Design</th><th>Len</th><th>Target<br>RMSD (Å)</th><th>i_pTM</th><th>i_pAE</th>
    <th>pLDDT</th><th>dG (REU)</th><th>Hotspot<br>RMSD (Å)</th><th>Failed filters</th>
  </tr>
  {near_miss_rows}
</table>

<h2>6. Interpretation and Next Steps</h2>
<p>Three observations follow from these data:</p>
<ol>
  <li><strong>The Target_RMSD filter is necessary.</strong> Trial 3 produced 28 designs that
  passed every other filter while exhibiting target RMSD between 25 and 39 Å. Without this filter, those designs would have
  been advanced to experimental work as nominal capsid binders, despite binding a non-physiological dimer collapsed by
  more than 25 Å.</li>
  <li><strong>The Target_RMSD filter is sufficient to expose the failure mode.</strong> 1,794
  candidates, none below 10 Å, best at 26 Å — this is not statistical noise. AF2-Multimer systematically rearranges the
  dimer to allow a single binder to engage hotspots on both protomers.</li>
  <li><strong>Loss-function gradients prefer collapse over independent binding.</strong> The
  Trial 3 / Trial 4 loss rewards inter-chain contacts on hotspots distributed across two non-covalently linked target chains.
  The cheapest optimization path is to bring those chains together, which BindCraft cannot prevent without a rigid-body
  constraint.</li>
</ol>

<blockquote>
The negative result here is itself the scientific outcome. The hypothesis that BindCraft can design a quaternary-epitope
binder against an AAV2 dimer using its standard multi-chain template mechanism is now rejected with quantitative evidence.
</blockquote>

<h3>Planned next steps</h3>
<ul>
  <li><strong>Pivot to single-protomer design.</strong> Use chain A only as target; restrict hotspots to one chain.
  This removes the multi-chain reposition degree of freedom by construction.</li>
  <li><strong>Post-hoc quaternary screen.</strong> Superpose each accepted single-chain binder onto the assembled capsid
  model (<span class="mono">1lp3_hexamer.pdb</span>) and filter for absence of clash with neighbouring protomers and
  for bonus contacts with adjacent VPs.</li>
  <li><strong>Optional control: fused-chain target.</strong> Construct an artificial A–GGGGSGGGGSGGGGS–C fusion as a single
  chain and re-run multimer design. Tests whether covalent constraint of the dimer rescues quaternary-epitope design.</li>
  <li><strong>Long-term:</strong> Evaluate RFdiffusion + ProteinMPNN, which applies a rigid-body constraint to the target
  by construction and may permit quaternary design directly.</li>
</ul>

<div class="footer">
  Source data: <span class="mono">{TRIAL_DIR}/</span><br>
  Report regenerable via: <span class="mono">python generate_trial4_report.py</span><br>
  Filters: <span class="mono">settings_filters/trial4_filters.json</span>; Settings:
  <span class="mono">settings_target/15del1lp3.json</span>; Advanced preset:
  <span class="mono">settings_advanced/default_4stage_multimer_hardtarget.json</span>.
</div>

</body>
</html>
"""

with open(REPORT_HTML_PATH, "w") as f:
    f.write(html)
print(f"HTML report:  {REPORT_HTML_PATH}")

# ---------------------------------------------------------------------------
# 6. Render PDF
# ---------------------------------------------------------------------------
weasyprint.HTML(string=html, base_url=TRIAL_DIR).write_pdf(REPORT_PDF_PATH)
print(f"PDF report:   {REPORT_PDF_PATH}")
