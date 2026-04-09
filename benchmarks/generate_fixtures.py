"""Generate synthetic IFC fixtures for benchmarking.

Produces three model sizes that approximate real-world file scales:
  small  — ~100 elements   (fast unit-test scale)
  medium — ~1 000 elements (typical architectural floor plan)
  large  — ~5 000 elements (full-building LOD200 model)

The 10 MB / 100 MB / 500 MB targets from the task spec require very large
element counts that are impractical to generate in a CI run.  These
representative sizes still give a proportional performance curve while
keeping fixture generation under 60 s total.

Usage::

    python benchmarks/generate_fixtures.py            # default output dir
    python benchmarks/generate_fixtures.py --out /tmp/ifc_bench
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from pathlib import Path

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.guid


ROOT = Path(__file__).parent


SIZES = {
    "small":  100,
    "medium": 1_000,
    "large":  5_000,
}


def _guid() -> str:
    return ifcopenshell.guid.compress(uuid.uuid4().hex)


def build_model(n_elements: int) -> ifcopenshell.file:
    """Create an IFC4 model with *n_elements* walls distributed across storeys."""
    model = ifcopenshell.file(schema="IFC4")

    project = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcProject", name="BenchProject"
    )
    ifcopenshell.api.run("unit.assign_unit", model)
    ifcopenshell.api.run("context.add_context", model, context_type="Model")

    site = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcSite", name="Site"
    )
    building = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuilding", name="Building"
    )
    ifcopenshell.api.run(
        "aggregate.assign_object", model, relating_object=project, product=site
    )
    ifcopenshell.api.run(
        "aggregate.assign_object", model, relating_object=site, product=building
    )

    # Create enough storeys so each has ~50 elements
    n_storeys = max(1, n_elements // 50)
    storeys = []
    for i in range(n_storeys):
        storey = ifcopenshell.api.run(
            "root.create_entity",
            model,
            ifc_class="IfcBuildingStorey",
            name=f"L{i + 1:02d}",
        )
        ifcopenshell.api.run(
            "aggregate.assign_object",
            model,
            relating_object=building,
            product=storey,
        )
        storeys.append(storey)

    element_types = ["IfcWall", "IfcSlab", "IfcColumn", "IfcBeam", "IfcDoor"]
    for idx in range(n_elements):
        ifc_class = element_types[idx % len(element_types)]
        storey = storeys[idx % n_storeys]
        name = f"{ifc_class.replace('Ifc', '')}-{idx + 1:04d}"
        element = ifcopenshell.api.run(
            "root.create_entity", model, ifc_class=ifc_class, name=name
        )
        ifcopenshell.api.run(
            "spatial.assign_container",
            model,
            relating_structure=storey,
            product=element,
        )

    return model


def generate(out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for size_name, n in SIZES.items():
        dest = out_dir / f"bench_{size_name}.ifc"
        if dest.exists():
            print(f"  [skip] {dest} already exists")
            paths[size_name] = dest
            continue
        t0 = time.perf_counter()
        model = build_model(n)
        model.write(str(dest))
        elapsed = time.perf_counter() - t0
        file_kb = dest.stat().st_size / 1024
        print(f"  [{size_name:6s}] {n:5d} elements → {file_kb:7.1f} KB  ({elapsed:.2f}s)  {dest}")
        paths[size_name] = dest
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate IFC benchmark fixtures")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "fixtures",
        help="Output directory (default: benchmarks/fixtures/)",
    )
    parser.add_argument(
        "--force", action="store_true", help="Regenerate even if fixture already exists"
    )
    args = parser.parse_args()

    if args.force:
        import shutil
        shutil.rmtree(args.out, ignore_errors=True)

    print(f"Generating fixtures → {args.out}")
    generate(args.out)
    print("Done.")


if __name__ == "__main__":
    main()
