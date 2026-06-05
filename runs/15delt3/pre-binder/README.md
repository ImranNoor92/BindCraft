# pre-binder — RFdiffusion C3-symmetric binder for AAV t3 hexamer

**Status:** Planning only. Nothing run yet. Awaiting decision after trial_6 BindCraft yields enough data to compare.

**Goal:** Produce a binder that is hexamer-specific by construction — meaning it cannot bind an isolated dimer of the AAV capsid, only the hexameric (3-fold) arrangement found in T=3 capsids.

---

## Why this exists

Trial 5 (`A+F` hotspots) and trial 6 (`A+C+E` hotspots) in BindCraft showed that single-chain binders struggle to bridge the geometric gaps between dimer-pairs in the hexamer:
- Trial 5: 42/42 trajectories failed (binder anchor landed 7.2 Å from chain C — physically inside it).
- Trial 6 (current, running): ~14% trajectory success rate. Spans 2 dimer-pairs so is partially hexamer-specific, but BindCraft's hotspot loss is OR-like — the binder may collapse to one chain rather than truly bridging.

The fundamental reason: enforcing "binder must contact residues that ONLY come together in the hexamer arrangement" requires either (a) explicit cross-pair contacts in the loss function (BindCraft doesn't have this), or (b) structural constraints from binder topology (the path we'll take here).

**Solution: a C3-symmetric homotrimer binder.** Three identical subunits arranged at 120° intervals around the hexamer's natural 3-fold axis. Each subunit binds one chain from a different dimer-pair (e.g., A, C, E). The C3 symmetry of the binder mechanically locks all three engagements simultaneously — the binder cannot "cheat" by binding only one pair.

On a hexamer → all 3 subunits engage → strong binding.
On an isolated dimer → at most 1 subunit engages → affinity collapses → **hexamer-specific by construction.**

---

## Target geometry recap (from prior analysis)

Source: `/data/binder_software/BindCraft/runs/15delt3/trial_6_may_20/1lp3_hexamer_trimmed_fixed.pdb`

| | |
|---|---|
| Topology | 6 chains (A–F), residues 70–150 per chain, single MODEL |
| Symmetry | C3 (3-fold axis through coordinates ~(0, 0, 180.8)) |
| Dimer pairs | A↔E, B↔D, C↔F (6.2 Å between partner 105-115 centroids) |
| Cross-pair distances | 18.6 Å (A-C, B-F, D-E) — the hexamer-specific contacts |
| Hotspot range | residues 105-115 (verified solvent-accessible, 34% buried by oligomerization) |

The hexamer's 3-fold axis is at the geometric center of the 6 chains' 105-115 patches: roughly (0, 0, 180.8) Å in the input PDB. A C3-symmetric binder of any reasonable size, placed with its C3 axis aligned to this point, will naturally engage chains A, C, E (or B, D, F — same by symmetry).

---

## The plan: phased approach

RFdiffusion's symmetric PPI mode has known issues with hotspot residues (per the official README: "they seem to interact weirdly with hotspot residues in PPI"). Rather than fight that, we use a more reliable phased approach:

### Phase 1 — Single-subunit binder (pilot, ~2-4 hours)

Use **regular** RFdiffusion PPI (no symmetry) to design a single-chain binder against just **one chain (A)** of the hexamer, hotspots `A105-115`.

