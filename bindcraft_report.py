#!/usr/bin/env python
"""
BindCraft Run Status Report Generator
======================================
Generates a self-contained HTML report with plots for a BindCraft run.

Usage:
    # Activate your BindCraft conda env first:
    conda activate BindCraft

    # Basic usage — point to the output directory:
    python bindcraft_report.py --output_dir ./aav_monomer/output

    # Specify custom log files if they're not in the output dir:
    python bindcraft_report.py --output_dir ./aav_monomer/output \
        --logs ./aav_monomer/output/run_log_gpu0.txt ./aav_monomer/output/run_log_gpu1.txt

    # Custom report filename:
    python bindcraft_report.py --output_dir ./aav_monomer/output --report_name my_report.html

    The HTML report is saved in the output directory by default.
"""

import argparse
import base64
import glob
import io
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Parse log files — extract per-iteration metrics and stage boundaries
# ---------------------------------------------------------------------------
def parse_log(filepath):
    """Parse a single BindCraft log file. Returns a list of design dicts."""
    designs = []
    current_design = None
    iterations = []
    stage = None

    with open(filepath) as f:
        for line in f:
            line = line.strip()

            # Detect stage transitions
            if "Stage 1: Test Logits" in line or "Stage 1: Additional Logits" in line:
                if current_design and iterations:
                    current_design["iterations"] = iterations
                    designs.append(current_design)
                current_design = {"stage_reached": 1, "outcome": None, "file": filepath}
                iterations = []
                stage = 1
            elif "Stage 2:" in line:
                stage = 2
                if current_design:
                    current_design["stage_reached"] = 2
            elif "Stage 3:" in line:
                stage = 3
                if current_design:
                    current_design["stage_reached"] = 3
            elif "Stage 4:" in line:
                stage = 4
                if current_design:
                    current_design["stage_reached"] = 4

            # Parse iteration lines: "N models [M] recycles ..."
            m = re.match(
                r"(\d+)\s+models\s+\[(\d+)\]\s+recycles\s+(\d+)\s+hard\s+(\d+)\s+soft\s+([\d.]+)"
                r"\s+temp\s+([\d.]+)\s+loss\s+([\d.]+)\s+helix\s+([\d.-]+)"
                r"\s+pae\s+([\d.]+)\s+i_pae\s+([\d.]+)\s+con\s+([\d.]+)\s+i_con\s+([\d.]+)"
                r"\s+plddt\s+([\d.]+)\s+ptm\s+([\d.]+)\s+i_ptm\s+([\d.]+)\s+rg\s+([\d.-]+)",
                line,
            )
            if m:
                iterations.append({
                    "iter": int(m.group(1)),
                    "model": int(m.group(2)),
                    "recycles": int(m.group(3)),
                    "loss": float(m.group(7)),
                    "plddt": float(m.group(13)),
                    "ptm": float(m.group(14)),
                    "i_ptm": float(m.group(15)),
                    "i_pae": float(m.group(10)),
                    "pae": float(m.group(9)),
                    "stage": stage,
                })

            # Detect outcomes
            if "pLDDT too low" in line:
                if current_design:
                    current_design["outcome"] = "LowConfidence"
            elif "Severe clashes" in line:
                if current_design:
                    current_design["outcome"] = "Clashing"
            elif "No accepted MPNN" in line:
                if current_design:
                    current_design["outcome"] = "MPNN_Failed"
            elif "Accepted" in line and "MPNN" not in line and "skipping" not in line:
                if current_design:
                    current_design["outcome"] = "Accepted"

    # Don't forget the last design
    if current_design and iterations:
        current_design["iterations"] = iterations
        designs.append(current_design)

    return designs


# ---------------------------------------------------------------------------
# 2. Parse failure CSV
# ---------------------------------------------------------------------------
def parse_failure_csv(filepath):
    """Parse failure_csv.csv and return a dict of failure counts."""
    df = pd.read_csv(filepath)
    if df.empty:
        return {}
    row = df.iloc[-1]  # latest row
    return row.to_dict()


