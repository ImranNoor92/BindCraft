#Step-by-Step Analysis Guide
"""
Step-by-step analysis guide for BindCraft design results.

This module provides a comprehensive framework for analyzing and visualizing
protein binder design statistics from BindCraft output files.

Step 1 - Load and Inspect Data:
    Loads the final design statistics CSV and provides an overview of the
    total number of designs and key performance metrics for the top candidates.

Step 2 - Rank Top Candidates:
    Sorts designs by interface pTM (i_pTM) score in descending order to
    identify the most promising binder candidates.

Step 3 - Understand Key Metrics:
    Displays summary statistics for all critical evaluation metrics including
    binding affinity, structural quality, and interface properties.

Step 4 - Plot Score Distributions:
    Generates histograms for 8 key metrics with mean values overlaid.
    Distributions tell if designs cluster around good values or if only
    a few outliers look promising. A tight distribution at high i_pTM means
    consistent quality.

Step 5 - Correlation Analysis:
    Creates a heatmap showing how metrics move together. Strong correlations
    confirm metrics measure the same quality (e.g., dG and i_pTM). Negative
    correlations reveal inverse relationships (e.g., Binder_RMSD vs i_pTM),
    confirming structurally consistent binders have better predicted affinity.

Step 6 - Scatter Plot Analysis:
    Visualizes the two most important metrics (i_pTM vs dG) with Shape
    Complementarity as color gradient. Best designs sit in top-left (high i_pTM,
    very negative dG) and are dark-colored (high shape complementarity).

Step 7 - Select Final Candidates:
    Applies strict cutoff filters to shortlist best candidates for wet lab
    testing. Filters for high binding confidence (i_pTM ≥ 0.80), favorable
    interface energy (dG < -40), good shape fit (SC ≥ 0.60), structural
    consistency (RMSD < 2.0 Å), and clean interface (few unsatisfied H-bonds).

Step 8 - Visualize Top Design Structures:
    Lists accepted PDB files and provides guidance for visual inspection in
    PyMOL. Checks for snug binder-target interface fit, absence of gaps/clashes,
    and well-defined secondary structure (helices/sheets vs loops).
"""


###################################################
#####################Step 1########################
###################################################
#Step 1 — Load and inspect the data
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys

OUTPUT_DIR = '/data/binder_software/BindCraft/example/output/'

# Redirect all print output to both terminal AND a log file
class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

log_file = open(OUTPUT_DIR + 'analysis_summary.txt', 'w')
sys.stdout = Tee(sys.__stdout__, log_file)

df = pd.read_csv(OUTPUT_DIR + 'final_design_stats.csv')

print(f"Total designs: {len(df)}")
print(f"\nFirst 5 designs:")
print(df[['Rank', 'Design', 'Length', 'Average_i_pTM', 'Average_pLDDT', 'Average_dG', 'Average_ShapeComplementarity', 'Average_Binder_RMSD']].head())
# Gives me an overview —how many designs passed all filters, their lengths, and a snapshot of the key scores.


###################################################
#####################Step 2########################
###################################################
#step 2 — Rank your top candidates
# The file is already ranked, but let's sort by the most important metric: i_pTM
top = df.sort_values('Average_i_pTM', ascending=False)

top_cols = ['Rank', 'Design', 'Length',
            'Average_i_pTM', 'Average_pLDDT', 'Average_dG',
            'Average_ShapeComplementarity', 'Average_Binder_RMSD',
            'Average_n_InterfaceHbonds']

print("\n--- TOP 20 DESIGNS RANKED BY i_pTM ---")
print(top[top_cols].head(20).to_string())

# Save full ranked table to CSV
top[top_cols].to_csv(OUTPUT_DIR + 'ranked_designs.csv', index=False)


###################################################
#####################Step 3########################
###################################################
#Step 3 — Understand what each key metric means
key_metrics = [
    'Average_i_pTM',
    'Average_pLDDT',
    'Average_dG',
    'Average_ShapeComplementarity',
    'Average_Binder_RMSD',
    'Average_n_InterfaceHbonds',
    'Average_n_InterfaceUnsatHbonds',
    'Average_Surface_Hydrophobicity'
]

print("\n--- KEY METRICS SUMMARY STATISTICS ---")
print(df[key_metrics].describe().round(3))

# Save metrics summary to CSV
df[key_metrics].describe().round(3).to_csv(OUTPUT_DIR + 'metrics_summary.csv')
#see glossary.md for detailed explanations of each metric. This summary gives me a sense of the range and distribution of scores across my designs.  



###################################################
#####################Step 4########################
###################################################
#Step 4 — Plot score distributions
fig, axes = plt.subplots(2, 4, figsize=(18, 8))
fig.suptitle('BindCraft PDL1 Design Score Distributions', fontsize=14)

metrics = [
    ('Average_i_pTM', 'Interface pTM (higher=better)'),
    ('Average_pLDDT', 'pLDDT (higher=better)'),
    ('Average_dG', 'Interface dG kcal/mol (lower=better)'),
    ('Average_ShapeComplementarity', 'Shape Complementarity (higher=better)'),
    ('Average_Binder_RMSD', 'Binder RMSD Å (lower=better)'),
    ('Average_n_InterfaceHbonds', 'Interface H-bonds (higher=better)'),
    ('Average_n_InterfaceUnsatHbonds', 'Unsat H-bonds (lower=better)'),
    ('Average_Surface_Hydrophobicity', 'Surface Hydrophobicity (lower=better)'),
]

for ax, (col, title) in zip(axes.flatten(), metrics):
    ax.hist(df[col].dropna(), bins=20, color='steelblue', edgecolor='white')
    ax.set_title(title, fontsize=9)
    ax.axvline(df[col].mean(), color='red', linestyle='--', label='mean')
    ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig('/data/binder_software/BindCraft/example/output/score_distributions.png', dpi=150)