- Subunit length: 50-80 residues (small — each subunit only needs to engage one chain's 105-115 patch)
- ~10 designs in the pilot
- Validates that single-chain binders against this epitope are feasible without the cross-pair constraint
- Output: 10 backbone PDBs in `outputs/01_rfdiffusion_pilot/`

### Phase 2 — Trimerize via C3 replication + AF2 validation (~4-6 hours for pilot)

Take the surviving Phase 1 backbones, replicate each by C3 symmetry around the hexamer's 3-fold axis, fuse the three copies into one polypeptide with flexible linkers, and validate the assembled trimer + full hexamer with AF2-multimer.

- Output per backbone: trimerized binder (3× subunit + 2 linkers, ~180-260 residues total)
- Validation: AF2-multimer with target (hexamer) + binder (trimer). Filter on:
  - Binder pLDDT > 0.70
  - Interface pTM > 0.65
  - All 3 subunits in contact (per-chain interface SASA > 200 Å² each)
  - RMSD of binder to RFdiffusion+C3-replicated design < 3 Å
- Output: validated designs in `outputs/02_trimerized_af2_validated/`

### Phase 3 — ProteinMPNN sequence redesign (~1-2 hours)

Run ProteinMPNN on the validated trimer backbones from Phase 2 to optimize sequence. Keep target sequence locked; redesign binder. Tie equivalent positions across the 3 subunits (so all subunits remain identical).

- Sequences per backbone: 8
- Output: validated sequences in `outputs/03_mpnn_sequences/`

### Phase 4 — Final AF2 re-validation (~1-2 hours)

Re-run AF2 multimer on each MPNN sequence variant. Apply the same filters as Phase 2.

- Output: ranked final designs in `outputs/04_final_ranked/`

**Total wall-clock estimate (single GPU):** ~10-15 hours for pilot of 10 designs.
**Total compute for full run (100 starting backbones):** ~3-5 days on 1 GPU, or ~2 days on 2 GPUs.

### Phase 5 (optional, more rigorous) — Direct symmetric RFdiffusion

If Phase 1-4 yields designs but you want to try the more rigorous direct approach (where symmetry is enforced at backbone generation time rather than post-hoc), this requires:

1. Pre-symmetrizing the input: extract one dimer pair (e.g., A+E), center on origin, align to RFdiffusion's canonical C3 axis (Z)
2. Running RFdiffusion with `--config-name=symmetry inference.symmetry=c3`
3. Working around the hotspot weirdness (probably by omitting hotspots and using guiding potentials instead)

Marked as optional because the post-hoc trimerization in Phase 1+2 should give equivalent designs with less risk.

---

## Decision criteria (when to actually run this)

Run Phase 1 pilot when **any** of the following is true:

- [ ] Trial 6 BindCraft accumulates 5+ accepted designs AND post-hoc dimer-binding test shows they bind the dimer too (i.e., they're not hexamer-specific in practice)
- [ ] Trial 6 BindCraft success rate stays below 10% after 24 more hours (low yield, may as well try the alternative)
- [ ] You want a parallel approach as a hedge (run both simultaneously, compare final designs)

Hold off if:
- [ ] Trial 6 produces 10+ designs that pass post-hoc dimer-binding test (specificity worked)
- [ ] We discover residues 105-115 isn't the right epitope and need to repick before any design work

---

## Files in this folder

```
pre-binder/
├── README.md                       # This file
├── docs/
│   ├── 01_workflow.md              # Phase-by-phase technical detail
│   ├── 02_rfdiffusion_contigs.md   # Contig syntax explained for this target
│   └── 03_validation_filters.md    # AF2 filter rationale
├── scripts/
│   ├── 00_check_env.sh             # Verify rfdiffusion + venv-af2 + ProteinMPNN paths
│   ├── 01_pilot_rfdiffusion.sh     # Phase 1: 10 single-subunit designs
│   ├── 02_trimerize_replicate.py   # Phase 2a: C3-replicate + linker-fuse each backbone
│   ├── 03_af2_validation.sh        # Phase 2b: AF2 multimer on trimerized backbones
│   ├── 04_proteinmpnn.sh           # Phase 3: sequence design with tied positions
│   └── 05_af2_revalidation.sh      # Phase 4: final AF2 check
├── inputs/
│   ├── target_pdb_link.md          # Pointer to source hexamer PDB
│   └── hotspot_residues.txt        # The chain A hotspot list
├── outputs/                        # Empty until runs start
└── logs/                           # Empty until runs start
```

---

## Quick-start (when ready)

```bash
cd /data/binder_software/BindCraft/runs/15delt3/pre-binder
bash scripts/00_check_env.sh                                  # ~30 sec
bash scripts/01_pilot_rfdiffusion.sh   2>&1 | tee logs/01.log # ~2-4 hr on 1 GPU
python scripts/02_trimerize_replicate.py                      # ~1 min
bash scripts/03_af2_validation.sh      2>&1 | tee logs/03.log # ~2 hr
bash scripts/04_proteinmpnn.sh         2>&1 | tee logs/04.log # ~30 min
bash scripts/05_af2_revalidation.sh    2>&1 | tee logs/05.log # ~2 hr
```

Each script is self-contained and idempotent: it checks for already-existing outputs and skips work that's already done. Safe to re-run.

---

## Reference: existing pipeline patterns on this machine

- `/data/rfdiffusion/trial_2B/master_pipeline/` — an existing pipeline that runs RFdiffusion → MPNN → AF2 on the t3 dimer-of-dimers (different target structure, but useful reference for the orchestration pattern).
- `/data/rfdiffusion/examples/design_ppi.sh` — canonical RFdiffusion PPI template (single-chain binder, no symmetry).
- `/data/rfdiffusion/examples/design_cyclic_oligos.sh` — symmetric oligomer design (without target — useful only as syntax reference).

The trial_2B JSON config (`/data/rfdiffusion/trial_2B/master_pipeline/trial2B_config.json`) is the closest existing reference for "structured RFdiffusion → MPNN → AF2 pipeline on a t3 capsid target." If you want a more integrated single-command pipeline later, copying its pattern would be the way.
