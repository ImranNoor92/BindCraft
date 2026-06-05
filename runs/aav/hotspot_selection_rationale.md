# BindCraft Hotspot Selection for Assembled AAV2 Capsid Binding  
**Target:** `BindCraft/AAV/1LP3_trimer_fixed.pdb`

---

## Overview

This guide explains how to choose `target_hotspot_residues` in BindCraft for designing a binder against the **assembled AAV2 capsid**, using a **3-chain trimer** derived from `1LP3`.

The goal is **not** necessarily to mimic A20 exactly. Instead, the main design objective is:

> Create a binder that prefers the **assembled capsid surface** rather than an isolated VP monomer.

Because of that, the hotspot residues should ideally define a **quaternary epitope** — a surface patch that exists only, or much more clearly, in the assembled trimer/capsid geometry.

---

## Biological Goal

### Desired outcome
Design a binder that recognizes the **assembled T=1 AAV2 capsid surface**.

### Not required
- It does **not** have to bind the exact same patch as A20
- It does **not** have to compete with A20
- It does **not** have to target a monomer-specific surface

### Preferred property
The binder should favor a **capsid-dependent surface patch**, ideally near the **3-fold axis**, where residues from multiple monomers contribute to the final binding surface.

---

## Input Structure

### Target PDB
```bash
BindCraft/AAV/1LP3_trimer_fixed.pdb
```

### Structure type

* AAV2 trimer
* 3 full VP monomer chains
* Used as a local model of assembled capsid geometry

### Chains

* `A`
* `B`
* `C`

---

## Why a Trimer Should Be Used Instead of a Monomer

Using the trimer is the correct choice for this project because the desired binder should recognize an **assembled capsid surface**, not a monomer in isolation.

If only one monomer is used as the target:

* BindCraft may design a binder to a surface that also exists on the isolated monomer
* This weakens the assembly-specific design logic

If the trimer is used:

* BindCraft can “see” the local quaternary geometry
* Hotspots can be chosen across multiple chains
* The resulting binder is more likely to recognize a **capsid-like epitope**

---

## Important Numbering Note

The hotspot residue numbering below assumes that my file:

```bash
BindCraft/AAV/1LP3_trimer_fixed.pdb
```

still uses residue numbering consistent with the canonical `1LP3` numbering.

That means residues such as:

* 261
* 263
* 264
* 381
* 384
* 385
* 548
* 658
* 659
* 660
* 708

are assumed to appear in the PDB exactly with those numbers.

If the structure was renumbered during preprocessing, these hotspot selections must be remapped.

---

## Design Principle for `target_hotspot_residues`

The hotspot list should not simply be a long list of every residue ever associated with antibody binding.

Instead, it should do something specific:

1. Focus the binder toward a **physically coherent surface patch**
2. Bias the design toward a **multi-chain / quaternary epitope**
3. Encourage binding near the **3-fold region**
4. Keep the hotspot list small enough to remain meaningful

In short:

> A tight, multi-chain hotspot set is usually better than a broad, scattered hotspot set.

---

## Recommended Hotspot Strategies

It is best to test **multiple hotspot sets** rather than relying on just one.

Three recommended hotspot schemes are listed below.

---

# Option 1 — Tight Quaternary 3-Fold Patch

**Recommended first pass**

This is the best starting point for my project.

It uses a compact hotspot set centered near the 3-fold region and spread across multiple chains, which helps bias the design toward assembled capsid recognition.

## Hotspot residues

```text
A261,A263,A264,B381,B384,B385,C381,C384,C385
```

## Why this is the best first option

* Compact and focused
* Multi-chain
* Strongly biased toward quaternary recognition
* Most aligned with the goal of targeting assembled capsid rather than monomer

---

# Option 2 — Balanced Quaternary Patch

**Good second pass**

This expands the same core region slightly by adding residues that may broaden the available contact surface.

## Hotspot residues

```text
A261,A263,A264,B381,B384,B385,C381,C384,C385,B548,C658,C659,C660
```

## Why use this

* Preserves the core trimer-focused patch
* Adds more surface context
* May help if the first hotspot set is too restrictive

## Tradeoff

* Broader target surface
* Slightly less sharply focused than Option 1

---

# Option 3 — Broad Exploratory Quaternary Patch

**Use after trying the first two**

This version adds `708` to create a larger exploratory patch.

## Hotspot residues

```text
A261,A263,A264,B381,B384,B385,C381,C384,C385,B548,C658,C659,C660,A708
```

## Why use this

* Allows exploration of a larger capsid-facing patch
* May help if binders need more interface area

## Tradeoff

* More diffuse
* Less constrained
* Higher chance of drifting away from a tight 3-fold-centered mode

