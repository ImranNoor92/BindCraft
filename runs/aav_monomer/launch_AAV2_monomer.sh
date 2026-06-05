# AAV2 Monomer Binder Design - 2026-04-09 (Run 2)
# Target: 1lp3_monomer_1chain_tight.pdb, chain A, hotspots A458-472 A488-494
# Binder lengths: 60-100, goal: 50 candidates
# Changed: betasheet_hardtarget advanced settings, longer binders

cd /data/binder_software/BindCraft

CUDA_VISIBLE_DEVICES=0 nohup python -u bindcraft.py \
  --settings './settings_target/AAV2_monomer.json' \
  --filters './settings_filters/default_filters.json' \
  --advanced './settings_advanced/betasheet_4stage_multimer_hardtarget.json' \
  > ./aav_monomer/output_run2/run_log_gpu0.txt 2>&1 &

CUDA_VISIBLE_DEVICES=1 nohup python -u bindcraft.py \
  --settings './settings_target/AAV2_monomer.json' \
  --filters './settings_filters/default_filters.json' \
  --advanced './settings_advanced/betasheet_4stage_multimer_hardtarget.json' \
  > ./aav_monomer/output_run2/run_log_gpu1.txt 2>&1 &
