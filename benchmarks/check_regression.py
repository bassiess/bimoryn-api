"""Regression check for BIMoryn benchmark results.

Compares a new benchmark run against a baseline and fails with exit code 1
if any size's avg_ms has degraded by more than --threshold percent.

Usage::

    python benchmarks/check_regression.py \\
        --baseline benchmarks/results/baseline.json \\
        --current  benchmarks/results/latest.json \\
        --threshold 20
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="BIMoryn benchmark regression checker")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument(
        "--threshold", type=float, default=20.0,
        help="Max allowed percent degradation (default: 20)"
    )
    args = parser.parse_args()

    baseline = json.loads(args.baseline.read_text())
    current  = json.loads(args.current.read_text())

    failures: list[str] = []

    for size, cur_data in current["sizes"].items():
        base_data = baseline.get("sizes", {}).get(size)
        if base_data is None:
            print(f"[skip] {size}: no baseline entry, skipping")
            continue

        base_ms = base_data["e2e"]["avg_ms"]
        cur_ms  = cur_data["e2e"]["avg_ms"]

        if base_ms <= 0:
            print(f"[skip] {size}: baseline avg_ms is 0, skipping")
            continue

        pct_change = ((cur_ms - base_ms) / base_ms) * 100

        status = "OK"
        if pct_change > args.threshold:
            status = "FAIL"
            failures.append(
                f"{size}: {cur_ms:.1f} ms vs baseline {base_ms:.1f} ms "
                f"(+{pct_change:.1f}% > {args.threshold:.0f}% threshold)"
            )

        print(
            f"[{status}] {size}: {base_ms:.1f} ms → {cur_ms:.1f} ms "
            f"({pct_change:+.1f}%)"
        )

    if failures:
        print("\nRegression failures:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\nAll sizes within regression threshold.")


if __name__ == "__main__":
    main()