# ---------------------------------------------------------------------------
# 3. Count trajectory files on disk
# ---------------------------------------------------------------------------
def count_trajectories(output_dir):
    """Count PDB files in each Trajectory subfolder."""
    traj_dir = os.path.join(output_dir, "Trajectory")
    counts = {}
    if os.path.isdir(traj_dir):
        for sub in sorted(os.listdir(traj_dir)):
            subpath = os.path.join(traj_dir, sub)
            if os.path.isdir(subpath):
                pdbs = glob.glob(os.path.join(subpath, "*.pdb"))
                counts[sub] = len(pdbs)
    return counts


def count_accepted(output_dir):
    """Count accepted designs (PDBs in Accepted/Ranked/)."""
    ranked = os.path.join(output_dir, "Accepted", "Ranked")
    if os.path.isdir(ranked):
        return len(glob.glob(os.path.join(ranked, "*.pdb")))
    return 0


# ---------------------------------------------------------------------------
# 4. Plot helpers — each returns a base64-encoded PNG string
# ---------------------------------------------------------------------------
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="#1e1e1e")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def style_ax(ax, title, xlabel, ylabel):
    """Apply dark theme to axes."""
    ax.set_facecolor("#2b2b2b")
    ax.set_title(title, color="white", fontsize=13, fontweight="bold")
    ax.set_xlabel(xlabel, color="#cccccc")
    ax.set_ylabel(ylabel, color="#cccccc")
    ax.tick_params(colors="#999999")
    for spine in ax.spines.values():
        spine.set_color("#555555")
    ax.grid(True, alpha=0.2, color="#666666")


def plot_failure_breakdown(failures):
    """Pie chart of where designs fail in the pipeline."""
    labels_map = {
        "Trajectory_logits_pLDDT": "Low pLDDT\n(Logits)",
        "Trajectory_softmax_pLDDT": "Low pLDDT\n(Softmax)",
        "Trajectory_one-hot_pLDDT": "Low pLDDT\n(One-hot)",
        "Trajectory_Clashes": "Clashing",
        "Trajectory_WrongHotspot": "Wrong\nHotspot",
    }
    labels, sizes = [], []
    for key, label in labels_map.items():
        val = failures.get(key, 0)
        if val > 0:
            labels.append(label)
            sizes.append(val)

    # MPNN failures = i_pTM failures (proxy for all MPNN-stage AF2 failures)
    mpnn_fail = failures.get("i_pTM", 0)
    if mpnn_fail > 0:
        labels.append("MPNN AF2\nFilter Fail")
        sizes.append(mpnn_fail)

    if not sizes:
        return None

    colors = ["#ff6b6b", "#ffa502", "#ff7979", "#e74c3c", "#d35400", "#8e44ad"]
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#1e1e1e")
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct="%1.0f%%",
        colors=colors[: len(sizes)],
        textprops={"color": "white", "fontsize": 10},
        pctdistance=0.8,
    )
    for t in autotexts:
        t.set_fontsize(9)
        t.set_color("white")
    ax.set_title("Failure Breakdown", color="white", fontsize=14, fontweight="bold")
    return fig_to_base64(fig)


def plot_trajectory_outcomes(traj_counts, n_accepted):
    """Bar chart of trajectory outcomes."""
    labels = list(traj_counts.keys()) + (["Accepted"] if n_accepted > 0 else [])
    values = list(traj_counts.values()) + ([n_accepted] if n_accepted > 0 else [])

    if not values:
        return None

    color_map = {
        "LowConfidence": "#ff6b6b",
        "Clashing": "#ffa502",
        "Accepted": "#2ecc71",
    }
    colors = [color_map.get(l, "#3498db") for l in labels]

    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor("#1e1e1e")
    bars = ax.bar(labels, values, color=colors, edgecolor="#444444")
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(val), ha="center", color="white", fontsize=11, fontweight="bold")
    style_ax(ax, "Trajectory Outcomes", "", "Count")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    return fig_to_base64(fig)


