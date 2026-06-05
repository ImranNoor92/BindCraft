# AAV2 BindCraft Target Selection Rationale

## Quick Start

If I only need the actionable setup, I use the following:

- **Target PDB**: `/data/binder_software/BindCraft/aav/1lp3_trimer_fixed.pdb`
- **Chains**: `A,B,C`
- **Primary hotspot set**: `A458-472,A488-494,B458-472,B488-494,C458-472,C488-494`
- **Binder length range**: `80–150`
- **Large-target setting**: `"predict_bigbang": true`

## Executive Summary

| Item | Recommendation | Why |
|---|---|---|
| Biological objective | Design for **assembled capsid** recognition | Avoid monomer-only binders |
| Structural target | **3-chain trimer** (`A,B,C`) from `1LP3` | Preserves local quaternary geometry near 3-fold axis |
| Hotspot strategy | Prioritize **3-fold protrusion** residues | Best alignment with assembled-surface context |
| Primary hotspot set | `A458-472,A488-494,B458-472,B488-494,C458-472,C488-494` | Tight multi-chain enforcement of trimer-dependent binding |
| Secondary hotspot set | `A343-345,A385,A455-472,A488-494` mirrored across `A,B,C` | Broader surface exploration if primary is too restrictive |
| Compute plan | Run one design per GPU (`CUDA_VISIBLE_DEVICES=0/1`) | BindCraft/AF2 is typically single-GPU per run |

---

## Purpose

In this document, I explain my rationale for selecting **target hotspot residues** for BindCraft design against the **assembled AAV2 capsid**, using a **3-chain trimer** derived from `1LP3`.

My goal is to design a binder that recognizes the **assembled T=1 AAV2 capsid**, not an isolated monomer.

---

## Biological Goal

### Desired outcome
I want to design a binder that recognizes the **assembled AAV2 capsid surface**.

### Important clarification
The binder does **not** need to reproduce A20 exactly.

What matters is:

- it should bind the **capsid context**
- it should prefer an **assembled surface geometry**
- it should ideally recognize a **quaternary epitope** rather than a monomer-only patch

---

## Input Structure Used

### Target PDB
`/data/binder_software/BindCraft/aav/1lp3_trimer_fixed.pdb`

### Structural composition
- PDB contains **3 chains**: `A`, `B`, `C`
- Each chain contains **519 residues**
- Residue numbering spans **80–598** on each chain
- This corresponds to the **VP3 region** present in the crystal structure

### Chain verification

- Chains present: `A`, `B`, `C`
- Residue range per chain: `80–598`
- Residues per chain: `519`

---

## Why a Trimer Was Chosen Instead of a Monomer

A monomer-only design target would allow BindCraft to design a binder against a surface that may also exist on an isolated VP subunit.

That is not ideal for my project.

Using the trimer allows my design process to see the **local assembled geometry** around the **3-fold axis**, which is much closer to the real capsid surface.

This improves my chances of getting a binder that recognizes:

- the assembled capsid
- a quaternary surface patch
- a geometry not fully present in a monomer by itself

---

## Initial Antibody Reference: A20 Epitope

I use A20 as a useful reference because it binds a **conformational epitope** on assembled AAV2 capsid rather than a denatured linear peptide.

### Literature-derived A20-associated residues
Residues repeatedly implicated include:

- 261
- 263
- 264
- 381
- 384
- 385
- 548
- 658–660
- 708
- 717

### Important caveat
My PDB spans residues **80–598**, so residues above 598 are **not present** in the structure I used for design.

Therefore:

### A20-associated residues that are present in my PDB
```text
261, 263, 264, 381, 384, 385, 548
```

### A20-associated residues missing from my PDB
```text
658, 659, 660, 708, 717
```

This means the full A20 epitope cannot be represented directly in this trimer file.

---

## PDB-Based Structural Inspection

I inspected the trimer computationally to determine which residues actually lie at the **inter-chain 3-fold region**.

### Findings from chain/interface analysis
Using CA-based inter-chain contact analysis, the residues most strongly associated with the **true 3-fold center** were:

```text
343–345
385
458–472
488–494
```

I found these residues in all three chains at corresponding positions, meaning the following are structurally central to the 3-fold region:

- `A343-345`, `A385`, `A458-472`, `A488-494`
- `B343-345`, `B385`, `B458-472`, `B488-494`
- `C343-345`, `C385`, `C458-472`, `C488-494`

---

## Interpretation of the 3-Fold Regions

### `458–472`
This appears to represent the **main 3-fold protrusion peak**.

Why it matters:

- highly exposed
- structurally central
- physically accessible to a binder
- likely to encourage capsid-surface recognition

### `488–494`
This forms the **shoulder/flanking region** of the protrusion.

Why it matters:

- expands the contactable surface
- allows a binder to sit more stably on the trimeric patch

### `343–345`
This appears deeper in the **inter-monomer contact environment**.

Why it matters:

- helps define the quaternary geometry
- useful if broader hotspot coverage is desired

### `385`
This is especially interesting because it is:

- located in the structural 3-fold center set
- also implicated in A20-related epitope mapping

So residue 385 provides a useful bridge between the **known antibody epitope literature** and the **actual local trimer geometry** seen in this structure.

---

## Overlap Between A20-Related Residues and 3-Fold Structural Center

### A20 residues that overlap with the trimer-interface region
```text
261, 381, 384, 385
```

