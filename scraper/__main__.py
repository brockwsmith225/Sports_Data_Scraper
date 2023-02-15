import typer

from scraper import cbb

app = typer.Typer()

app.add_typer(cbb.app, name="cbb")

app()