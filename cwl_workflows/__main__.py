"""CWL Workflow."""
import logging
import typer
from utils import SEG_JSON_FILENAME
from utils import get_params
from cwl_nuclear_segmentation import CWLSegmentationWorkflow


app = typer.Typer()

# Initialize the logger
logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger("WIC Python API")
logger.setLevel(logging.INFO)


@app.command()
def main(
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="Name of imaging dataset of Broad Bioimage Benchmark Collection (https://bbbc.broadinstitute.org/image_sets)"
    ),
    workflow: str = typer.Option(
        ...,
        "--workflow",
        "-w",
        help="Name of cwl workflow"
    )
) -> None:

    """Execute CWL Workflow."""

    logger.info(f"name = {name}")
    logger.info(f"workflow = {workflow}")

    if workflow == "segmentation":
         params = get_params(SEG_JSON_FILENAME, name)
         logger.info(f"Executing {workflow}!!!")
         model = CWLSegmentationWorkflow(**params)
         model.workflow()

    logger.info("Completed CWL workflow!!!")


if __name__ == "__main__":
    app()