### A20-confirmed residues that do not appear to sit in the core 3-fold-center set
```text
263, 264, 548
```

This is important because it shows me that the A20 epitope and the structurally defined 3-fold center are related, but not identical.

That supports the following conclusion:

> If my goal is simply assembled capsid binding, it is better for me to choose residues based on the **actual 3-fold structural center** rather than trying to force the design around only the historically mapped A20 residues.

---

## Final Design Logic

Because my goal is:

> bind assembled capsid, not monomer

I therefore prioritize the following in hotspot selection:

- **true trimeric geometry**
- **multi-chain hotspot definition**
- **surface-exposed 3-fold protrusion residues**
- **not necessarily exact A20 competition**

That is why I focus my selected hotspot set on the **3-fold structural center**, not just the historical antibody list.

---

## Recommended Hotspot Options

### Option 1 — Tight multi-chain 3-fold hotspot (**recommended**)
This is my best first-pass option for assembled capsid recognition.

```text
A458-472,A488-494,B458-472,B488-494,C458-472,C488-494
```

### Why this is recommended
- directly centered on the true 3-fold protrusion
- strongly multi-chain
- most likely to enforce capsid-dependent recognition for my design objective
- avoids drifting toward a monomer-only surface

---

### Option 2 — Broader multi-chain 3-fold hotspot
I use this if the first option feels too restrictive.

```text
A343-345,A385,A455-472,A488-494,B343-345,B385,B455-472,B488-494,C343-345,C385,C455-472,C488-494
```

### Why use this
- keeps the same core 3-fold protrusion
- adds deeper interface-defining residues
- gives BindCraft a broader local surface to work with

### Tradeoff
- broader search space
- less tightly focused than Option 1

---

### Option 3 — Single-chain face only
I use this only when I want a simpler design setup.

```text
A343-345,A385,A455-472,A488-494
```

### Tradeoff
- easier target definition
- less explicitly quaternary
- may produce a binder that recognizes one exposed monomer surface instead of the assembled capsid context

---

## Main Recommendation

### Best starting hotspot set
```text
A458-472,A488-494,B458-472,B488-494,C458-472,C488-494
```

This is my best option because it most directly matches my biological goal:

> recognize assembled AAV2 capsid through the trimeric 3-fold surface

---

## Hardware Assessment

My available system has:

- **2 × NVIDIA RTX 6000 Ada GPUs**
- **48 GB VRAM each**
- **112 CPU cores**
- **~256 GB RAM**

### Practical implication
A full 3-chain target is large but feasible on my hardware.

### Approximate target size
- Target: `519 × 3 = 1557 residues`
- Binder: roughly `80–150 residues`
- Total complex: approximately `1637–1707 residues`

### Conclusion
This setup should be able to run the **full trimer** without trimming, especially with large-target settings enabled.

---

## Important Compute Note

BindCraft/AF2 design is primarily **single-GPU per run**.

That means:

- one run will usually occupy one GPU
- the second GPU is best used by launching a **second independent run**
- CPU cores help with supporting steps such as PyRosetta relaxation, but GPU is still the main bottleneck

So the best use of my machine is usually:

- run one design job on GPU 0
- run a second design job on GPU 1

---

## Recommended BindCraft Target JSON

```json
{
  "design_path": "/data/binder_software/BindCraft/aav/output/",
  "binder_name": "AAV2_trimer_3fold",
  "starting_pdb": "/data/binder_software/BindCraft/aav/1lp3_trimer_fixed.pdb",
  "chains": "A,B,C",
  "target_hotspot_residues": "A458-472,A488-494,B458-472,B488-494,C458-472,C488-494",
  "lengths": [80, 150],
  "number_of_final_designs": 100
}
```

---

## Recommended Advanced Setting Change

Because this is a large target, I enable this in the advanced settings:

```json
"predict_bigbang": true
```

### Why
This helps AF2 handle large complexes more robustly by introducing positional bias in the structure module for difficult large-scale systems.

---

## Example Run Commands

### GPU 0
```bash
conda activate BindCraft
cd /data/binder_software/BindCraft

CUDA_VISIBLE_DEVICES=0 nohup python -u bindcraft.py \
  --settings './settings_target/AAV2_trimer_3fold.json' \
  --filters './settings_filters/default_filters.json' \
  --advanced './settings_advanced/AAV2_4stage_multimer.json' \
  > ./aav/output/run_log_gpu0.txt 2>&1 &
```

### GPU 1
```bash
CUDA_VISIBLE_DEVICES=1 nohup python -u bindcraft.py \
  --settings './settings_target/AAV2_trimer_3fold.json' \
  --filters './settings_filters/default_filters.json' \
  --advanced './settings_advanced/AAV2_4stage_multimer.json' \
  > ./aav/output/run_log_gpu1.txt 2>&1 &
```

---

## Final Conclusion

The hotspot strategy chosen here is based on:

- the real structure of my **1LP3-derived trimer**
- the requirement to target **assembled capsid rather than monomer**
- structural identification of the **true 3-fold center**
- partial comparison with the known **A20 conformational epitope**
- the practical realities of my available compute hardware

### Final recommended hotspot definition
```text
A458-472,A488-494,B458-472,B488-494,C458-472,C488-494
```

I treat this as the primary starting point for BindCraft design against the assembled AAV2 trimer.
