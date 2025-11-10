"""
Progress indicators for CLI operations.

Provides progress bars, spinners, and status indicators using Rich.
"""

from contextlib import contextmanager
from typing import Optional

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.spinner import Spinner
from rich.live import Live

console = Console()


@contextmanager
def create_progress():
    """
    Create a progress bar for file/item processing.

    Usage:
        with create_progress() as progress:
            task = progress.add_task("Processing...", total=100)
            for i in range(100):
                # Do work
                progress.update(task, advance=1)
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )

    with progress:
        yield progress


@contextmanager
def create_spinner(message: str = "Working..."):
    """
    Create a spinner for quick operations.

    Usage:
        with create_spinner("Loading..."):
            # Do work
            time.sleep(2)
    """
    spinner = Spinner("dots", text=f"[bold cyan]{message}")
    with Live(spinner, console=console, transient=True):
        yield


@contextmanager
def show_status(message: str, success_message: Optional[str] = None):
    """
    Show a status message with optional success confirmation.

    Usage:
        with show_status("Creating snapshot...", "Snapshot created!"):
            # Do work
            time.sleep(2)
    """
    console.print(f"\n[bold cyan]{message}[/bold cyan]")
    try:
        yield
        if success_message:
            console.print(f"[bold green]✓[/bold green] {success_message}\n")
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed: {str(e)}\n")
        raise


class ScanProgress:
    """Progress tracker for file scanning operations."""

    def __init__(self, total_paths: int):
        self.total_paths = total_paths
        self.current = 0
        self.progress = None
        self.task_id = None

    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Scanning paths..."),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[dim]{task.fields[current_path]}"),
            TimeElapsedColumn(),
            console=console,
        )
        self.progress.__enter__()
        self.task_id = self.progress.add_task(
            "Scanning",
            total=self.total_paths,
            current_path="",
        )
        return self

    def __exit__(self, *args):
        if self.progress:
            self.progress.__exit__(*args)

    def update(self, path: str):
        """Update progress with current path."""
        if self.progress and self.task_id is not None:
            self.current += 1
            # Truncate long paths
            display_path = str(path)
            if len(display_path) > 50:
                display_path = "..." + display_path[-47:]

            self.progress.update(
                self.task_id,
                advance=1,
                current_path=display_path,
            )


class ExportProgress:
    """Progress tracker for export operations."""

    def __init__(self, total_items: int, operation: str = "Exporting"):
        self.total_items = total_items
        self.operation = operation
        self.progress = None
        self.task_id = None

    def __enter__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{self.operation}..."),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        self.progress.__enter__()
        self.task_id = self.progress.add_task(
            self.operation,
            total=self.total_items,
        )
        return self

    def __exit__(self, *args):
        if self.progress:
            self.progress.__exit__(*args)

    def update(self, advance: int = 1):
        """Update progress."""
        if self.progress and self.task_id is not None:
            self.progress.update(self.task_id, advance=advance)


def show_step_progress(steps: list[str], current_step: int):
    """
    Show progress through multi-step operations.

    Args:
        steps: List of step names
        current_step: Current step index (0-based)
    """
    step_indicators = []
    for i, step in enumerate(steps):
        if i < current_step:
            step_indicators.append(f"[green]✓[/green] {step}")
        elif i == current_step:
            step_indicators.append(f"[cyan]→[/cyan] [bold]{step}[/bold]")
        else:
            step_indicators.append(f"[dim]○ {step}[/dim]")

    console.print("\n".join(step_indicators))
