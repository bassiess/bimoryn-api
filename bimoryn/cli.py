"""BIMoryn CLI — bimoryn validate <model.ifc>

Usage:
    bimoryn validate model.ifc
    bimoryn validate model.ifc --output report.json --format json
    bimoryn validate model.ifc --output issues.bcfzip --format bcf
    bimoryn validate model.ifc --min-severity warning --disable GE-003,PM-006
    bimoryn rules list
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from bimoryn.engine import Engine, EngineConfig
from bimoryn.models import Severity
from bimoryn.rules import REGISTRY

app = typer.Typer(
    name="bimoryn",
    help="BIMoryn — rule-based BIM validation engine",
    add_completion=False,
)
rules_app = typer.Typer(help="Manage validation rules")
app.add_typer(rules_app, name="rules")

console = Console()
err_console = Console(stderr=True, style="red")

_SEVERITY_COLOURS = {
    "error":   "[bold red]",
    "warning": "[yellow]",
    "info":    "[dim]",
}


@app.command()
def validate(
    model: Annotated[Path, typer.Argument(help="Path to IFC file")],
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output file path")] = None,
    fmt: Annotated[str, typer.Option("--format", "-f", help="Output format: json | bcf")] = "json",
    min_severity: Annotated[str, typer.Option("--min-severity", "-s", help="Minimum severity: info | warning | error")] = "info",
    disable: Annotated[Optional[str], typer.Option("--disable", "-d", help="Comma-separated rule IDs to skip")] = None,
    enable: Annotated[Optional[str], typer.Option("--enable", "-e", help="Only run these rule IDs (comma-separated)")] = None,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Suppress issue table, print summary only")] = False,
) -> None:
    """Validate an IFC model against the BIMoryn rule library."""

    if not model.exists():
        err_console.print(f"File not found: {model}")
        raise typer.Exit(1)

    # --- Build engine config ---
    try:
        sev = Severity(min_severity.lower())
    except ValueError:
        err_console.print(f"Invalid severity '{min_severity}'. Use: info | warning | error")
        raise typer.Exit(1)

    disabled_rules = [r.strip() for r in disable.split(",")] if disable else []
    enabled_rules  = [r.strip() for r in enable.split(",")]  if enable  else None

    cfg = EngineConfig(
        enabled_rules  = enabled_rules,
        disabled_rules = disabled_rules,
        min_severity   = sev,
    )

    # --- Run ---
    with console.status(f"[bold green]Validating {model.name}…"):
        result = Engine(cfg).run(model)

    # --- Print summary ---
    s = result.summary
    console.print()
    console.print(f"[bold]Model:[/bold]  {result.project_name or model.name}")
    console.print(f"[bold]Schema:[/bold] {result.schema}")
    console.print(f"[bold]Elements:[/bold] {s.total_elements:,}  |  [bold]Rules run:[/bold] {s.rules_run}  |  [bold]Time:[/bold] {s.duration_ms:.0f}ms")
    console.print()
    console.print(
        f"Issues: [bold red]{s.errors} errors[/bold red]  "
        f"[yellow]{s.warnings} warnings[/yellow]  "
        f"[dim]{s.infos} info[/dim]  "
        f"([bold]{s.total_issues} total[/bold])"
    )

    # --- Print issue table ---
    if not quiet and result.issues:
        console.print()
        table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
        table.add_column("SEV",      style="", width=8)
        table.add_column("RULE",     style="", width=8)
        table.add_column("CATEGORY", style="dim", width=12)
        table.add_column("ELEMENT",  style="", width=30)
        table.add_column("MESSAGE",  style="")

        for issue in result.issues:
            sev_str = issue.severity.value.upper()
            colour = _SEVERITY_COLOURS.get(issue.severity.value, "")
            elem_str = f"{issue.element_type or ''}  {issue.element_name or ''}"[:30]
            table.add_row(
                f"{colour}{sev_str}",
                issue.rule_id,
                issue.category.value,
                elem_str.strip(),
                issue.message[:80],
            )

        console.print(table)

    # --- Write output ---
    if output:
        _write_output(result, output, fmt)
        console.print(f"\n[green]Output written:[/green] {output}")

    # Exit with non-zero if errors found (useful for CI pipelines)
    if s.errors > 0:
        raise typer.Exit(2)


@rules_app.command("list")
def rules_list(
    category: Annotated[Optional[str], typer.Option("--category", "-c")] = None,
) -> None:
    """List all registered validation rules."""
    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("ID",       width=10)
    table.add_column("CATEGORY", width=14)
    table.add_column("SEVERITY", width=10)
    table.add_column("NAME")

    for rule_cls in sorted(REGISTRY.all_rules(), key=lambda r: r.id):
        if category and rule_cls.category.value != category.lower():
            continue
        table.add_row(
            rule_cls.id,
            rule_cls.category.value,
            rule_cls.severity.value,
            rule_cls.name,
        )

    console.print(table)
    console.print(f"\n[dim]{len(REGISTRY)} rules registered[/dim]")


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _write_output(result, output: Path, fmt: str) -> None:
    fmt = fmt.lower()
    if fmt == "json":
        from bimoryn.output.json_report import write_json
        write_json(result, output)
    elif fmt in ("bcf", "bcfzip"):
        from bimoryn.output.bcf import write_bcf
        write_bcf(result, output)
    else:
        err_console.print(f"Unknown format '{fmt}'. Use: json | bcf")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
