# AAV2 Binder Design Campaign — Plan

## Phase 0: Fix the PDB file (critical prerequisite)

Your exported PDB has a problem: **all three subunits are labeled chain A** with identical residue numbering (80-598). ChimeraX collapsed the chain IDs when exporting from the biological assembly. BindCraft needs distinct chain IDs (A, B, C) to know what is "target" vs what to design against.

We need to relabel the three copies as chains A, B, and C.

**Status:** DONE — fixed file saved as `1lp3_trimer_fixed.pdb`

---

## Phase 1: Configure `target_settings.json`

This is the "what to design" file — 7 fields:

| Field | Recommended Value | Rationale |
|---|---|---|
| `design_path` | `"/data/binder_software/BindCraft/aav/output/"` | Keep outputs organized under your project folder |
| `binder_name` | `"AAV2"` | Prefix for all output files |
| `starting_pdb` | `"/data/binder_software/BindCraft/aav/1lp3_trimer_fixed.pdb"` | The chain-relabeled PDB (after Phase 0) |
| `chains` | `"A,B,C"` | Use all three subunits as the target — the binder should see the full trimeric interface so it designs against the real capsid surface |
| `target_hotspot_residues` | *Needs biology discussion* | Residues on the capsid surface you want the binder to contact. Options: (a) leave `null` to let AF2 find sites freely, (b) specify known functional residues on the AAV2 3-fold axis or receptor-binding regions. |
| `lengths` | `[80, 150]` | 80-150 residues gives enough surface area for a capsid binder while staying within AF2's sweet spot. The total complex will be ~1,557 + binder residues. |
| `number_of_final_designs` | `50` | Start with 50 passing designs; you can always resume later |

---

## Phase 2: Configure `advanced_settings.json`

Starting from `default_4stage_multimer.json` with these AAV2-specific modifications:

| Field | Default | Recommended | Rationale |
|---|---|---|---|
| `predict_bigbang` | `false` | **`true`** | Your complex is ~1,557+ AAs — this introduces atom-position bias into AF2's structure module, critical for large complexes |
| `predict_initial_guess` | `false` | **`true`** | Helps AF2 predict the correct binding pose for large targets |
| `rm_template_seq_design` | `false` | **`true`** | Increases target flexibility during design — helpful because the crystal structure may not capture all capsid dynamics |
| `rm_template_sc_design` | `false` | **`true`** | Remove target sidechains during design to avoid overfitting to crystal contacts |
| `weights_helicity` | `-0.3` | `0.0` or `-0.3` | Keep default (-0.3 favors some beta) or use 0.0 for no bias; AAV2 surface is mostly beta-barrel so a mixed binder is fine |
| `num_recycles_design` | `1` | `1` | Keep low to manage GPU memory with this large target |
| `num_recycles_validation` | `3` | `3` | Standard; sufficient for validation |
| `num_seqs` | `20` | `20` | Number of MPNN sequences per trajectory — default is good |
| `max_trajectories` | `false` | `false` (unlimited) or `1000` | Set a cap if you want to limit GPU time |
| `start_monitoring` | `600` | `300` | Start monitoring acceptance rate earlier since large-target campaigns can be slow |
| Everything else | default | **keep default** | The 4-stage algorithm with default weights is well-tuned |

---

## Phase 3: Configure `filter_settings.json`

Recommend starting with **`relaxed_filters.json`** initially.

**Why:** AAV2 is a large, challenging target (3-subunit capsid). Default filters are tuned for simpler monomeric targets like PD-L1. Using relaxed filters for the first campaign lets you see what the pipeline can produce, then tighten thresholds based on the distribution of your results. You can always re-filter the output CSVs post-hoc.

If you prefer default filters, they're still reasonable — you'll just get fewer accepted designs and the campaign will run longer.

---

## Phase 4: Run the campaign

```bash
python bindcraft.py \
  --settings aav/AAV2_target.json \
  --advanced aav/AAV2_advanced.json \
  --filters settings_filters/relaxed_filters.json
```

---

## Phase 5: Analyze results

Review `final_design_stats.csv`, inspect top designs in ChimeraX, check binding poses relative to the 3-fold axis.

---

## Key decision needed before proceeding

**Hotspot residues** — do you want to:

1. **Leave `null`** — let AF2 explore the entire trimeric surface freely
2. **Specify residues at the 3-fold symmetry axis** — the depression between the three subunits where they meet (biologically relevant for receptor binding / antibody epitopes)
3. **Specify known receptor-binding residues** — e.g., the HSPG binding footprint around residues 484-528, 585-588

This is the most impactful design decision. Option 2 or 3 will focus the search and give faster results; option 1 is more exploratory but slower.
