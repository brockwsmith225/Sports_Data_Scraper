import datetime
import typer

app = typer.Typer()

@app.command()
def fetch(year: int = None):
    if not year:
        year = datetime.date.today().year

if __name__ == "__main__":
    app()