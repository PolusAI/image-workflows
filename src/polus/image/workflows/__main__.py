"""CWL Workflow."""
import logging
import typer
from pathlib import Path
from polus.image.workflows.utils import LoadYaml
from workflows.cwl_analysis import CWLAnalysisWorkflow
from workflows.cwl_nuclear_segmentation import CWLSegmentationWorkflow
from pathlib import Path


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

    config_path = Path(__file__).parent.parent.parent.parent.parent.joinpath(f"configuration/{workflow}/{name}.yml")
    print(config_path)


    model = LoadYaml(workflow=workflow, config_path=config_path)
    params = model.parse_yaml()

    if workflow == "analysis":
        logger.info(f"Executing {workflow}!!!")
        model = CWLAnalysisWorkflow(**params)
        model.workflow()

    if workflow == "segmentation":
        logger.info(f"Executing {workflow}!!!")
        model = CWLSegmentationWorkflow(**params)
        model.workflow()


    logger.info("Completed CWL workflow!!!")


if __name__ == "__main__":
    app()