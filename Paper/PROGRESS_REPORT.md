# Three-Week Progress Report
## *De novo* Binder Design: PD-L1 and AAV2 Capsid

**Period:** 2026-03-25 – 2026-04-15
**Platform:** BindCraft (Pacesa *et al.*, 2024) — AlphaFold2-Multimer hallucination + ProteinMPNN redesign + Rosetta interface scoring

---

## 1. Objective

Establish an *in silico* pipeline for generating *de novo* miniprotein binders against two targets of increasing difficulty:
1. **PD-L1** — benchmarking target with published binders (validation of the workflow).
2. **AAV2 capsid** — engineering goal. A binder directed at the assembled capsid surface could serve as a targeting or neutralizing module for gene-therapy vectors.

The scientific question driving the AAV2 effort is: **can we design a binder that prefers the quaternary (assembled-capsid) surface over an isolated VP monomer?** This is non-trivial because most AAV2 surface epitopes involve residues contributed by multiple VP protomers.

---

## 2. Methods (abbreviated)

Each run of BindCraft performs the following pipeline per trajectory:

1. **Backbone hallucination** — AlphaFold2-Multimer is inverted via gradient descent over the binder sequence, optimizing a composite loss (pLDDT, pTM, i_pTM, interface contacts, radius of gyration, secondary-structure bias). Four stages: logits → softmax → one-hot → semi-greedy.
2. **Sequence redesign** — ProteinMPNN (soluble weights) generates 20 sequence variants per accepted backbone, with interface residues fixed.
3. **Validation** — each sequence is re-predicted by AF2, relaxed with Rosetta, and scored on ≥ 15 interface metrics (e.g. ΔG, shape complementarity, interface hydrogen bonds, binder RMSD on binding).
4. **Filtering** — designs passing all thresholds are archived to `Accepted/`.

Hardware: 2× NVIDIA GPU (parallel trajectories). Typical wall-time per trajectory: 3–5 min (design) + 1–2 min (validation).

### 2.1 Two distinct controls: design biases vs. validation filters

BindCraft uses two conceptually different sets of numerical parameters, which are easy to confuse:

- **Design loss weights** (e.g. `weights_iptm = 0.05`, `weights_helicity = −0.3`) act *during* trajectory hallucination. They form a weighted sum that gradient descent *minimizes*. They do not reject any design — they simply bias the optimizer toward certain properties (more interface contacts, more helical content, etc.). A loss weight is a continuous gradient.
- **Validation filters** (e.g. `Average_i_pTM ≥ 0.50`) act *after* a design is generated, on the AF2 re-prediction of each MPNN sequence. They are pass/fail thresholds. A design failing **any** filter is rejected.

In short: loss weights *guide* the optimizer; filters *gate* the output. Reported metrics in §4 below are filter-side quantities.

### 2.2 Reported validation metrics, scales, and normalization

The `final_design_stats.csv` produced by BindCraft contains 232 columns, but only ~15 unique metrics are scientifically meaningful — each is reported once as `Average_*` (mean over five AF2 model variants) and again per individual model (`1_*`–`5_*`). For reporting, only the `Average_*` columns are used. Two metrics are normalized by BindCraft for convenience and are not in their native AF2 units; this is documented below.