def plot_loss_over_time(designs, gpu_label):
    """Line plot of loss over iterations for recent designs from one GPU."""
    if not designs:
        return None

    # Show last 6 designs
    recent = designs[-6:]
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#1e1e1e")

    cmap = plt.cm.viridis
    for i, d in enumerate(recent):
        iters = d.get("iterations", [])
        if not iters:
            continue
        xs = [it["iter"] for it in iters]
        ys = [it["loss"] for it in iters]
        outcome = d.get("outcome", "?")
        color = cmap(i / max(len(recent) - 1, 1))
        ax.plot(xs, ys, color=color, alpha=0.8, linewidth=1.2, label=f"#{len(designs)-len(recent)+i+1} ({outcome})")

    style_ax(ax, f"Loss Trajectories — {gpu_label} (last {len(recent)} designs)", "Iteration", "Loss")
    ax.legend(fontsize=7, facecolor="#2b2b2b", edgecolor="#555555", labelcolor="white", loc="upper right")
    return fig_to_base64(fig)


def plot_key_metrics_over_time(designs, gpu_label):
    """Plot pLDDT and i_pTM over iterations for recent designs."""
    if not designs:
        return None

    recent = designs[-6:]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor("#1e1e1e")

    cmap = plt.cm.viridis
    for i, d in enumerate(recent):
        iters = d.get("iterations", [])
        if not iters:
            continue
        xs = [it["iter"] for it in iters]
        color = cmap(i / max(len(recent) - 1, 1))
        label = f"#{len(designs)-len(recent)+i+1}"

        axes[0].plot(xs, [it["plddt"] for it in iters], color=color, alpha=0.8, linewidth=1.2, label=label)
        axes[1].plot(xs, [it["i_ptm"] for it in iters], color=color, alpha=0.8, linewidth=1.2, label=label)

    # Add threshold lines
    axes[0].axhline(y=0.8, color="#2ecc71", linestyle="--", alpha=0.5, label="Filter (0.8)")
    axes[1].axhline(y=0.5, color="#2ecc71", linestyle="--", alpha=0.5, label="Filter (0.5)")

    style_ax(axes[0], f"pLDDT — {gpu_label}", "Iteration", "pLDDT")
    style_ax(axes[1], f"i_pTM — {gpu_label}", "Iteration", "i_pTM")
    for ax in axes:
        ax.legend(fontsize=7, facecolor="#2b2b2b", edgecolor="#555555", labelcolor="white")

    fig.tight_layout()
    return fig_to_base64(fig)


def plot_stage_distribution(designs):
    """Bar chart: how many designs reached each stage."""
    stage_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for d in designs:
        s = d.get("stage_reached", 1)
        stage_counts[s] = stage_counts.get(s, 0) + 1

    labels = [f"Stage {s}" for s in sorted(stage_counts)]
    values = [stage_counts[s] for s in sorted(stage_counts)]
    colors = ["#e74c3c", "#f39c12", "#3498db", "#2ecc71"]

    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor("#1e1e1e")
    bars = ax.bar(labels, values, color=colors, edgecolor="#444444")
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(val), ha="center", color="white", fontsize=11, fontweight="bold")
    style_ax(ax, "Designs by Furthest Stage Reached", "", "Count")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    return fig_to_base64(fig)


