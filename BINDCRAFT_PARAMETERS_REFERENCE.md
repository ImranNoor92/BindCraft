# BindCraft Parameters & Cutoffs — Master Reference

**Created:** 2026-04-10
**Purpose:** Single-source reference for all parameters, weights, and cutoff values used in BindCraft runs. Use this to interpret logs, understand why designs fail, and tune settings.

---

## 1. Design Loss Weights (Trajectory Optimization)

These weights control the **composite loss function** that BindCraft minimizes during the 4-stage trajectory optimization. A design is *generated* by minimizing the weighted sum of these terms. These are **NOT cutoffs** — they bias the optimizer.

| Parameter | Default | Hardtarget | Beta-sheet HT | Meaning | Direction |
|---|---|---|---|---|---|
| `weights_plddt` | 0.1 | 0.1 | 0.15 | Weight on predicted pLDDT loss. Higher → pushes for more confident local structure. | Minimize `1 - pLDDT` |
| `weights_pae_intra` | 0.4 | 0.4 | 0.4 | Weight on intra-chain PAE (binder internal). Higher → more confident binder fold. | Minimize PAE |
| `weights_pae_inter` | 0.1 | 0.1 | 0.1 | Weight on inter-chain PAE (binder↔target). Higher → more confident interface positioning. | Minimize PAE |
| `weights_con_intra` | 1.0 | 1.0 | 0.4 | Weight on binder internal contacts. Higher → more compact binder. | Maximize contacts |
| `weights_con_inter` | 1.0 | 1.0 | 0.5 | Weight on binder↔target contacts. Higher → more interface contacts. | Maximize contacts |
| `weights_helicity` | -0.3 | -0.3 | **-2.0** | Negative values *penalize* helical content. Strong negative → beta-sheet binder. | Minimize helicity |
| `weights_iptm` | 0.05 | 0.05 | 0.05 | Weight on interface pTM loss. Higher → stronger bias toward predicted binding. | Minimize `1 - i_pTM` |
| `weights_rg` | 0.3 | 0.3 | 0.3 | Radius of gyration loss. Keeps binder compact, not extended. | Minimize Rg |
| `weights_termini_loss` | 0.1 | 0.1 | 0.1 | Only active if `use_termini_distance_loss=true`. Pulls N/C termini together. | Minimize distance |

**If loss is too high during a stage:** Trajectory may be abandoned early if pLDDT drops below internal thresholds (see Section 3).

---

## 2. Design Algorithm Parameters

Control how the 4-stage optimization runs. These affect runtime and convergence but don't directly reject designs.

| Parameter | Default | Meaning |
|---|---|---|
| `design_algorithm` | `"4stage"` | Optimization schedule: logits → softmax → one-hot → greedy |
| `soft_iterations` | 75 | Iterations in Stage 2 (softmax) |
| `temporary_iterations` | 45 | Iterations in Stage 1 (logits) |
| `hard_iterations` | 5 | Iterations in Stage 3 (one-hot) |
| `greedy_iterations` | 15 | Iterations in Stage 4 (greedy refinement) |
| `greedy_percentage` | 1 | Fraction of positions to perturb in greedy stage |
| `num_recycles_design` | 1 | AF2 recycles during design (speed vs. accuracy trade-off) |
| `num_recycles_validation` | 3 | AF2 recycles during final validation (more = slower, more accurate) |
| `sample_models` | `true` | Sample different AF2 model weights across iterations |
| `optimise_beta` | `true` | Run extra optimization if binder has beta-sheet content |
| `optimise_beta_recycles_design` | 3 | Recycles during beta optimization (design) |
| `optimise_beta_recycles_valid` | 3 | Recycles during beta optimization (validation) |
| `predict_initial_guess` | `false` (true in hardtarget) | Use initial guess for AF2 prediction. Helps for hard targets. |
| `predict_bigbang` | `false` (true in non-HT) | Big-bang initialization for trajectory |

