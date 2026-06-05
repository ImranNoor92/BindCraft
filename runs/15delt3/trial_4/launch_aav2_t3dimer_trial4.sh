#!/bin/bash
# AAV2 T3 Dimer Binder Design - TRIAL 4 - 2026-04-29
# Target: 151lp3t3_dimer_fixed.pdb, chains A & C (C2 symmetric dimer)
# Hotspots: A30-34, A102-105, A113-115, A451-456 + same on C chain
# Binder lengths: 60-150, goal: 50 candidates
#
# Changes from Trial 3:
#   - Filters: trial4_filters.json — adds Average_Target_RMSD ≤ 5 Å
#     (was null in Trial 3; this is THE fix for the dimer-collapse failure)
#
# RATIONALE FOR EACH PARAMETER
# ---------------------------------------------------------------------------
# Settings file:   settings_target/15del1lp3.json
#   - chains "A,C": dimer target, both protomers visible to AF2-Multimer.
#                   Required to design a quaternary-epitope binder.
#   - hotspots A+C symmetric: enforces a C2-symmetric binding mode that
#                   contacts both protomers, mimicking the assembled capsid
#                   surface near the 2-fold axis.
#   - lengths [60,150]: long enough to span the inter-protomer hotspots
#                   (~30 Å apart); shorter binders failed in monomer trials.
#   - 50 final designs: enough diversity to choose from after the new
#                   Target_RMSD filter shrinks the acceptance pool.
#
# Advanced preset: settings_advanced/default_4stage_multimer_hardtarget.json
#   - default helicity weight (-0.3, NOT -2.0): in Trial 2 the strong
#                   beta-sheet bias (-2.0) produced unstructured binders that
#                   failed Loop% / Surface_Hydrophobicity filters. Default
#                   helicity allows AF2 to choose the most stable fold for
#                   the surface, which on a flat capsid surface tends to
#                   converge on helical bundles and short β/α mixed folds.
#   - hardtarget settings: enables predict_initial_guess=true. AF2 starts
#                   each prediction from the input target template, which
#                   speeds convergence on β-sheet-dominated AAV surfaces.
#
# Filters file:    settings_filters/trial4_filters.json
#   THE KEY CHANGE FROM TRIAL 3:
#   - Average_Target_RMSD ≤ 5 Å (was: null, no limit)
#     Trial 3 produced 28 "accepted" designs, but ALL had Target_RMSD
#     between 25 and 39 Å. The dimer (chains A+C) collapsed inward during
#     AF2 prediction, because the loss rewarded contacts with hotspots on
#     both chains and AF2-Multimer is free to reposition non-covalently
#     linked chains. The 28 designs are biologically invalid: they bind a
#     non-physiological target conformation.
#     5 Å chosen because:
#       * monomer targets typically achieve <2 Å (template-constrained)
#       * <5 Å allows minor flexibility (loop reorganization, side chain
#         repacking) but rejects gross interchain rearrangement
#       * if 5 Å proves too strict, can relax to 8–10 Å in next trial
#   - Per-model thresholds (1_Target_RMSD, 2_Target_RMSD): also set to 5 Å.
#     Models 3-5 left null because BindCraft only enforces models 1-2 by
#     convention (consistent with the rest of the filter file).
#   - All other filters identical to relaxed_filters.json:
#       Loop% 95% (relaxed from 90), UnsatHbonds 6 (relaxed from 4),
#       SurfHydro 0.45 (relaxed from 0.35). These relaxations were
#       defensible in Trial 3 and remain so for Trial 4.
#
# Expected outcome:
#   Acceptance rate will drop from Trial 3's 10% (28/278) to perhaps 1–3%,
#   because every collapsed-dimer design is now rejected. Reaching 50
#   accepted designs may take 1500–5000 trajectories (1–3 days). If the
#   acceptance rate falls below 1% after the 600-trajectory monitoring
#   window, BindCraft will exit automatically — at which point we reassess
#   (relax Target_RMSD to 8 Å, or pivot to single-protomer design).
# ---------------------------------------------------------------------------

source /home/a-mxn833/mambaforge/etc/profile.d/conda.sh
conda activate BindCraft
cd /data/binder_software/BindCraft

CUDA_VISIBLE_DEVICES=0 nohup python -u bindcraft.py \
  --settings '/data/binder_software/BindCraft/settings_target/15del1lp3.json' \
  --filters './settings_filters/trial4_filters.json' \
  --advanced './settings_advanced/default_4stage_multimer_hardtarget.json' \
  > /data/binder_software/BindCraft/15delt3.pdb/output/run_log_gpu0.txt 2>&1 &

CUDA_VISIBLE_DEVICES=1 nohup python -u bindcraft.py \
  --settings '/data/binder_software/BindCraft/settings_target/15del1lp3.json' \
  --filters './settings_filters/trial4_filters.json' \
  --advanced './settings_advanced/default_4stage_multimer_hardtarget.json' \
  > /data/binder_software/BindCraft/15delt3.pdb/output/run_log_gpu1.txt 2>&1 &
