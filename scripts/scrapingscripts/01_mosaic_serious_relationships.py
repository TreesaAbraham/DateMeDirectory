#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_csv", required=True, help="Path to input CSV")
    parser.add_argument("--out", dest="out_png", required=True, help="Path to output PNG")
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--theme", default="whitegrid", choices=["whitegrid", "darkgrid", "white", "dark", "ticks"])
    parser.add_argument("--context", default="paper", choices=["paper", "notebook", "talk", "poster"])
    args = parser.parse_args()

    in_csv = Path(args.in_csv)
    out_png = Path(args.out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)

    sns.set_theme(style=args.theme, context=args.context)

    df = pd.read_csv(in_csv)

    # TODO: your plot code here
    # Example scaffold:
    fig, ax = plt.subplots()
    ax.text(0.5, 0.5, "replace me", ha="center", va="center")
    ax.axis("off")

    fig.tight_layout()
    fig.savefig(out_png, dpi=args.dpi)
    plt.close(fig)


if __name__ == "__main__":
    main()
