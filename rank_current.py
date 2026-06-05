#!/usr/bin/env python
"""
Rank currently-accepted BindCraft designs WITHOUT stopping the run.
Mirrors the built-in ranker: sort by Average_i_pTM descending, copy into Ranked/.

Usage:
    python rank_current.py --output_dir ./15delt3.pdb/output
"""
import argparse
import os
import shutil
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output_dir", "-o", required=True)
    args = ap.parse_args()

    out = os.path.abspath(args.output_dir)
    accepted_dir = os.path.join(out, "Accepted")
    ranked_dir = os.path.join(accepted_dir, "Ranked")
    mpnn_csv = os.path.join(out, "mpnn_design_stats.csv")

    os.makedirs(ranked_dir, exist_ok=True)

    accepted = [f for f in os.listdir(accepted_dir)
                if f.endswith(".pdb") and not f.startswith(".")]
    print(f"Found {len(accepted)} accepted PDBs in {accepted_dir}")

    df = pd.read_csv(mpnn_csv).sort_values("Average_i_pTM", ascending=False)

    for f in os.listdir(ranked_dir):
        os.remove(os.path.join(ranked_dir, f))

    rank = 1
    summary = []
    for _, row in df.iterrows():
        for binder in accepted:
            name, model = binder.rsplit("_model", 1)
            if name == row["Design"]:
                new_path = os.path.join(
                    ranked_dir, f"{rank}_{name}_model{model.rsplit('.', 1)[0]}.pdb"
                )
                shutil.copyfile(os.path.join(accepted_dir, binder), new_path)
                summary.append({
                    "Rank": rank,
                    "Design": name,
                    "Length": row.get("Length"),
                    "i_pTM": row.get("Average_i_pTM"),
                    "i_pAE": row.get("Average_i_pAE"),
                    "pLDDT": row.get("Average_pLDDT"),
                    "dG": row.get("Average_dG"),
                    "ShapeComp": row.get("Average_ShapeComplementarity"),
                    "Binder_RMSD": row.get("Average_Binder_RMSD"),
                    "Hotspot_RMSD": row.get("Average_Hotspot_RMSD"),
                    "Target_RMSD": row.get("Average_Target_RMSD"),
                })
                rank += 1
                break

    sdf = pd.DataFrame(summary)
    out_csv = os.path.join(out, "ranked_current.csv")
    sdf.to_csv(out_csv, index=False)
    print(f"Ranked {len(sdf)} designs → {ranked_dir}")
    print(f"Summary CSV → {out_csv}")
    print()
    print(sdf.to_string(index=False))


if __name__ == "__main__":
    main()
