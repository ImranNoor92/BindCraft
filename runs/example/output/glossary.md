
# BindCraft Metrics Glossary

| Metric | What it measures | Good value |
|--------|------------------|-----------|
| Average_i_pTM | AF2's confidence that binding actually occurs | Higher → better (>0.6 is good, your top is 0.88) |
| Average_pLDDT | Overall structural confidence of the complex | Higher → better (>0.8, your designs are ~0.93–0.94) |
| Average_dG | Rosetta interface binding energy (kcal/mol) | More negative → stronger predicted binding |
| Average_ShapeComplementarity | How well binder surface fits target surface | Higher → better (0–1 scale, >0.6 is good) |
| Average_Binder_RMSD | How much the binder drifts when repredicted alone vs. in complex | Lower → better (your designs ~1.0–1.2 Å, excellent) |
| Average_n_InterfaceHbonds | Number of hydrogen bonds at the interface | Higher → more stable interface |
| Average_n_InterfaceUnsatHbonds | Buried H-bond donors/acceptors with no partner | Lower → better (unsatisfied ones destabilize binding) |
| Average_Surface_Hydrophobicity | Fraction of exposed hydrophobic surface on binder | Lower → better (high hydrophobicity = aggregation risk) |
