import typer
from typing import Optional, List
from datetime import date
import json
import os

app = typer.Typer()
log_app = typer.Typer()
app.add_typer(log_app, name="log")

# Log storage directory
DATA_DIR = os.path.expanduser("~/.statusly/logs")
os.makedirs(DATA_DIR, exist_ok=True)

def get_log_file_path(log_date: str):
    return os.path.join(DATA_DIR, f"{log_date}.json")

def load_log(log_date: str):
    path = get_log_file_path(log_date)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        return {"doing": [], "done": [], "blocker": [], "misc": []}

def save_log(log_date: str, data: dict):
    path = get_log_file_path(log_date)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

@log_app.command()
def add(
    doing: Optional[List[str]] = typer.Option(None, "--doing", help="Things you are currently working on"),
    done: Optional[List[str]] = typer.Option(None, "--done", help="Tasks you've completed"),
    blocker: Optional[List[str]] = typer.Option(None, "--blocker", help="Anything blocking your progress"),
    misc: Optional[List[str]] = typer.Option(None, "--misc", help="Miscellaneous activities (calls, side work, etc.)"),
    log_date: Optional[str] = typer.Option(str(date.today()), "--log-date", help="Log date (default: today)")
):
    """Add a status log entry."""
    log_data = load_log(log_date)

    if doing:
        log_data.setdefault("doing", []).extend(doing)
    if done:
        log_data.setdefault("done", []).extend(done)
    if blocker:
        log_data.setdefault("blocker", []).extend(blocker)
    if misc:
        log_data.setdefault("misc", []).extend(misc)

    save_log(log_date, log_data)
    typer.echo(f"✅ Log updated for {log_date}")

@app.command()
def show(
    log_date: Optional[str] = typer.Option(str(date.today()), "--log-date", help="Date of the log to view")
):
    """Show the logged work for a given date."""
    log_data = load_log(log_date)

    if not any([
        log_data.get("doing", []),
        log_data.get("done", []),
        log_data.get("blocker", []),
        log_data.get("misc", [])
    ]):
        typer.echo(f"📭 No log found for {log_date}")
        return

    typer.echo(f"\n📓 Log for {log_date}:\n")
    if log_data.get("doing"):
        typer.echo("DOING:")
        for item in log_data["doing"]:
            typer.echo(f"  • {item}")
    if log_data.get("done"):
        typer.echo("\nDONE:")
        for item in log_data["done"]:
            typer.echo(f"  • {item}")
    if log_data.get("blocker"):
        typer.echo("\nBLOCKER:")
        for item in log_data["blocker"]:
            typer.echo(f"  • {item}")
    if log_data.get("misc"):
        typer.echo("\nMISCELLANEOUS:")
        for item in log_data["misc"]:
            typer.echo(f"  • {item}")
    typer.echo("")

if __name__ == "__main__":
    app()