plt.show()
#Why: Distributions tell me if your designs cluster around good values or if only a few outliers look promising. 
# A tight distribution at high i_pTM means consistent quality.


###################################################
#####################Step 5########################
###################################################
#step 5 — Correlation plot (find what drives good binding)
corr_cols = [
    'Average_i_pTM', 'Average_pLDDT', 'Average_dG',
    'Average_ShapeComplementarity', 'Average_Binder_RMSD',
    'Average_n_InterfaceHbonds', 'Average_n_InterfaceUnsatHbonds',
    'Average_dSASA', 'Average_Surface_Hydrophobicity', 'Length'
]

corr = df[corr_cols].corr()

plt.figure(figsize=(12, 10))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            square=True, linewidths=0.5)
plt.title('Score Correlation Matrix')
plt.tight_layout()
plt.savefig('/data/binder_software/BindCraft/example/output/correlation_matrix.png', dpi=150)
plt.show()
#Why: Shows which metrics move together.
#  For example, if dG strongly correlates with i_pTM, that confirms both are measuring the same thing (good).
#  If Binder_RMSD negatively correlates with i_pTM, it confirms that structurally consistent binders also have better predicted affinity.



###################################################
#####################Step 6########################
###################################################
# Step 6 — Scatter plot: the two most important metrics
plt.figure(figsize=(10, 7))
scatter = plt.scatter(
    df['Average_i_pTM'],
    df['Average_dG'],
    c=df['Average_ShapeComplementarity'],
    cmap='viridis',
    s=60, alpha=0.7
)
plt.colorbar(scatter, label='Shape Complementarity')
plt.xlabel('Average i_pTM (higher = better binding confidence)')
plt.ylabel('Average dG kcal/mol (more negative = stronger binding energy)')
plt.title('PDL1 Binder Designs: i_pTM vs dG')

# Label your top 5
for _, row in df.head(5).iterrows():
    plt.annotate(row['Design'].split('_mpnn')[0],
                 (row['Average_i_pTM'], row['Average_dG']),
                 fontsize=7, ha='left')

plt.tight_layout()
plt.savefig('/data/binder_software/BindCraft/example/output/iptm_vs_dg.png', dpi=150)
plt.show()
#Why: The best designs sit in the top-left (high i_pTM, very negative dG) AND are colored dark (high shape complementarity). These are my best candidates to order for experimental testing



###################################################
#####################Step 7########################
###################################################
#step 7 — Select final candidates to order
# Apply strict cutoffs to shortlist best candidates
candidates = df[
    (df['Average_i_pTM'] >= 0.80) &
    (df['Average_dG'] < -40) &
    (df['Average_ShapeComplementarity'] >= 0.60) &
    (df['Average_Binder_RMSD'] < 2.0) &
    (df['Average_n_InterfaceUnsatHbonds'] <= 3)
].sort_values('Average_i_pTM', ascending=False)

print(f"Candidates passing strict filters: {len(candidates)}")
print(candidates[['Rank', 'Design', 'Length', 'Sequence',
                   'Average_i_pTM', 'Average_dG',
                   'Average_ShapeComplementarity',
                   'Average_Binder_RMSD']].to_string())

# Save shortlist
candidates.to_csv('/data/binder_software/BindCraft/example/output/top_candidates.csv', index=False)
#Why: From hundreds of designs, you only want to order 5–20 for wet lab testing. These cutoffs filter for:
    #High AF2 binding confidence (i_pTM ≥ 0.80)
    #Favorable interface energy (dG < -40)
    #Good shape fit (SC ≥ 0.60)
    #Structural consistency (RMSD < 2.0 Å) — if a binder only folds correctly in the presence of the target, it's risky
    #Clean interface (few unsatisfied H-bonds)


###################################################
#####################Step 8########################
###################################################
# Step 8 — Visualize the top design structures
# After identifying top candidates, run these in your TERMINAL (not Python):
#
#   ls /data/binder_software/BindCraft/example/output/Accepted/
#
#   pymol /data/binder_software/BindCraft/example/output/Accepted/PDL1_l131_s667087_mpnn12*.pdb
#
import os
accepted_dir = '/data/binder_software/BindCraft/example/output/Accepted/'
pdb_files = [f for f in os.listdir(accepted_dir) if f.endswith('.pdb')]
print(f"\nAccepted PDB files ({len(pdb_files)} total):")
for f in sorted(pdb_files):
    print(f"  {f}")
#What to look for visually:
    #Does the binder sit snugly against the target hotspot (residue 56)?
    #Are there obvious gaps or clashes at the interface?
    #Does the binder have a defined secondary structure (helices/sheets) or is it mostly loops?

#Summary: What to prioritize when choosing designs to order
#Priority	 Metric	                           Your Rank 1 value
# 1st	     Average_i_pTM	                   0.88 (excellent)
# 2nd	     Average_dG	                       -54.41 (strong)
# 3rd	     Average_ShapeComplementarity	   0.65 (good)
# 4th	     Average_Binder_RMSD	           1.02 (excellent — very stable)
#5 th	     Average_n_InterfaceUnsatHbonds	   3.0 (acceptable)

print("\n--- OUTPUT FILES SAVED ---")
print(f"  analysis_summary.txt  — full terminal log")
print(f"  ranked_designs.csv    — all designs ranked by i_pTM")
print(f"  metrics_summary.csv   — key metrics statistics")
print(f"  top_candidates.csv    — designs passing strict filters")
print(f"  score_distributions.png")
print(f"  correlation_matrix.png")
print(f"  iptm_vs_dg.png")

# Close the log file
sys.stdout = sys.__stdout__
log_file.close()