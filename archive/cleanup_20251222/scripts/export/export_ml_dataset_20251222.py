#!/usr/bin/env python3
"""Export ML-ready dataset from PostgreSQL."""

from pathlib import Path
import pandas as pd
from datetime import datetime
from chainguardian.database.manager import DatabaseManager  # uses your DB manager

def main() -> None:
    db = DatabaseManager()

    # Pull full joined feature view
    df = db.get_all_features()

    # Drop failed analyses
    df = df[df["failure_reason"].isna()].copy()

    # Build ML label
    df["label"] = df["data_source"].map({
        "openzeppelin": 0,
        "production_safe": 0,
        "smartbugs_curated": 1,
        "production_vulnerable": 1,
        "trail_of_bits": 1,
    })

    df = df[~df["label"].isna()].copy()
    df["label"] = df["label"].astype(int)

    # Optional: drop very DB-specific columns
    drop_cols = [
        "id",
        "created_at",
        "updated_at",
        "failure_reason",
        "error_message",
        "source_code",
    ]
    df = df[[c for c in df.columns if c not in drop_cols]]

    ts = datetime.now().strftime("%Y%m%d")
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"training_with_semantic_{ts}.csv"
    df.to_csv(out_path, index=False)

    print(f"Saved ML dataset: {out_path}")
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print("Label distribution:")
    print(df["label"].value_counts())

if __name__ == "__main__":
    main()
