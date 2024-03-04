"""CWL Workflow."""
import logging
import typer
from utils import FEAT_JSON_FILENAME
from utils import LoadData
from cwl_features_extraction import CWLFeatureWorkflow


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

    
    if workflow == "feature":
        model = LoadData(path=FEAT_JSON_FILENAME, name= name)
        params = model.parse_json()
        logger.info(f"Executing {workflow}!!!")
        model = CWLFeatureWorkflow(**params)
        model.workflow()

    logger.info("Completed CWL workflow!!!")


if __name__ == "__main__":
    app()