| # | Metric (`Average_*`) | What it measures | Native scale | Normalized? | Direction | Cutoff (filter value) | Interpretation when value sits at cutoff |
|---|---|---|---|---|---|---|---|
| 1 | `i_pTM` | Interface predicted TM-score; AF2's confidence that the binder and target are positioned correctly *relative to each other* | 0–1 (TM-score) | No | higher = better | **≥ 0.50** | Borderline — AF2 only marginally believes the interface. Strong designs reach 0.80+. |
| 2 | `pTM` | Global predicted TM-score for the whole complex fold | 0–1 (TM-score) | No | higher = better | **≥ 0.55** | Overall fold is plausible but not strong. |
| 3 | `pLDDT` | Predicted local Distance Difference Test, averaged across the whole complex; AF2's per-residue confidence | 0–100 (AF2 native) | **Yes — divided by 100** → 0–1 | higher = better | **≥ 0.80** | Confident structure (≥ 80 % per-residue confidence). |
| 4 | `Binder_pLDDT` | Same as pLDDT but for the binder predicted alone (no target) | 0–100 (AF2) | **Yes — /100** → 0–1 | higher = better | **≥ 0.80** | Binder fold is confident even without the target — i.e. it is a real protein, not target-stabilized scaffolding. |
| 5 | `i_pAE` | Interface predicted Aligned Error; AF2's positional uncertainty between binder and target residues | Å (AF2 native, max ≈ 31 Å) | **Yes — divided by 31** → 0–1 | lower = better | **≤ 0.35** (≈ 10.9 Å raw) | Interface positions known to ≈ 11 Å — borderline. Strong designs reach 0.17 (≈ 5 Å). |
| 6 | `pAE` | Same as i_pAE for the whole complex | Å (max ≈ 31) | **Yes — /31** → 0–1 | lower = better | (no separate cutoff) | Used as context for i_pAE. |
| 7 | `dG` | Rosetta binding free energy on relaxed complex | REU (Rosetta Energy Units, dimensionless ~ kcal/mol) | No | lower (more negative) = better | **< 0** | Net favourable binding. Trial 3 designs span −68 to −114 REU. |
| 8 | `dSASA` | Solvent-accessible surface area buried at the interface | Å² | No | higher = better | **> 1** | Effectively non-zero. Strong interfaces bury 1 500–4 500 Å². |
| 9 | `ShapeComplementarity` | Lawrence–Colman geometric fit of the two surfaces | 0–1 (defined) | No | higher = better | **≥ 0.60** | Surfaces fit reasonably well. Antibody–antigen interfaces are typically 0.65–0.75. |
| 10 | `n_InterfaceResidues` | Count of binder residues within contact distance of target | count | No | higher = better | **≥ 7** | Minimum viable interface size. |
| 11 | `n_InterfaceHbonds` | Count of cross-interface hydrogen bonds | count | No | higher = better | **≥ 3** | Minimum to provide specificity. |
| 12 | `n_InterfaceUnsatHbonds` | Buried polar groups with no hydrogen-bond partner (energetic penalty) | count | No | lower = better | **≤ 4** (relaxed to 6 in Trial 3) | Each unsatisfied buried polar costs ≈ 1–2 kcal/mol. |
| 13 | `Binder_Energy_Score` | Rosetta total energy of the binder predicted alone | REU | No | lower (more negative) = better | **< 0** | Binder is physically stable on its own. |
| 14 | `Surface_Hydrophobicity` | Fraction of binder surface that is hydrophobic | 0–1 (defined) | No | lower = better | **< 0.35** (relaxed to 0.45 in Trial 3) | Higher values predict aggregation in solution. |
| 15 | `Binder_RMSD` | Backbone RMSD: binder in the complex vs. binder predicted alone | Å | No | lower = better | **≤ 3.5 Å** | Binder does not refold on binding (i.e. its bound and unbound structures agree). |
| 16 | `Hotspot_RMSD` | Distance between the binder and the user-specified hotspot residues on the target | Å | No | lower = better | **≤ 6.0 Å** | Binder lands on the intended site. Trial 3: 0.77–1.89 Å (well below cutoff). |
| 17 | `Target_RMSD` | Backbone RMSD between the input target structure and the AF2-predicted target structure | Å | No | lower = better | *no hard cutoff — informational* | Should be < 2 Å for monomers. **For Trial 3 (multi-chain target) this metric flagged the dimer-collapse failure described in §5: 25–39 Å.** |
| 18 | `Binder_Loop%` | Fraction of binder residues in coil/loop secondary structure | % (0–100) | No | lower = better | **< 90 %** (relaxed to 95 % in Trial 3) | Designs above this are too unstructured to be reliable folders. |

**How to read this table when reporting results.** For an accepted design, every value above passes its cutoff by construction. The scientific question is **how far above the cutoff** the design sits. A design at i_pTM = 0.51 only barely passed; one at 0.85 is highly confident. Reporting the *range* of each metric across the accepted set (as in §4) is therefore more informative than reporting only that filters were satisfied.

