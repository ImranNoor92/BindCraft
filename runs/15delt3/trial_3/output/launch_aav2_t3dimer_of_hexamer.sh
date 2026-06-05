# AAV2 T3 Dimer Binder Design - TRIAL 3 - 2026-04-10
# Target: 151lp3t3_dimer_fixed.pdb, chains A & C (C2 symmetric dimer)
# Hotspots: A30-34, A102-105, A113-115, A451-456 + same on C chain
# Binder lengths: 60-150, goal: 50 candidates
# Changes from Trial 2:
#   - Advanced: default_4stage_multimer_hardtarget (was betasheet, weights_helicity -0.3 vs -2.0)
#   - Filters: relaxed_filters (Loop% 90->95, UnsatHbonds 4->6, SurfHydro 0.35->0.45)

source /home/a-mxn833/mambaforge/etc/profile.d/conda.sh
conda activate BindCraft
cd /data/binder_software/BindCraft

CUDA_VISIBLE_DEVICES=0 nohup python -u bindcraft.py \
  --settings '/data/binder_software/BindCraft/settings_target/15del1lp3.json' \
  --filters './settings_filters/relaxed_filters.json' \
  --advanced './settings_advanced/default_4stage_multimer_hardtarget.json' \
  > /data/binder_software/BindCraft/15delt3.pdb/output/run_log_gpu0.txt 2>&1 &

CUDA_VISIBLE_DEVICES=1 nohup python -u bindcraft.py \
  --settings '/data/binder_software/BindCraft/settings_target/15del1lp3.json' \
  --filters './settings_filters/relaxed_filters.json' \
  --advanced './settings_advanced/default_4stage_multimer_hardtarget.json' \
  > /data/binder_software/BindCraft/15delt3.pdb/output/run_log_gpu1.txt 2>&1 &