---

## 3. Internal Trajectory Checkpoints (Early Termination)

BindCraft will **abandon a trajectory mid-stage** if confidence drops. These thresholds are hardcoded in the pipeline (not in the JSON):

| Checkpoint | Threshold | What Happens if Failed |
|---|---|---|
| Initial trajectory pLDDT (Stage 1 start) | `< 0.65` | Design skipped immediately, marked as **LowConfidence** |
| Logit-stage pLDDT (Stage 1 end) | `< 0.7` approx | Design continues but flagged |
| Softmax trajectory pLDDT | `< 0.65` | Design abandoned, moved to **Trajectory/LowConfidence/** |
| One-hot trajectory pLDDT | `< 0.65` | Design abandoned |
| Clash check (any stage) | CA-CA distance too small | Moved to **Trajectory/Clashing/** |

**In the log you'll see:**
- `"Initial trajectory pLDDT too low to continue: 0.62"` → never started MPNN
- `"One-hot trajectory pLDDT too low to continue: 0.49"` → abandoned after Stage 3
- `"Severe clashes detected, skipping analysis and MPNN optimisation"` → clash rejection

---

## 4. ProteinMPNN (Sequence Redesign) Parameters

After a viable backbone is found, MPNN generates alternative sequences for validation.

| Parameter | Default | Meaning |
|---|---|---|
| `enable_mpnn` | `true` | Run MPNN sequence redesign |
| `num_seqs` | 20 | Number of MPNN sequences to generate per trajectory |
| `max_mpnn_sequences` | 2 | Max sequences allowed to pass filters per trajectory (prevents over-representation) |
| `sampling_temp` | 0.1 | MPNN sampling temperature. Higher = more diverse, lower = more conservative |
| `backbone_noise` | 0.0 | Noise added to backbone before MPNN sampling |
| `model_path` | `"v_48_020"` | MPNN model weights version |
| `mpnn_weights` | `"soluble"` | Use soluble-protein trained MPNN (vs "original") |
| `mpnn_fix_interface` | `true` | Keep interface residues fixed during MPNN redesign |
| `omit_AAs` | `"C"` | Amino acids MPNN is forbidden from sampling (cysteine by default) |

**If all MPNN sequences fail filters:** Log shows `"No accepted MPNN designs found for this trajectory."` → trajectory discarded.

---

## 5. AF2 Validation Filters (THE CRITICAL CUTOFFS)

After MPNN, each candidate sequence is re-predicted with AF2 and scored. **These are the make-or-break cutoffs.** A design must pass **all active filters** to be accepted.

Filters are evaluated across 5 AF2 model predictions. Metrics exist as `Average_*`, `1_*`, `2_*`, etc. Typically only `Average`, `1_`, and `2_` thresholds are enforced (models 3-5 set to `null`).

### 5a. AF2 Confidence Filters

| Filter | Threshold | Direction | Meaning | Failure Mode |
|---|---|---|---|---|
| `Average_pLDDT` | **≥ 0.80** | higher | Overall complex pLDDT (0-1 scale) | Structure poorly predicted |
| `1_pLDDT`, `2_pLDDT` | **≥ 0.80** | higher | Per-model pLDDT (models 1 & 2) | Same as above |
| `Average_pTM` | **≥ 0.55** | higher | Global TM-score confidence | Overall fold uncertain |
| `1_pTM`, `2_pTM` | **≥ 0.55** | higher | Per-model pTM | Same |
| `Average_i_pTM` | **≥ 0.50** | higher | **Interface** pTM — key for binding | AF2 doesn't believe it binds |
| `1_i_pTM`, `2_i_pTM` | **≥ 0.50** | higher | Per-model i_pTM | Same |
| `Average_i_pAE` | **≤ 0.35** | lower | Interface aligned error (normalized) | Interface position uncertain |
| `1_i_pAE`, `2_i_pAE` | **≤ 0.35** | lower | Per-model i_pAE | Same |
| `Average_Binder_pLDDT` | **≥ 0.80** | higher | Binder-alone confidence | Binder fold poorly predicted |
| `Average_Binder_RMSD` | **≤ 3.5 Å** | lower | RMSD between binder in-complex vs. alone | Binder changes fold when bound |
| `Average_Hotspot_RMSD` | **≤ 6.0 Å** | lower | Distance from intended hotspot residues | Binder lands on wrong site |

### 5b. Rosetta Interface Filters

Calculated by Rosetta after AF2 relaxation.

| Filter | Threshold | Direction | Meaning | Failure Mode |
|---|---|---|---|---|
| `Average_Binder_Energy_Score` | **< 0** | lower | Rosetta REU for binder alone | Binder not physically stable |
| `Average_dG` | **< 0** | lower | Binding free energy (REU). Negative = favorable | Unfavorable binding |
| `Average_dSASA` | **> 1** | higher | Buried surface area on binding | Too little contact |
| `Average_ShapeComplementarity` | **≥ 0.60** | higher | Geometric surface meshing (0-1) | Poor fit |
| `1_ShapeComplementarity` | **≥ 0.55** | higher | Per-model SC | Same |
| `Average_n_InterfaceResidues` | **≥ 7** | higher | Count of residues at interface | Interface too small |
| `Average_n_InterfaceHbonds` | **≥ 3** | higher | H-bonds across interface | Not enough specific contacts |
| `Average_n_InterfaceUnsatHbonds` | **≤ 4** | lower | Unsatisfied H-bond donors/acceptors | Buried polar groups = penalty |
| `Average_Surface_Hydrophobicity` | **< 0.35** | lower | Exposed hydrophobic surface | Aggregation-prone binder |
| `Average_Binder_Loop%` | **< 90%** | lower | % of binder in loops | Binder too unstructured |

### 5c. Interface Amino Acid Composition

Limits on specific residue types at the interface (prevents "cheating" via overrepresentation):

| Filter | Threshold | Meaning |
|---|---|---|
| `Average_InterfaceAAs_K` | **≤ 3** | Max lysine at interface |
| `Average_InterfaceAAs_M` | **≤ 3** | Max methionine at interface |

---

## 6. Run Control & Monitoring

| Parameter | Default | Meaning |
|---|---|---|
| `number_of_final_designs` | varies | Target number of accepted designs (e.g., 50). Run stops when reached. |
| `lengths` | `[60, 150]` | Min/max binder length (random in range per trajectory) |
| `acceptance_rate` | 0.01 | Minimum acceptance rate (1%) to continue run |
| `start_monitoring` | 600 | Start acceptance-rate monitoring after N trajectories |
| `max_trajectories` | `false` | Hard cap on trajectories (false = unlimited) |
| `enable_rejection_check` | `true` | If acceptance rate drops below threshold after monitoring starts, exit run |

---

## 7. Outcome Categories (Where Designs End Up)

```
output/
├── Accepted/
│   ├── Ranked/           ← FINAL accepted designs (what you want)
│   ├── Animation/        ← GIF of design process
│   ├── Pickle/           ← Saved design state
│   └── Plots/            ← Per-design plots
├── Trajectory/
│   ├── LowConfidence/    ← pLDDT checkpoint failure
│   ├── Clashing/         ← Severe steric clash
│   ├── Animation/        ← All trajectory animations
│   ├── Pickle/           ← Trajectory state
│   └── Plots/            ← Per-trajectory plots
├── MPNN/                 ← MPNN redesigned candidates (pre-filter)
├── failure_csv.csv       ← Tally of failures per filter (KEY DEBUG FILE)
├── final_design_stats.csv ← Stats for accepted designs
├── mpnn_design_stats.csv  ← Stats for all MPNN candidates
└── run_log_gpu*.txt      ← Live run logs
```

**failure_csv.csv columns = the filters listed in Section 5.** Non-zero values tell you exactly which filter is killing designs.

---

## 8. Typical Failure Signatures

| Symptom in Log | Likely Cause | Action |
|---|---|---|
| Many `"pLDDT too low to continue"` | Target surface too hard for AF2 / too flat | Try hardtarget settings, different hotspots |
| Many `"Severe clashes detected"` | Binder fold incompatible with target topology | Try longer binders, different secondary structure bias |
| `"No accepted MPNN designs"` + high `i_pTM` in failure_csv | MPNN sequences don't predict as binders | Relax i_pTM filter, try mpnn_weights="original" |
| `"Base AF2 filters not passed"` in many sequences | Trajectory is weak; MPNN can't rescue it | Run longer, tune loss weights |
| `failure_csv.csv` shows all MPNN failures on `Binder_Energy_Score` | Rosetta thinks binder is unstable | Increase `weights_plddt` or binder length |
| `failure_csv.csv` shows high `Hotspot_RMSD` failures | Binder binds wrong site | Redefine hotspots, increase `weights_con_inter` |

---

## 9. Advanced Preset Files

Located in `settings_advanced/`. Pick one based on target difficulty and desired binder topology.

| Preset | When to Use |
|---|---|
| `default_4stage_multimer.json` | Normal targets, mix of alpha/beta binders |
| `default_4stage_multimer_hardtarget.json` | Hard targets — relaxed loss, initial guess prediction |
| `default_4stage_multimer_flexible.json` | Flexible targets (loops, disordered regions) |
| `default_4stage_multimer_mpnn.json` | Aggressive MPNN redesign settings |
| `betasheet_4stage_multimer.json` | Force beta-sheet binder (`weights_helicity = -2.0`) |
| `betasheet_4stage_multimer_hardtarget.json` | Beta-sheet binder + hard target (used for AAV run 2) |
| `peptide_3stage_multimer.json` | Peptide binders (very short, 3-stage only) |

---

## 10. Filter Preset Files

Located in `settings_filters/`.

| Preset | Use Case |
|---|---|
| `default_filters.json` | Standard cutoffs (values in Section 5) |
| (You can create custom filters by copying and editing) | Relax specific thresholds for hard targets |

**To relax filters:** Copy `default_filters.json`, edit thresholds (e.g., lower `i_pTM` from 0.50 to 0.40), and pass via `--filters ./settings_filters/my_relaxed.json`.

---

## Quick Reference: The Most Important Numbers

| Metric | Cutoff | If Not Met |
|---|---|---|
| **Trajectory pLDDT** | ≥ 0.65 (internal) | Trajectory abandoned, no MPNN |
| **Binder pLDDT** | ≥ 0.80 | Filtered out after AF2 validation |
| **i_pTM** | ≥ 0.50 | Filtered out (most common failure) |
| **i_pAE** | ≤ 0.35 | Filtered out |
| **Binder RMSD** | ≤ 3.5 Å | Filtered out (binder refolds) |
| **Hotspot RMSD** | ≤ 6.0 Å | Filtered out (wrong site) |
| **dG (Rosetta)** | < 0 REU | Filtered out |
| **Shape Complementarity** | ≥ 0.60 | Filtered out |
| **n_InterfaceHbonds** | ≥ 3 | Filtered out |
| **n_InterfaceResidues** | ≥ 7 | Filtered out |

---

## 11. Glossary of Terms and Abbreviations

### AlphaFold2 & Structure Prediction

| Term | Definition |
|---|---|
| **AlphaFold2 (AF2)** | Deep learning model by DeepMind that predicts 3D protein structures from amino acid sequences and multiple sequence alignments. BindCraft inverts AF2 by optimizing sequences to minimize predicted loss. |
| **AF2 model weights** | AlphaFold2 has 5 sets of pre-trained model parameters; BindCraft evaluates designs across all 5 to measure consistency. Reported as `1_*`, `2_*`, ..., `5_*` metrics. |
| **Recycles** | Number of times AF2 iteratively refines its predictions within a single run. Higher recycles = more accurate but slower. BindCraft uses 1 recycle during design (fast) and 3 during validation (accurate). |
| **pLDDT** | **Predicted Local Distance Difference Test.** AF2's per-residue confidence score (0–100 in AF2 native; 0–1 in BindCraft). ~90+ = high confidence; <50 = unreliable prediction. |
| **pTM** | **Predicted TM-score.** Global confidence that the predicted fold is correct, measured on the TM-score scale (0–1). TM >0.5 indicates correct fold for related structures. |
| **i_pTM** | **Interface pTM.** Predicted TM-score specifically for the binder–target interface geometry. Most critical metric for binding. ≥0.50 = AF2 believes the binder binds. |
| **pAE** | **Predicted Aligned Error.** AF2's estimate of positional uncertainty (in Å) for each residue pair. Low pAE = high confidence in relative positioning. |
| **i_pAE** | **Interface pAE.** PAE averaged over binder–target residue pairs. Normalized to 0–1 scale in BindCraft (divide by max possible pAE ≈ 31 Å). Lower = more confident interface. |

### Design & Optimization

| Term | Definition |
|---|---|
| **Design loss** | Weighted sum of multiple objectives (pLDDT, pAE, contacts, helicity, etc.) that gradient descent minimizes during trajectory optimization. NOT a validation cutoff — a continuous training signal. |
| **Loss weights** | Scalar multipliers (e.g. `weights_iptm = 0.05`) controlling how much each component contributes to the design loss. Tune these to bias the optimizer toward desired binder properties. |
| **Trajectory** | One complete design optimization pass. Starts with a random sequence, runs through 4 stages of gradient descent on the loss function, ends with a backbone. Each trajectory may fail (LowConfidence, Clashing) or succeed (→ MPNN). |
| **4-stage design algorithm** | Four increasingly discrete optimization phases: (1) Logits — soft gradients on log-probabilities; (2) Softmax — over probability distributions; (3) One-hot — discrete amino acid selection; (4) Semigreedy — local refinement of selected positions. |
| **Logits** | Unnormalized log-probabilities of amino acid identities at each position. Stage 1 optimizes these with high gradient flow (soft). |
| **Softmax** | Normalized probability distribution over amino acids at each position. Stage 2 refines these distributions. |
| **One-hot** | Discrete (0/1) selection of a single amino acid per position. Stage 3 commits to hard choices; backbone must satisfy these constraints. |
| **Semigreedy** | Stage 4: starting from one-hot selections, randomly perturb a small fraction of positions and accept improvements. Fast local optimization. |
| **Gradient descent** | Optimization algorithm: iteratively move in the direction that decreases the loss. BindCraft uses Adam optimizer with adaptive learning rates. |
| **Hallucination** | Inverting AlphaFold2: instead of predicting structure given sequence, we optimize sequence to generate a structure predicted to bind the target. All four stages perform hallucination. |

### ProteinMPNN & Sequence Design

| Term | Definition |
|---|---|
| **ProteinMPNN** | Neural network for sequence design conditioned on a fixed protein backbone. Given a backbone, MPNN samples diverse amino acid sequences likely to fold into that backbone. Trained on soluble proteins (vs. membrane proteins). |
| **Sequence redesign** | MPNN stage: after a backbone is generated, MPNN produces 20 variants per backbone, with interface residues optionally fixed to ensure binding. Provides robustness — a weak backbone may be rescued by a good sequence. |
| **MPNN_score** | MPNN's log-likelihood (negative, lower = more confident). Ranges from ~−500 to −50 depending on sequence complexity. Not directly a filter cutoff, but reported for reference. |
| **Sequence recovery** | Fraction of original (template) residues that MPNN re-samples identically. High recovery = conservative design; low = diverse. BindCraft uses low sampling temperature (0.1) to bias toward consistency. |
| **Sampling temperature** | MPNN parameter (0.0–1.0+). Lower = more conservative, samples the same sequences repeatedly. Higher = more diverse. BindCraft default is 0.1 (low diversity, high confidence). |
| **Interface residues fixed** | Option to prevent MPNN from changing amino acids at the binder–target interface, ensuring the interaction remains as designed. Default: true. |
| **omit_AAs** | Amino acids MPNN is forbidden from sampling. BindCraft omits cysteine (C) by default to avoid disulfide complications. |

### Rosetta & Energy Terms

| Term | Definition |
|---|---|
| **Rosetta** | Molecular modeling suite for protein design, refinement, and analysis. BindCraft uses Rosetta to (1) relax predicted AF2 structures with physics-based energy minimization, and (2) score interface energetics. |
| **Relaxation** | Energy minimization: Rosetta adjusts atomic coordinates to minimize its energy function (van der Waals, electrostatics, solvation, hydrogen bonds). Cleans up geometric clashes. |
| **REU** | **Rosetta Energy Unit.** Dimensionless energy term approximating kcal/mol. Negative = favorable; positive = unfavorable. Exact conversion factor is application-dependent. |
| **dG** | **Binding free energy (ΔG).** Rosetta's estimate of the Gibbs free energy of binding (REU). Negative = favorable; < −5 REU is typically very favorable. Calculated via interface energy minus solvation cost. |
| **dSASA** | **Change in Solvent-Accessible Surface Area.** Buried area when binder and target bind (Å²). Positive dSASA = interfaces hide hydrophobic surface from solvent. Strong binders bury 1500–4500 Å². |
| **Binder Energy Score** | Rosetta total energy of the binder predicted alone. Negative = stable fold; positive = strained or incompletely packed. Filter cutoff: < 0 REU. |
| **Shape Complementarity (SC)** | Rosetta metric (0–1) quantifying how well two surfaces fit together geometrically, like a lock and key. 0.6–0.7 is good for proteins; >0.75 is excellent. Uses Lawrence–Colman algorithm. |
| **PackStat** | Rosetta packing score (0–1). Fraction of the protein volume occupied by atoms (van der Waals packing efficiency). >0.6 indicates good packing. |

### Interface & Binding Metrics

| Term | Definition |
|---|---|
| **Interface** | Region of contact between binder and target; defined as residues within a distance cutoff (typically 8 Å, CA-CA). |
| **n_InterfaceResidues** | Count of binder residues within contact distance of the target. Minimum viable: ≥ 7. Larger = more interaction surface. |
| **n_InterfaceHbonds** | Number of hydrogen bonds across the binder–target interface. Each hydrogen bond provides specificity and stabilization. Filter: ≥ 3. |
| **n_InterfaceUnsatHbonds** | Count of polar groups (H-bond donors/acceptors) that are buried at the interface but lack a hydrogen-bond partner. Each costs ≈ 1–2 kcal/mol. Filter: ≤ 4 (or 6 relaxed). |
| **Interface SASA** | Solvent-accessible surface area at the interface. Buried SASA (dSASA) is the main driving force for binding. |
| **Interface Hydrophobicity** | Average hydrophobicity of residues at the interface. Hydrophobic contacts are favorable; hydrophilic interfaces are weaker. |
| **Surface Hydrophobicity** | Fraction of the binder's surface that is hydrophobic (not buried, not in interface). High values (>0.45) indicate aggregation risk. Filter: < 0.35. |
| **Contact distance** | Distance threshold (typically 8 Å, measured CA-CA for Cα atoms) used to define the interface. Residues closer than this are considered in contact. |
| **CA-CA distance** | Distance between alpha-carbon (CA) atoms of two residues. Used to determine clash and contact definitions. Typical van der Waals clash: <3 Å. |

### Structure & Geometry

| Term | Definition |
|---|---|
| **Backbone** | The polypeptide chain atoms (N, CA, C, O); excludes side chains. Backbone geometry is determined by phi/psi dihedral angles. |
| **Side chain** | Atoms hanging off the backbone (Cβ and beyond) that determine amino acid identity and chemical properties. |
| **RMSD** | **Root Mean Square Deviation.** Measure of structural divergence between two conformations (Å). Computed over CA atoms typically. RMSD = 0 means identical; >2 Å typically indicates significant change. |
| **Binder_RMSD** | RMSD of the binder backbone in the predicted complex vs. the binder alone. Tests if binding causes the binder to refold. Filter: ≤ 3.5 Å (stable binder). |
| **Hotspot_RMSD** | RMSD between the binder backbone and the user-specified hotspot residues on the target. Tests whether the binder lands on the intended site. Filter: ≤ 6.0 Å (on target). |
| **Target_RMSD** | RMSD between the input target structure and the AF2-predicted target structure. Should be ~0 for monomers (template-constrained). High values flag target distortion (e.g., dimer collapse). No hard filter, but >10 Å is suspicious. |
| **Clash** | Steric overlap between atoms (CA-CA distance <3 Å typically). Detected early and trajectories with severe clashes are abandoned. |
| **Helix** | Secondary structure where the backbone forms a right-handed coil stabilized by intra-chain hydrogen bonds (i → i+4). Compact, stable, good for binding. |
| **Beta-sheet** | Secondary structure where the backbone is extended and stabilized by inter-strand hydrogen bonds. Flat, extended, harder for AF2 to hallucinate. |
| **Loop / Coil** | Secondary structure regions with no regular hydrogen-bonding pattern. Flexible, structurally variable, can accommodate diverse sequences. |
| **Loop%** | Fraction of residues in loop/coil (vs. helix or sheet). High loop% (>90%) indicates an unstructured binder. Filter: < 90% (or 95% relaxed). |
| **Radius of gyration (Rg)** | Measure of protein compactness: average distance of atoms from the center of mass. Smaller Rg = more compact. BindCraft penalizes large Rg (weights_rg = 0.3). |
| **Dihedral angles (phi, psi)** | Angles (φ, ψ) defining the backbone conformation at each residue. Restricted by Ramachandran plot constraints. AF2 respects these implicitly. |

### BindCraft-Specific

| Term | Definition |
|---|---|
| **Hotspot residues** | User-defined target residues that the binder is designed to contact. Binder is scored on how close it approaches these residues (Hotspot_RMSD filter). |
| **Trajectory checkpoint** | Internal pLDDT threshold that kills a trajectory early if confidence drops (e.g., < 0.65). Hardcoded in BindCraft; not configurable. Prevents wasting compute on hopeless trajectories. |
| **LowConfidence trajectory** | A trajectory that failed a pLDDT checkpoint and was abandoned before reaching MPNN. Stored in `Trajectory/LowConfidence/` for debugging. |
| **Clashing trajectory** | A trajectory that generated severe atomic overlaps. Rejected before MPNN. Stored in `Trajectory/Clashing/`. Usually indicates the target topology is incompatible with the binder length. |
| **Acceptance rate** | Fraction of trajectories that yield at least one accepted MPNN-redesigned design. BindCraft monitors this after 600 trajectories and stops if it drops below 1%, indicating a bottleneck. |
| **Design time** | Wall-clock time (hours, minutes, seconds) required to run a single trajectory (design + validation). Typical: 4–6 minutes. |
| **Binder length** | Number of residues in the designed binder. Sampled uniformly per trajectory from `lengths = [min, max]`. |
| **Seed** | Random seed that, with design parameters held constant, produces the same backbone. Used to identify binders from the same trajectory for diversity analysis. |

### Protein Structure & Biology

| Term | Definition |
|---|---|
| **Monomer** | A single protein chain. Monomeric targets are simpler to design against but may miss quaternary epitopes. |
| **Dimer (homodimer)** | Two identical chains in complex. Often a good model for surface interaction without the complexity of a full capsid. |
| **Multimer** | Assembly of 3+ identical chains. BindCraft can design against multimers using AF2-Multimer (accounts for chain interfaces). |
| **Quaternary epitope** | Epitope (binding site) that spans residues from multiple protein chains. Requires multimer target to model accurately. Hard to design de novo because AF2-Multimer can reposition chains. |
| **Epitope** | Region of an antigen recognized by a binder (antibody, designed protein, etc.). |
| **Binder** | The designed protein (miniprotein, antibody, etc.) intended to bind the target. In BindCraft, binder length is 40–150 residues typical. |
| **Target** | The protein (or complex) against which the binder is designed to bind. Fixed during optimization (though AF2-Multimer can reposition chains). |
| **AAV** | **Adeno-Associated Virus.** Small DNA virus (~25 nm capsid) used as a vector for gene therapy. VP1/VP2/VP3 are the three capsid proteins, arranged in T=1 icosahedral symmetry (60 copies total). |
| **VP (viral protein)** | Subunit of the AAV capsid. VP1, VP2, VP3 form the 60-copy asymmetric assembly. |
| **Capsid** | Protein shell surrounding viral genetic material. AAV2 capsid is highly symmetric (icosahedral) and β-sheet-dominated (hard target). |
| **Serotype** | Variant of a virus (e.g., AAV2, AAV5, AAV9) with different cell-tropism and immunogenicity. |
| **PD-L1** | **Programmed Death Ligand 1.** Immune checkpoint protein; target of therapeutic antibodies. Used as a validation benchmark in BindCraft (easier target than AAV). |
| **Miniprotein** | Small protein (40–150 residues); no disulfide bonds typically. BindCraft designs miniproteins, not antibodies (which are larger). |

### Advanced Concepts

| Term | Definition |
|---|---|
| **Template** | Input structure (PDB file) used as a reference during AF2 prediction. BindCraft passes the target as a template hint (not a hard constraint). AF2 can override the template if predicted loss is lower elsewhere. |
| **Initial guess prediction** | Option (`predict_initial_guess = true`) to initialize AF2 with the input template structure, accelerating convergence for hard targets. Enabled in hardtarget presets. |
| **Big-bang initialization** | Default initialization strategy for non-hardtarget runs: random coordinates, let AF2 infer the structure from scratch. Slower but more exploratory. |
| **Multimer design** | Designing a binder against a multi-chain target using AF2-Multimer, which accounts for chain interactions. Powerful but risky: AF2 may reposition chains to minimize loss. |
| **Scaffold** | The overall fold/architecture of the designed binder. Different scaffolds (helix bundles, beta-sheets, mixed) have different properties. BindCraft does not restrict scaffold — pure hallucination. |
| **Amino acid composition** | Counts of each amino acid type (A, C, D, ..., Y) in a sequence. BindCraft applies filters on lysine (K) and methionine (M) at interfaces to prevent "cheating" via repeated residues. |
| **Aggregation-prone** | Sequence/structure likely to oligomerize or precipitate in solution. Detected by high surface hydrophobicity. |
| **Hydrophobic core** | Interior of a protein; predominantly hydrophobic amino acids. Necessary for stable folding. |
| **Amphipathic** | Region with both hydrophobic and hydrophilic character (e.g., helix at protein surface). Can stabilize interfaces. |
| **Secondary structure bias** | Loss weight (e.g., `weights_helicity = −0.3`) that preferentially pushes the optimizer toward (or away from) helix, sheet, or loop. Negative weight penalizes the structure; positive encourages it. |
| **Soluble protein MPNN** | MPNN model trained on soluble (non-membrane) proteins. Better for water-soluble binders; the "original" model was trained on membrane proteins. BindCraft uses soluble by default. |