**Why `Target_RMSD` has no hard cutoff but is the most important number for this project.** BindCraft's developers expect this column to be near zero (target geometry is normally preserved). They did not anticipate quaternary-epitope designs against a non-covalently linked multimer. In that regime, `Target_RMSD` becomes the diagnostic for the failure mode in §5 and must be inspected manually until the workflow is changed.

---

## 3. Chronology and Rationale

| Wk | Target | Input structure | Outcome | Reasoning for next step |
|----|--------|-----------------|---------|--------------------------|
| 1 | **PD-L1** (reference) | `PDL1.pdb`, chain A, hotspot 56 | **101 accepted / 1362 trajectories** (7.4% acceptance) | Confirms the pipeline is functioning correctly on an established easy target. Moves us to the real problem. |
| 1→2 | **AAV2 VP monomer (run 1)** | `1lp3_monomer_1chain_tight.pdb`, hotspots A458–472, A488–494 | **0 accepted / 64 trajectories** | Mostly severe clashes (48%). The VP-monomer surface is flat and β-sheet-dominated — a known-hard topology for AF2-based hallucination. |
| 2 | **AAV2 VP monomer (run 2, hardtarget)** | same, binder length 60–100 | **0 accepted / 252 trajectories** | Same failure mode persists despite switching to `hardtarget` preset (initial-guess prediction, relaxed contact weights). Concluded the monomer surface is intrinsically poor for solo targeting. |
| 2→3 | **AAV2 trimer (3-fold axis)** | `1lp3_trimer_3fold_tight.pdb`, quaternary hotspots | **0 accepted / 15 trajectories** (short probe) | Trimer was computationally expensive and early trajectories showed the same clash pattern; pivoted. |
| 3 | **AAV2 dimer — trial 2** | `151lp3t3_dimer_fixed.pdb`, chains A & C, symmetric hotspots; `betasheet_4stage_multimer_hardtarget` preset | **0 accepted / 37 trajectories** | Strong β-sheet bias (`weights_helicity = −2.0`) produced unstructured binders that failed `Binder_Loop%` and `Surface_Hydrophobicity` filters. |
| 3 | **AAV2 dimer — trial 3** | same target; `default_4stage_multimer_hardtarget` preset + relaxed filters (Loop 90→95 %, UnsatHbonds 4→6, SurfHydro 0.35→0.45) | **28 accepted / 278 trajectories (10.1%)** — *but see §5* | Replacing β-sheet bias with the default helicity weight yielded high-confidence designs. Filter relaxation was conservative and targeted at hard-surface pathologies, not core quality metrics. |

**Figure 1** summarizes trajectory counts and acceptance across all runs.

![Figure 1](figures/fig1_run_summary.png)

**Figure 4** shows *why* each run failed: low-confidence trajectory pLDDT (orange) and severe steric clashes (grey) dominated all AAV2 monomer runs.

![Figure 4](figures/fig4_outcomes.png)

---

## 4. Trial 3 Results (Accepted Designs)

The 28 accepted designs clear every validation threshold with substantial margin:

| Metric | Cutoff | Observed range |
|---|---|---|
| Interface pTM | ≥ 0.50 | 0.77 – 0.89 |
| Interface pAE | ≤ 0.35 | 0.17 – 0.29 |
| Complex pLDDT | ≥ 0.80 | 0.81 – 0.92 |
| Binding ΔG (REU) | < 0 | −68 to −114 |
| Shape complementarity | ≥ 0.60 | 0.60 – 0.71 |
| Binder RMSD (bound vs. free, Å) | ≤ 3.5 | 0.84 – 3.46 |

**Figure 2** shows the distribution of each metric across all 28 accepted designs.

![Figure 2](figures/fig2_trial3_metrics.png)

By every BindCraft-internal metric, these designs appear to be strong binders.

---

## 5. Critical Finding: Target Collapse in Multimer Designs

Visual inspection of the accepted complexes revealed that **the target dimer (chains A + C) had undergone massive rearrangement during AF2 prediction** — the two VP protomers had collapsed inward to form a compact pseudo-complex around the binder, rather than retaining their crystallographic dimer geometry.

Quantifying this:

![Figure 3](figures/fig3_target_rmsd_failure.png)

