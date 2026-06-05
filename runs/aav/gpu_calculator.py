"""
BindCraft GPU Memory & Time Calculator

Usage:
    python gpu_calculator.py --target 450 --binder_min 60 --binder_max 120 --gpu_vram 48

Formulas derived from empirical BindCraft runs on RTX 6000 Ada (48 GB):
    VRAM (GB) ≈ n² / 12,500  (where n = target + binder residues)
    Time/trajectory (min) ≈ (n / 250)^2.5
"""
import argparse
import math

def calculate(target_residues, binder_min, binder_max, gpu_vram_gb):
    print(f"{'='*60}")
    print(f"BindCraft GPU Resource Calculator")
    print(f"{'='*60}")
    print(f"Target residues:  {target_residues}")
    print(f"Binder range:     {binder_min}-{binder_max} aa")
    print(f"GPU VRAM:         {gpu_vram_gb} GB")
    print(f"{'='*60}\n")

    # Best case (smallest binder)
    n_min = target_residues + binder_min
    vram_min = n_min**2 / 12500
    time_min = (n_min / 250)**2.5

    # Worst case (largest binder)
    n_max = target_residues + binder_max
    vram_max = n_max**2 / 12500
    time_max = (n_max / 250)**2.5

    print(f"  Binder {binder_min} aa (best case):")
    print(f"    Total residues:     {n_min}")
    print(f"    Estimated VRAM:     {vram_min:.1f} GB")
    print(f"    Time/trajectory:    ~{time_min:.1f} min")
    print()
    print(f"  Binder {binder_max} aa (worst case):")
    print(f"    Total residues:     {n_max}")
    print(f"    Estimated VRAM:     {vram_max:.1f} GB")
    print(f"    Time/trajectory:    ~{time_max:.1f} min")
    print()

    # Will it fit?
    safe_vram = gpu_vram_gb * 0.85  # leave 15% headroom
    if vram_max <= safe_vram:
        print(f"  ✓ FITS in {gpu_vram_gb} GB GPU (with 15% headroom)")
    elif vram_min <= safe_vram:
        # Find max binder that fits
        max_n = math.sqrt(safe_vram * 12500)
        max_binder = int(max_n - target_residues)
        print(f"  ⚠ PARTIAL FIT — reduce max binder length to {max_binder} aa")
        print(f"    At binder {max_binder}: {(target_residues + max_binder)**2 / 12500:.1f} GB")
    else:
        # Find required target trim
        max_n = math.sqrt(safe_vram * 12500)
        max_target = int(max_n - binder_max)
        print(f"  ✗ DOES NOT FIT — need to trim target to ~{max_target} residues")
        print(f"    Or use a GPU with ≥{math.ceil(vram_max / 0.85)} GB VRAM")

    # Time estimate for 100 designs
    avg_time = (time_min + time_max) / 2
    # Assume ~5% acceptance rate for hard targets
    trajectories_needed = 100 / 0.05
    total_hours = (trajectories_needed * avg_time) / 60
    print(f"\n  Time estimate for 100 final designs (~5% acceptance):")
    print(f"    ~{int(trajectories_needed)} trajectories needed")
    print(f"    ~{total_hours:.0f} hours ({total_hours/24:.1f} days) on 1 GPU")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BindCraft GPU Resource Calculator")
    parser.add_argument("--target", type=int, required=True, help="Total target residues in PDB")
    parser.add_argument("--binder_min", type=int, default=60, help="Min binder length")
    parser.add_argument("--binder_max", type=int, default=120, help="Max binder length")
    parser.add_argument("--gpu_vram", type=float, default=48, help="GPU VRAM in GB")
    args = parser.parse_args()
    calculate(args.target, args.binder_min, args.binder_max, args.gpu_vram)
