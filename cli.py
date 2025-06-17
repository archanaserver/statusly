import typer
import os
import json
import requests
from typing import Optional, List
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    typer.echo("OPENAI_API_KEY is not set. Please set it in your .env file.")
    raise typer.Exit()
client = OpenAI(api_key=api_key)

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
    typer.echo(f"Log updated for {log_date}")

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
        typer.echo(f"No log found for {log_date}")
        return

    typer.echo(f"\nLog for {log_date}:\n")
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

def fetch_github_activity(start_date: str, end_date: str):
    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("GITHUB_USERNAME")
    headers = {"Authorization": f"token {token}"}
    doing = []
    done = []

    # Pull Requests Opened
    pr_url = f"https://api.github.com/search/issues?q=author:{username}+type:pr+created:{start_date}..{end_date}"
    pr_response = requests.get(pr_url, headers=headers).json()
    for item in pr_response.get("items", []):
        title = item["title"]
        url = item["html_url"]
        doing.append(f"Opened PR: [{title}]({url})")

    # Pull Requests Reviewed
    review_url = f"https://api.github.com/search/issues?q=commenter:{username}+type:pr+updated:{start_date}..{end_date}"
    review_response = requests.get(review_url, headers=headers).json()
    for item in review_response.get("items", []):
        title = item["title"]
        url = item["html_url"]
        done.append(f"Reviewed PR: [{title}]({url})")

    return {"doing": doing, "done": done}

@app.command()
def ai_summary(
    start_date: str = typer.Option(..., help="Start date in YYYY-MM-DD"),
    end_date: str = typer.Option(..., help="End date in YYYY-MM-DD")
):
    """Use AI to summarize your work logs between two dates."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        typer.echo("Invalid date format. Use YYYY-MM-DD.")
        raise typer.Exit()

    if end < start:
        typer.echo("End date cannot be before start date.")
        raise typer.Exit()

    combined_logs = {"doing": set(), "done": set(), "blocker": set()}
    current = start
    while current <= end:
        log_data = load_log(str(current))
        for key in combined_logs:
            combined_logs[key].update(log_data.get(key, []))
        current += timedelta(days=1)

    # Fetch GitHub activity and merge with logs
    github_logs = fetch_github_activity(start_date, end_date)
    combined_logs["doing"].update(github_logs["doing"])
    combined_logs["done"].update(github_logs["done"])

    if not any(combined_logs.values()):
        typer.echo("No logs found in the given date range.")
        raise typer.Exit()

    summary_text = ""
    for section in ["doing", "done", "blocker"]:
        if combined_logs[section]:
            summary_text += f"{section.upper()}:\n"
            for item in sorted(combined_logs[section]):
                summary_text += f"• {item}\n"
            summary_text += "\n"

    typer.echo("Sending logs to OpenAI for summarization...\n")

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes developer logs into bullet points grouped by section. Group semantically similar tasks into one bullet point. Use markdown with sections for DOING, DONE, and BLOCKER. Do not include MISC"},
                {"role": "user", "content": f"Summarize the following developer logs into three sections: ##doing, ##done, ##blocker. Keep it concise and in bullet points. Ignore MISC: {summary_text}"}
            ]
        )
        summary = response.choices[0].message.content
        today_str = str(date.today())
        typer.echo(f"Status {today_str}:\n")
        typer.echo(summary)

    except Exception as e:
        typer.echo(f"Failed to call OpenAI: {e}")

if __name__ == "__main__":
    app()
