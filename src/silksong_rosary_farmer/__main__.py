#!/usr/bin/env python3

from datetime import timedelta

import typer
from rich import print

from silksong_rosary_farmer.farm import farm
from silksong_rosary_farmer.monitor import list_monitors

# Create a Typer app
app = typer.Typer(
    help="Silksong Rosary Farmer - Automates farming rosaries in Hollow Knight."
)


@app.command()
def main(
    list_monitors_flag: bool = typer.Option(
        False, "--list-monitors", help="List available monitors and exit"
    ),
    monitor: str = typer.Option(
        "0",
        "--monitor",
        help="Monitor to use (index number or name like 'left', 'right', 'center')",
    ),
    max_time_in_minutes: int = typer.Option(
        999_999_999,
        "--max-time-in-minutes",
        help="Maximum time to run the farmer (in minutes)",
    ),
) -> None:
    """Silksong Rosary Farmer - Automates farming rosaries in Hollow Knight."""

    # Handle --list-monitors flag
    if list_monitors_flag:
        monitors = list_monitors()
        if not monitors:
            print("[red]No monitors detected![/red]")
            raise typer.Exit(1)

        print("[bold cyan]\nAvailable monitors:[/bold cyan]")
        for label, index in monitors:
            print(f"  {label:>10} -> index {index}")
        return

    # Parse monitor option (can be int index or string label)
    monitors = list_monitors()
    monitor_index = None

    # Try to parse as integer first
    try:
        monitor_index = int(monitor)
    except ValueError:
        # It's a string label like "left", "right", etc.
        monitor_label = monitor.lower()
        for label, index in monitors:
            if label == monitor_label:
                monitor_index = index
                break

        if monitor_index is None:
            print(f"[red]Error: Monitor '{monitor}' not found![/red]")
            print("[yellow]Available monitors:[/yellow]")
            for label, index in monitors:
                print(f"  {label:>10} -> index {index}")
            raise typer.Exit(1)  # noqa: B904

    # Validate monitor index
    if monitor_index < 0 or monitor_index >= len(monitors):
        print(f"[red]Error: Monitor index {monitor_index} is out of range![/red]")
        print(f"[yellow]Valid indices: 0 to {len(monitors) - 1}[/yellow]")
        raise typer.Exit(1)

    # Convert max_time_in_minutes to timedelta
    max_time = timedelta(minutes=max_time_in_minutes)

    # Display starting info
    monitor_label = next(
        (label for label, idx in monitors if idx == monitor_index),
        f"index-{monitor_index}",
    )
    print(
        f"[green]Starting farmer on monitor:[/green] [bold]{monitor_label}[/bold] "
        f"(index {monitor_index})"
    )
    print(f"[green]Max time:[/green] [bold]{max_time_in_minutes}[/bold] minutes")

    # Start farming
    farm(monitor_index, max_time=max_time, enable_esc_exit=True)


if __name__ == "__main__":
    try:
        app()
    except (typer.Exit, SystemExit) as e:
        if hasattr(e, "exit_code"):
            exit(e.exit_code)
        elif isinstance(e, SystemExit):
            exit(e.code if e.code is not None else 0)
        exit(0)
