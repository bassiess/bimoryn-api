"""BIMoryn validation engine — performance benchmark harness.

Measures:
  - End-to-end wall-clock time per model size
  - Per-rule execution time
  - Peak memory (via tracemalloc)
  - Element throughput (elements/second)

Outputs:
  - Human-readable table to stdout (via rich if available, plain text fallback)
  - JSON report to benchmarks/results/latest.json
  - Optional markdown summary to benchmarks/results/latest.md

Usage::

    # From the repo root:
    python benchmarks/run_benchmarks.py

    # Skip fixture generation (use existing files in benchmarks/fixtures/):
    python benchmarks/run_benchmarks.py --no-generate

    # Save report to a specific file:
    python benchmarks/run_benchmarks.py --out benchmarks/results/2026-04-09.json

    # Run a single size:
    python benchmarks/run_benchmarks.py --sizes small
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Make sure repo root is on sys.path so `bimoryn` is importable even when
# running directly (not as an installed package).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import benchmarks.generate_fixtures as gen_fixtures  # noqa: E402
from bimoryn.engine import Engine  # noqa: E402
from bimoryn.rules import REGISTRY  # noqa: E402

BENCHMARK_DIR = Path(__file__).parent
FIXTURES_DIR  = BENCHMARK_DIR / "fixtures"
RESULTS_DIR   = BENCHMARK_DIR / "results"
BUDGET_PATH   = BENCHMARK_DIR / "budget.json"

REPEATS = 3  # average over N runs to reduce noise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_budget() -> dict[str, Any]:
    if BUDGET_PATH.exists():
        with open(BUDGET_PATH) as f:
            return json.load(f)
    return {}


def _mem_mb(peak_bytes: int) -> float:
    return round(peak_bytes / 1024 / 1024, 2)


def _throughput(n_elements: int, duration_ms: float) -> float:
    if duration_ms <= 0:
        return 0.0
    return round(n_elements / (duration_ms / 1000), 1)


# ---------------------------------------------------------------------------
# Per-rule timing
# ---------------------------------------------------------------------------

def _bench_rules(model_path: Path) -> dict[str, float]:
    """Return {rule_id: avg_ms} for each rule run in isolation."""
    import ifcopenshell

    model = ifcopenshell.open(str(model_path))
    results: dict[str, float] = {}

    for rule_cls in REGISTRY.all_rules():
        from bimoryn.models import RuleConfig
        cfg = RuleConfig()
        rule = rule_cls(config=cfg)

        times: list[float] = []
        for _ in range(REPEATS):
            t0 = time.perf_counter()
            list(rule.check(model, cfg))
            times.append((time.perf_counter() - t0) * 1000)

        results[rule_cls.id] = round(sum(times) / len(times), 2)

    return results


# ---------------------------------------------------------------------------
# End-to-end timing + memory
# ---------------------------------------------------------------------------

def _bench_e2e(model_path: Path) -> dict[str, Any]:
    """Run the full engine REPEATS times; return timing + memory stats."""
    engine = Engine()
    times_ms: list[float] = []
    peak_bytes_list: list[int] = []
    element_count = 0

    for i in range(REPEATS):
        tracemalloc.start()
        t0 = time.perf_counter()
        result = engine.run(model_path)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        times_ms.append(elapsed_ms)
        peak_bytes_list.append(peak)
        element_count = result.summary.total_elements

    avg_ms   = round(sum(times_ms) / REPEATS, 1)
    min_ms   = round(min(times_ms), 1)
    max_ms   = round(max(times_ms), 1)
    peak_mb  = _mem_mb(max(peak_bytes_list))
    tput     = _throughput(element_count, avg_ms)

    return {
        "avg_ms":        avg_ms,
        "min_ms":        min_ms,
        "max_ms":        max_ms,
        "peak_memory_mb": peak_mb,
        "elements":      element_count,
        "throughput_elem_per_s": tput,
        "issues_found":  result.summary.total_issues,
        "rules_run":     result.summary.rules_run,
    }


# ---------------------------------------------------------------------------
# Budget check
# ---------------------------------------------------------------------------

def _check_budget(size: str, e2e: dict[str, Any], budget: dict) -> list[str]:
    violations: list[str] = []
    b = budget.get(size, {})
    if "max_duration_ms" in b and e2e["avg_ms"] > b["max_duration_ms"]:
        violations.append(
            f"duration {e2e['avg_ms']} ms > budget {b['max_duration_ms']} ms"
        )
    if "max_memory_mb" in b and e2e["peak_memory_mb"] > b["max_memory_mb"]:
        violations.append(
            f"memory {e2e['peak_memory_mb']} MB > budget {b['max_memory_mb']} MB"
        )
    return violations


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def _render_table(report: dict[str, Any]) -> None:
    try:
        from rich.console import Console  # noqa: F401
        from rich.table import Table  # noqa: F401
        _render_rich(report)
    except ImportError:
        _render_plain(report)


def _render_rich(report: dict[str, Any]) -> None:
    from rich import box
    from rich.console import Console
    from rich.table import Table

    console = Console()
    console.print(f"\n[bold]BIMoryn Benchmark Report[/bold]  {report['generated_at']}\n")

    # E2E table
    t = Table(title="End-to-end performance", box=box.SIMPLE_HEAD)
    t.add_column("Size",    style="cyan")
    t.add_column("Elements", justify="right")
    t.add_column("Avg ms",   justify="right")
    t.add_column("Min ms",   justify="right")
    t.add_column("Max ms",   justify="right")
    t.add_column("Peak MB",  justify="right")
    t.add_column("Elem/s",   justify="right")
    t.add_column("Issues",   justify="right")
    t.add_column("Budget",   justify="left")

    for size, data in report["sizes"].items():
        e2e = data["e2e"]
        violations = data.get("budget_violations", [])
        budget_str = "[red]FAIL[/red]" if violations else "[green]OK[/green]"
        t.add_row(
            size,
            str(e2e["elements"]),
            str(e2e["avg_ms"]),
            str(e2e["min_ms"]),
            str(e2e["max_ms"]),
            str(e2e["peak_memory_mb"]),
            str(e2e["throughput_elem_per_s"]),
            str(e2e["issues_found"]),
            budget_str,
        )
    console.print(t)

    # Slowest rules table (top 10)
    all_rules: dict[str, list[float]] = {}
    for data in report["sizes"].values():
        for rule_id, ms in data["rules"].items():
            all_rules.setdefault(rule_id, []).append(ms)

    avg_rule = {r: sum(v) / len(v) for r, v in all_rules.items()}
    top10 = sorted(avg_rule.items(), key=lambda x: -x[1])[:10]

    rt = Table(title="Slowest rules (avg across sizes)", box=box.SIMPLE_HEAD)
    rt.add_column("Rule ID", style="cyan")
    rt.add_column("Avg ms", justify="right")
    for rule_id, ms in top10:
        rt.add_row(rule_id, f"{ms:.2f}")
    console.print(rt)


def _render_plain(report: dict[str, Any]) -> None:
    print(f"\nBIMoryn Benchmark Report  {report['generated_at']}")
    print("=" * 70)
    print(f"{'Size':<8} {'Elem':>6} {'Avg ms':>8} {'Min ms':>8} {'Max ms':>8} {'MB':>6} {'Elem/s':>8} {'Budget'}")
    print("-" * 70)
    for size, data in report["sizes"].items():
        e = data["e2e"]
        v = data.get("budget_violations", [])
        status = "FAIL" if v else "OK"
        print(
            f"{size:<8} {e['elements']:>6} {e['avg_ms']:>8} {e['min_ms']:>8} "
            f"{e['max_ms']:>8} {e['peak_memory_mb']:>6} {e['throughput_elem_per_s']:>8} {status}"
        )
    print()


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# BIMoryn — Performance Benchmark Report",
        "",
        f"Generated: {report['generated_at']}  |  Engine version: {report['engine_version']}",
        "",
        "## End-to-end Results",
        "",
        "| Size | Elements | Avg ms | Min ms | Max ms | Peak MB | Elem/s | Issues | Budget |",
        "|------|----------|--------|--------|--------|---------|--------|--------|--------|",
    ]
    for size, data in report["sizes"].items():
        e = data["e2e"]
        v = data.get("budget_violations", [])
        status = "❌ FAIL" if v else "✅ OK"
        lines.append(
            f"| {size} | {e['elements']} | {e['avg_ms']} | {e['min_ms']} | {e['max_ms']} "
            f"| {e['peak_memory_mb']} | {e['throughput_elem_per_s']} | {e['issues_found']} | {status} |"
        )

    lines += [
        "",
        "## Slowest Rules (avg across sizes)",
        "",
        "| Rule ID | Avg ms |",
        "|---------|--------|",
    ]
    all_rules: dict[str, list[float]] = {}
    for data in report["sizes"].values():
        for rule_id, ms in data["rules"].items():
            all_rules.setdefault(rule_id, []).append(ms)
    top10 = sorted(
        {r: sum(v) / len(v) for r, v in all_rules.items()}.items(),
        key=lambda x: -x[1],
    )[:10]
    for rule_id, ms in top10:
        lines.append(f"| {rule_id} | {ms:.2f} |")

    if any(data.get("budget_violations") for data in report["sizes"].values()):
        lines += ["", "## Budget Violations", ""]
        for size, data in report["sizes"].items():
            for v in data.get("budget_violations", []):
                lines.append(f"- **{size}**: {v}")

    lines += [
        "",
        "## Performance Budget",
        "",
        "| Size | Max ms | Max MB |",
        "|------|--------|--------|",
    ]
    for size, b in report.get("budget", {}).items():
        lines.append(f"| {size} | {b.get('max_duration_ms', '—')} | {b.get('max_memory_mb', '—')} |")

    lines += [
        "",
        "---",
        "_Note: Comparison against Solibri / BIMcollab ZOOM requires manual runs._",
        "_Add timed results here once pilot data is available._",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown report → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="BIMoryn benchmark harness")
    parser.add_argument(
        "--no-generate", action="store_true",
        help="Skip fixture generation (use existing files)"
    )
    parser.add_argument(
        "--sizes", nargs="+",
        choices=list(gen_fixtures.SIZES.keys()),
        default=list(gen_fixtures.SIZES.keys()),
        help="Which sizes to benchmark"
    )
    parser.add_argument(
        "--out", type=Path,
        default=RESULTS_DIR / "latest.json",
        help="JSON output path"
    )
    parser.add_argument(
        "--repeats", type=int, default=REPEATS,
        help=f"Number of repetitions per size (default: {REPEATS})"
    )
    args = parser.parse_args()

    global REPEATS
    REPEATS = args.repeats

    # Step 1: generate fixtures
    if not args.no_generate:
        print("Generating fixtures...")
        gen_fixtures.generate(FIXTURES_DIR)

    budget = _load_budget()

    report: dict[str, Any] = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "engine_version": "0.1.0",
        "python_version": sys.version.split()[0],
        "repeats":        REPEATS,
        "budget":         budget,
        "sizes":          {},
    }

    for size in args.sizes:
        fixture = FIXTURES_DIR / f"bench_{size}.ifc"
        if not fixture.exists():
            print(f"[skip] {fixture} not found — run without --no-generate")
            continue

        print(f"\nBenchmarking [{size}]  {fixture} ...")
        print(f"  Per-rule timing ({REPEATS} runs each)...")
        rule_times = _bench_rules(fixture)

        print(f"  End-to-end ({REPEATS} runs)...")
        e2e = _bench_e2e(fixture)

        violations = _check_budget(size, e2e, budget)
        if violations:
            print(f"  [BUDGET FAIL] {violations}")

        report["sizes"][size] = {
            "fixture":           str(fixture),
            "e2e":               e2e,
            "rules":             rule_times,
            "budget_violations": violations,
        }

    # Save JSON
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nJSON report → {args.out}")

    # Save markdown alongside JSON
    md_path = args.out.with_suffix(".md")
    _write_markdown(report, md_path)

    # Print table
    _render_table(report)

    # Exit 1 if any budget violation
    violations_total = sum(
        len(d.get("budget_violations", [])) for d in report["sizes"].values()
    )
    if violations_total:
        sys.exit(1)


if __name__ == "__main__":
    main()