---

## My Main Recommendation

If starting from scratch, use this first:

```text
A261,A263,A264,B381,B384,B385,C381,C384,C385
```

This is the cleanest and most biologically consistent hotspot definition for my goal.

It best matches the requirement:

> Design a binder that recognizes assembled capsid geometry rather than a monomeric surface.

---

## Recommended BindCraft Input Examples

### Option 1 — Tight Quaternary 3-Fold Patch

```json
{
  "target_pdb": "BindCraft/AAV/1LP3_trimer_fixed.pdb",
  "target_chain": "ABC",
  "target_hotspot_residues": "A261,A263,A264,B381,B384,B385,C381,C384,C385"
}
```

### Option 2 — Balanced Quaternary Patch

```json
{
  "target_pdb": "BindCraft/AAV/1LP3_trimer_fixed.pdb",
  "target_chain": "ABC",
  "target_hotspot_residues": "A261,A263,A264,B381,B384,B385,C381,C384,C385,B548,C658,C659,C660"
}
```

### Option 3 — Broad Exploratory Patch

```json
{
  "target_pdb": "BindCraft/AAV/1LP3_trimer_fixed.pdb",
  "target_chain": "ABC",
  "target_hotspot_residues": "A261,A263,A264,B381,B384,B385,C381,C384,C385,B548,C658,C659,C660,A708"
}
```

---

## Important Note About JSON Comments

Standard JSON does **not** allow comments.

So this is **not valid JSON**:

```javascript
{
  // target is the trimer
  "target_pdb": "BindCraft/AAV/1LP3_trimer_fixed.pdb",

  // use all 3 chains
  "target_chain": "ABC",

  // multi-chain hotspot near the 3-fold region
  "target_hotspot_residues": "A261,A263,A264,B381,B384,B385,C381,C384,C385"
}
```

Use comments only in documentation or pseudo-config examples.
For actual BindCraft runs, remove all comments.

---

## Why Multi-Chain Hotspots Are Better for This Project

A single-chain hotspot could still produce a binder that recognizes an exposed monomer surface.

That is not ideal for this project.

A multi-chain hotspot is better because it tells BindCraft:

> Design around a surface that makes sense in the assembled capsid context.

This does **not** guarantee perfect assembly-specific recognition, but it increases the probability that the resulting binder will prefer a capsid-like geometry.

---

## Suggested Run Order

Run the hotspot schemes in this order:

1. **Option 1 — Tight quaternary patch**
2. **Option 2 — Balanced patch**
3. **Option 3 — Broad exploratory patch**

This gives a good progression from:

* highly focused
* to moderately broad
* to exploratory

---

## Post-Design Evaluation Checklist

After BindCraft generates candidate binders, inspect the models and ask:

### 1. Does the binder contact more than one chain?

This is one of the strongest indicators that the design is truly quaternary.

### 2. Is the interface centered near the intended 3-fold region?

The binder should not drift far away from the intended capsid patch.

### 3. Could the same binder plausibly bind an isolated monomer?

If yes, that is less ideal for the project goal.

### 4. Does the binder clash with neighboring capsid geometry?

A local trimer model may look acceptable while the full capsid context may introduce steric clashes.

### 5. Is the interface compact and continuous?

A good binder should not make only weak or scattered contacts.

---

## Practical Recommendation

### Best starting configuration

```json
{
  "target_pdb": "BindCraft/AAV/1LP3_trimer_fixed.pdb",
  "target_chain": "ABC",
  "target_hotspot_residues": "A261,A263,A264,B381,B384,B385,C381,C384,C385"
}
```

This is the best first-choice configuration because it is:

* trimer-aware
* compact
* multi-chain
* assembly-biased
* centered on a known conformational surface region

---

## Summary

For m project, the most sensible design logic is:

* use the **AAV2 trimer**
* include **all three chains**
* choose **multi-chain hotspot residues**
* bias the design toward the **3-fold region**
* start with a **tight quaternary hotspot set**
* test broader sets only after that

### Final recommended hotspot set

```text
A261,A263,A264,B381,B384,B385,C381,C384,C385
```

---

## Quick Copy Block

```json
{
  "target_pdb": "BindCraft/AAV/1LP3_trimer_fixed.pdb",
  "target_chain": "ABC",
  "target_hotspot_residues": "A261,A263,A264,B381,B384,B385,C381,C384,C385"
}
```

---

## Project Note

This hotspot strategy is intended to bias binder design toward the **assembled AAV2 capsid surface** rather than an isolated VP monomer. It does not enforce A20 competition specifically, but it uses a trimer-centered, conformationally relevant surface patch that is well suited for assembly-aware binder design.