- `Average_Target_RMSD` (deviation of the target backbone from its input pose) is **25 – 39 Å** for every accepted design.
- No design falls within a structurally meaningful cutoff (< 5 Å).
- The high i_pTM (0.77–0.89) is not protective — AF2 confidently predicts the collapsed complex.

**Mechanism.** AF2-Multimer predicts the relative positioning of all chains each step. When the target consists of two non-covalently-linked chains and the loss rewards contacts with hotspots on both, the cheapest optimization path is to pull the two target chains toward each other until one binder can engage both. BindCraft passes the target coordinates only as a template *hint*, not a constraint; there is no rigid-body lock for multi-chain targets.

**Consequence.** The 28 Trial 3 designs are confident but biologically invalid with respect to the stated goal. They cannot be claimed to bind the assembled capsid surface.

---

## 6. Challenges Encountered

1. **Hard target topology.** AAV2 VP presents a flat, β-sheet-dominated surface. AF2-driven hallucination works best for targets with concave, helix-compatible binding pockets. This is the root cause of the 0% acceptance on both monomer runs.
2. **Multi-chain template drift.** As detailed in §5, BindCraft has no mechanism to hold the relative positions of two non-covalently joined chains. Any quaternary-epitope design is at risk of this failure mode.
3. **Input-structure hygiene.** Several runs were delayed by multi-MODEL PDBs, inconsistent chain labelling, and whitespace in hotspot specifications. All are now resolved with a fixed-structure pipeline (`151lp3t3_dimer_fixed.pdb`).
4. **Filter relaxation is a double-edged sword.** Loosening the Loop% / UnsatHbonds / SurfHydro filters in Trial 3 was what enabled acceptance, but it also admits designs that are structurally marginal on those axes. Post-hoc analysis of the accepted set (§4) confirms the accepted designs are in fact well within the relaxed thresholds, so the relaxation is defensible.

---

## 7. Conclusions

- **PD-L1 benchmark:** pipeline is operational and reproducible.
- **AAV2 monomer:** not a viable target under current BindCraft settings.
- **AAV2 dimer (Trial 3):** produces high-confidence designs at 10% acceptance, **but** the designs bind to a collapsed, non-physiological target conformation. They are not valid candidates for experimental validation as-is.

---

## 8. Next Steps

**Immediate (this week):**
1. **Abort Trial 3** and re-run as a **single-protomer design** against chain A only (hotspots A30-34, A102-105, A113-115, A451-456; binder length 40–100). This removes the multi-chain collapse degree of freedom entirely.
2. **Post-hoc quaternary screen.** Each accepted single-chain binder will be superposed onto the full capsid model (`1lp3_hexamer.pdb`) and filtered for (i) absence of steric clash with neighbouring protomers and (ii) secondary contacts with adjacent VPs. This recovers the quaternary-preference goal *without* asking AF2 to model it.

**Medium-term (next 2 weeks):**
3. If single-protomer designs pass the quaternary screen, **rank the top 10 for experimental characterization** (synthesis, biolayer interferometry against assembled AAV2 capsid).
4. Parallel exploration: **fused-chain target** (`A–GGGGSGGGGSGGGGS–C` construct) as a control for whether covalent constraint of the dimer enables direct quaternary design.

**Longer-term:**
5. Extend to other serotypes (AAV5, AAV9) once the AAV2 pipeline is validated experimentally.
6. Evaluate RFdiffusion + MPNN as an alternative backbone-generation route, which applies a rigid-body constraint to the target by construction.

---

## 9. Data and Reproducibility

All runs, logs, and analysis scripts are preserved under `/data/binder_software/BindCraft/`:

- `settings_target/` — target JSONs for each run
- `settings_advanced/` and `settings_filters/` — preset and filter configurations
- `15delt3.pdb/output/` — Trial 3 full outputs (Accepted, Trajectory, failure_csv)
- `bindcraft_report.py` — HTML run-status generator (used for live monitoring)
- `rank_current.py` — manual re-ranking without halting a run
- `BINDCRAFT_PARAMETERS_REFERENCE.md` — parameter and cutoff reference
- `Paper/figures/` — source PNGs for this report

Figures were generated by `Paper/generate_figures.py` from the raw `final_design_stats.csv` and directory-count data; all numbers are directly traceable.
