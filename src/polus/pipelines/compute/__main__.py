"""Command line Interface to submit pipelines to compute."""

import logging
import os
from pathlib import Path
from typing import Annotated

import typer
from dotenv import find_dotenv
from dotenv import load_dotenv
from .compute import submit_pipeline
from ..utils import make_logger

load_dotenv(find_dotenv())
logger = make_logger(__file__)
app = typer.Typer(help="Compute Client.")


@app.command()
def main(compute_pipeline_file: Annotated[Path, typer.Argument()]) -> None:
    """Command line Interface to submit pipelines to compute."""
    submit_pipeline(compute_pipeline_file)


if __name__ == "__main__":
    app()
