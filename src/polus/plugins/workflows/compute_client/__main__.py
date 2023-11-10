from pathlib import Path
import logging
import os
from dotenv import load_dotenv
import typer
from typing_extensions import Annotated
from polus.plugins.workflows.compute_client import submit_workflow

load_dotenv(override=True)

logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
POLUS_LOG = getattr(logging, os.environ.get("POLUS_LOG", "INFO"))
logger = logging.getLogger("polus.plugins.workflows.compute_client")
logger.setLevel(POLUS_LOG)

app = typer.Typer(help="Compute Client.")

@app.command()
def main(compute_workflow_file: Annotated[Path, typer.Argument()]):

    compute_workflow_file = compute_workflow_file.resolve()

    if not compute_workflow_file.exists():
        raise FileExistsError("no cwl workflow file has been provided."
                                +f"{compute_workflow_file} not found.")
    
    # TODO do we have a pydantic model to validate against?
    if not (compute_workflow_file.is_file() and compute_workflow_file.suffix == ".json"):
        raise Exception(f"{compute_workflow_file} is not a valid workflow file.")
    
    submit_workflow(compute_workflow_file)


if __name__ == "__main__":
    app()