# ---------------------------------------------------------------------------
# 5. HTML generation
# ---------------------------------------------------------------------------
def generate_html(output_dir, log_files, report_path):
    """Main function: gather data, create plots, write HTML."""

    # --- Gather data ---
    failure_csv = os.path.join(output_dir, "failure_csv.csv")
    failures = parse_failure_csv(failure_csv) if os.path.exists(failure_csv) else {}
    traj_counts = count_trajectories(output_dir)
    n_accepted = count_accepted(output_dir)

    # Parse logs per GPU
    gpu_designs = {}
    for lf in log_files:
        label = os.path.basename(lf).replace(".txt", "").replace("run_log_", "").upper()
        gpu_designs[label] = parse_log(lf)

    all_designs = []
    for ds in gpu_designs.values():
        all_designs.extend(ds)

    total_attempts = sum(len(ds) for ds in gpu_designs.values())
    mpnn_reached = sum(1 for d in all_designs if d.get("outcome") == "MPNN_Failed")
    mpnn_seqs_failed = failures.get("i_pTM", 0)

    # --- Build stats CSV path ---
    stats_csv = os.path.join(output_dir, "final_design_stats.csv")
    has_stats = os.path.exists(stats_csv) and os.path.getsize(stats_csv) > 0

    # --- Generate plots ---
    plots = {}
    plots["failure_pie"] = plot_failure_breakdown(failures)
    plots["traj_outcomes"] = plot_trajectory_outcomes(traj_counts, n_accepted)
    plots["stage_dist"] = plot_stage_distribution(all_designs)
    for label, designs in gpu_designs.items():
        plots[f"loss_{label}"] = plot_loss_over_time(designs, label)
        plots[f"metrics_{label}"] = plot_key_metrics_over_time(designs, label)

    # --- Assemble HTML ---
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build plot sections
    plot_sections = ""
    if plots.get("failure_pie"):
        plot_sections += f'<div class="plot"><img src="data:image/png;base64,{plots["failure_pie"]}"></div>\n'
    if plots.get("traj_outcomes"):
        plot_sections += f'<div class="plot"><img src="data:image/png;base64,{plots["traj_outcomes"]}"></div>\n'
    if plots.get("stage_dist"):
        plot_sections += f'<div class="plot"><img src="data:image/png;base64,{plots["stage_dist"]}"></div>\n'

    for label in gpu_designs:
        if plots.get(f"loss_{label}"):
            plot_sections += f'<div class="plot wide"><img src="data:image/png;base64,{plots[f"loss_{label}"]}"></div>\n'
        if plots.get(f"metrics_{label}"):
            plot_sections += f'<div class="plot wide"><img src="data:image/png;base64,{plots[f"metrics_{label}"]}"></div>\n'

    # Failure table rows
    key_failures = [
        ("Trajectory_logits_pLDDT", "Low pLDDT at Logits stage"),
        ("Trajectory_softmax_pLDDT", "Low pLDDT at Softmax stage"),
        ("Trajectory_one-hot_pLDDT", "Low pLDDT at One-hot stage"),
        ("Trajectory_final_pLDDT", "Low final trajectory pLDDT"),
        ("Trajectory_Clashes", "Severe steric clashes"),
        ("Trajectory_WrongHotspot", "Binder on wrong hotspot"),
        ("pLDDT", "MPNN seq failed pLDDT filter"),
        ("i_pTM", "MPNN seq failed i_pTM filter"),
        ("i_pAE", "MPNN seq failed i_pAE filter"),
    ]
    failure_rows = ""
    for key, desc in key_failures:
        val = int(failures.get(key, 0))
        if val > 0:
            failure_rows += f"<tr><td>{desc}</td><td>{val}</td></tr>\n"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BindCraft Report — {os.path.basename(output_dir)}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #121212; color: #e0e0e0; font-family: 'Segoe UI', system-ui, sans-serif; padding: 20px; }}
    h1 {{ color: #ffffff; margin-bottom: 5px; font-size: 24px; }}
    h2 {{ color: #bbbbbb; margin: 30px 0 15px; font-size: 18px; border-bottom: 1px solid #333; padding-bottom: 8px; }}
    .meta {{ color: #888; font-size: 13px; margin-bottom: 25px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 30px; }}
    .card {{ background: #1e1e1e; border-radius: 10px; padding: 20px; text-align: center; border: 1px solid #333; }}
    .card .value {{ font-size: 36px; font-weight: bold; margin-bottom: 5px; }}
    .card .label {{ font-size: 12px; color: #999; text-transform: uppercase; letter-spacing: 1px; }}
    .green {{ color: #2ecc71; }}
    .red {{ color: #e74c3c; }}
    .yellow {{ color: #f1c40f; }}
    .blue {{ color: #3498db; }}
    .plots {{ display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; }}
    .plot {{ background: #1e1e1e; border-radius: 10px; padding: 10px; border: 1px solid #333; }}
    .plot img {{ max-width: 100%; height: auto; border-radius: 6px; }}
    .plot.wide {{ flex-basis: 100%; }}
    table {{ width: 100%; border-collapse: collapse; background: #1e1e1e; border-radius: 10px; overflow: hidden; margin-bottom: 20px; }}
    th {{ background: #2b2b2b; color: #ccc; padding: 10px 15px; text-align: left; font-size: 12px; text-transform: uppercase; }}
    td {{ padding: 10px 15px; border-top: 1px solid #2b2b2b; font-size: 14px; }}
    tr:hover {{ background: #252525; }}
</style>
</head>
<body>
<h1>BindCraft Run Report</h1>
<p class="meta">Output: {output_dir} &nbsp;|&nbsp; Generated: {now}</p>

<div class="cards">
    <div class="card"><div class="value {'green' if n_accepted > 0 else 'red'}">{n_accepted}</div><div class="label">Accepted Designs</div></div>
    <div class="card"><div class="value blue">{total_attempts}</div><div class="label">Total Attempts</div></div>
    <div class="card"><div class="value yellow">{mpnn_reached}</div><div class="label">Reached MPNN</div></div>
    <div class="card"><div class="value red">{mpnn_seqs_failed}</div><div class="label">MPNN Seqs Failed AF2</div></div>
    <div class="card"><div class="value blue">{len(gpu_designs)}</div><div class="label">Active GPUs</div></div>
    <div class="card"><div class="value">{'%.1f' % (100*n_accepted/total_attempts) if total_attempts else 0}%</div><div class="label">Acceptance Rate</div></div>
</div>

<h2>Failure Breakdown</h2>
<table>
<tr><th>Failure Reason</th><th>Count</th></tr>
{failure_rows}
</table>

<h2>Plots</h2>
<div class="plots">
{plot_sections}
</div>

</body>
</html>"""

    with open(report_path, "w") as f:
        f.write(html)
    print(f"Report saved to: {report_path}")


# ---------------------------------------------------------------------------
# 6. CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate BindCraft run status report.")
    parser.add_argument("--output_dir", "-o", required=True,
                        help="Path to the BindCraft output directory (contains failure_csv.csv, Trajectory/, etc.)")
    parser.add_argument("--logs", "-l", nargs="+", default=None,
                        help="Paths to log files. If not given, looks for run_log_gpu*.txt in output_dir.")
    parser.add_argument("--report_name", "-r", default=None,
                        help="Output HTML filename. Default: report_YYYYMMDD_HHMMSS.html in the output dir.")
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)

    # Auto-discover log files if not specified
    if args.logs:
        log_files = [os.path.abspath(l) for l in args.logs]
    else:
        log_files = sorted(glob.glob(os.path.join(output_dir, "run_log_gpu*.txt")))
        if not log_files:
            print("No log files found. Use --logs to specify them.")
            sys.exit(1)

    # Report path
    if args.report_name:
        report_path = os.path.join(output_dir, args.report_name)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(output_dir, f"report_{ts}.html")

    print(f"Parsing {len(log_files)} log file(s)...")
    for lf in log_files:
        print(f"  - {lf}")

    generate_html(output_dir, log_files, report_path)
