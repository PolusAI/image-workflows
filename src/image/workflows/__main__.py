"""CWL Workflow."""
import logging
import typer
from pathlib import Path
from typing import Optional
from image.workflows.utils import LoadYaml
from image.workflows.cwl_analysis import CWLAnalysisWorkflow
from image.workflows.cwl_nuclear_segmentation import CWLSegmentationWorkflow
from image.workflows.cwl_visualization import CWLVisualizationWorkflow




app = typer.Typer()

# Initialize the logger
logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger("WIC Python API")
logger.setLevel(logging.INFO)


# Mapping of workflow names to their corresponding classes
WORKFLOW_CLASSES = {
    "analysis": CWLAnalysisWorkflow,
    "segmentation": CWLSegmentationWorkflow,
    "visualization": CWLVisualizationWorkflow
}


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
    ),
    out_dir: Optional[Path] = typer.Option(
        None,
        "--outDir",
        "-o",
        help="Name of cwl workflow"
    )
) -> None:

    """
    Execute the specified CWL Workflow.

    Attributes:
        name (str): The name of the imaging dataset.
        workflow (str): The name of the CWL workflow to execute.
        out_dir (Path): The output directory for workflow results.
    """

    logger.info(f"name = {name}")
    logger.info(f"workflow = {workflow}")
    logger.info(f"outDir = {out_dir}")

    config_path = Path.cwd().joinpath(f"configuration/{workflow}/{name}.yml")
    work_dir = Path.cwd()
 
    try:
        # Load the YAML configuration
        model = LoadYaml(workflow=workflow, config_path=config_path)
        params = model.parse_yaml()

        # Set output directory
        out_dir = out_dir or Path.cwd()
        params["out_dir"] = out_dir
        params["work_dir"] = work_dir

        # Get the workflow class
        workflow_class = WORKFLOW_CLASSES.get(workflow)
        if not workflow_class:
            logger.error(f"Workflow '{workflow}' is not recognized. Available workflows: {list(WORKFLOW_CLASSES.keys())}")
            raise ValueError(f"Unknown workflow: {workflow}")

        logger.info(f"Executing {workflow} workflow.")
        # Initialize and execute the workflow class
        workflow_instance = workflow_class(**params)
        workflow_instance.workflow()

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
    except Exception as e:
        logger.error(f"An error occurred while executing the workflow: {e}")
        raise

    # model = LoadYaml(workflow=workflow, config_path=config_path)
    # params = model.parse_yaml()

    # out_dir = out_dir or Path.cwd()

    # params["out_dir"] = out_dir
    # params["work_dir"] = work_dir

    # # Validate workflow and execute corresponding class
    # workflow_class = WORKFLOW_CLASSES.get(workflow)
    # print(workflow_class)
    # if workflow_class:
    #     logger.info(f"Executing {workflow} workflow.")
    #     model = workflow_class(**params)
    #     model.workflow()
    # else:
    #     logger.error(f"Invalid workflow: {workflow}. Available options: {', '.join(WORKFLOW_CLASSES.keys())}")
    #     raise ValueError(f"Workflow '{workflow}' is not recognized.")

    # logger.info(f"Completed {workflow} workflow execution!")



if __name__ == "__main__":
    app()