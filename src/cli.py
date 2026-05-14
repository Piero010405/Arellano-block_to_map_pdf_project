from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from src.core.settings import get_available_countries, load_settings
from src.pipelines.run_pipeline import run_country_pipeline
from src.pipelines.validate_pipeline import validate_country

app = typer.Typer(help="Generador de PDFs por BLOCKID usando KML local y Geoapify.")
console = Console()


def _countries(country: str) -> list[str]:
    available = get_available_countries()
    if country == "all":
        return available
    if country not in available:
        raise typer.BadParameter(f"Invalid country '{country}'. Available: {available + ['all']}")
    return [country]


@app.command()
def validate(
    country: str = typer.Option("peru", help="País: peru, bolivia, paraguay o all."),
):
    """Valida Excel y KMLs disponibles."""
    results = []
    for c in _countries(country):
        settings = load_settings(c, profile="prod")
        results.append(validate_country(settings))
    console.print(results)


@app.command()
def preview(
    country: str = typer.Option("peru", help="País: peru, bolivia o paraguay."),
    sample_size: int = typer.Option(10, help="Cantidad de bloques de prueba."),
    force: bool = typer.Option(True, help="Regenerar aunque existan salidas preview."),
):
    """Genera prueba visual sin caché en carpeta preview."""
    if country == "all":
        raise typer.BadParameter("Preview debe ejecutarse por país para controlar requests.")
    settings = load_settings(country, profile="test")
    run_country_pipeline(
        settings,
        command_name="preview",
        preview=True,
        sample_size=sample_size,
        force=force,
    )


@app.command()
def debug(
    country: str = typer.Option("peru", help="País: peru, bolivia o paraguay."),
    sample_size: int = typer.Option(3, help="Cantidad de mapas mock."),
):
    """Genera mapas falsos para probar PDF sin consumir Geoapify."""
    settings = load_settings(country, profile="debug")
    run_country_pipeline(
        settings,
        command_name="debug",
        preview=True,
        sample_size=sample_size,
        force=True,
    )


@app.command("run")
def run_command(
    country: str = typer.Option("peru", help="País: peru, bolivia, paraguay o all."),
    offset: Optional[int] = typer.Option(None, help="Posición inicial. Ej: 0 o 2000."),
    limit: Optional[int] = typer.Option(None, help="Cantidad máxima a ejecutar."),
    only_missing: bool = typer.Option(False, help="Ejecutar solo faltantes en cache/output."),
    block_ids_file: Optional[str] = typer.Option(None, help="Archivo txt con BLOCKID a ejecutar."),
    force: bool = typer.Option(False, help="Ignorar caché y regenerar."),
):
    """Ejecuta producción con caché."""
    summaries = []
    for c in _countries(country):
        settings = load_settings(c, profile="prod")
        summaries.append(
            run_country_pipeline(
                settings,
                command_name="run",
                preview=False,
                sample_size=None,
                offset=offset,
                limit=limit,
                only_missing=only_missing,
                block_ids_file=block_ids_file,
                force=force,
            )
        )
    console.print(summaries)


@app.command("run-sample")
def run_sample(
    country: str = typer.Option("peru", help="País: peru, bolivia o paraguay."),
    sample_size: int = typer.Option(10, help="Cantidad de bloques a ejecutar en output con caché."),
):
    """Ejecuta una muestra pero guardando en output y usando caché."""
    settings = load_settings(country, profile="prod")
    run_country_pipeline(
        settings,
        command_name="run_sample",
        preview=False,
        sample_size=sample_size,
    )
