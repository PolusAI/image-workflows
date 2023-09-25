
import polus.plugins as pp
from wic.api import Step, Workflow

import logging
from pathlib import Path
import os
from enum import Enum
import utils
import re
import requests, zipfile, io
from typing import Tuple

# Initialize the logger
logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class DatasetType(Enum):
    BBBC = "BBBC",
    NIST_MIST = "NIST_MIST"

def viz_workflow(dataset_name : str, 
                 dataset_type : DatasetType, 
                 cwl_path : Path, 
                 dataset_path : Path, 
                 wic_path: Path,
                 compute_path : Path,
                 download: bool,
                 convert: bool,
                 montage: bool,
                 assemble_and_build_pyramid: bool,
                 build_full_viz_workflow: bool
                 ):
    """
    First version of the visualization workflow.
    The workflow configuration will largely depends on the type 
    of dataset and the specific dataset as well (thus `dataset_name`
    and `dataset_type` parameters).
    `cwl_path`, `dataset_path`, `wic_path`, `compute_path` are used as staging directories
    for the various artifacts generated.
    The boolean flags are currently used to generate only parts of the workflow.
    """

    # ensure staging dirs are available
    os.makedirs(cwl_path, exist_ok=True)
    os.makedirs(dataset_path, exist_ok=True)
    os.makedirs(wic_path, exist_ok=True)
    os.makedirs(compute_path, exist_ok=True)

    partial_workflows = []

    
    # Define our download output paths
    img_path, stitch_path = None, None
    if dataset_type == DatasetType.BBBC:
        # by convention, this is how the BBBC_Download plugin organize data
        img_path = dataset_path / "BBBC" / dataset_name / "Images"
        # no stitching vector are provided in BBBC datasets.
        stitch_path = None
    elif dataset_type == DatasetType.NIST_MIST:
        # Create our own convention for NIST MIST
        # TODO we may want to harmonize even more closely with BBBC
        img_path = dataset_path / "NIST_MIST/raw/images"
        stitch_path = dataset_path / "NIST_MIST/raw/vectors"

    if(download):
        if dataset_type == DatasetType.BBBC:
            download_bbbc_workflow = create_download_bbbc_workflow(dataset_name, cwl_path, dataset_path, wic_path)
            run_workflow(download_bbbc_workflow, compute_path)
            partial_workflows.append(download_bbbc_workflow)
        elif dataset_type == DatasetType.NIST_MIST:
            img_path, stitch_path = create_nist_mist_dataset(img_path, stitch_path)

    # Define conversion step output dir
    # That is the converted images and the converted stitching vector if available.
    # TODO CHECK somehow we need to create a single directory at the top-level 
    # Everything else will not work
    convert_out_dir = WORKING_DIR / ( dataset_name + "_convert_out" )
    os.makedirs(convert_out_dir, exist_ok=True)
    #TODO WORKAROUND. CHANGE. As all hierarchies are ignored, we shove every bit of info in the name
    convert_out_dir_vectors = convert_out_dir.with_name(convert_out_dir.name + "_vectors")
    os.makedirs(convert_out_dir_vectors, exist_ok=True)

    if(convert):
        convert_workflow = create_convert_dataset_workflow(dataset_name, dataset_type, cwl_path, dataset_path, wic_path, convert_out_dir)
        run_workflow(convert_workflow, compute_path)
        partial_workflows.append(convert_workflow)
    
        # TODO REPLACE recycle does not seem to be designed for this 
        # purpose, so for now we recycling the stitching vector manually.
        # the original image names have their first suffix set to ome after conversion.
        # we need to update the stitching vectors accordingly
        # TODO could be extended to any dataset that ships with stitching vectors.
        # TODO CHECK how should we check we have a stitching vector? 
        # For now we check for the some file name convention, which is brittle
        if dataset_type == DatasetType.NIST_MIST:
            # TODO CHECK why prepending the original image directory to each images?
            # It is probably because of wic top directory limitation, causing all images
            # to be dump in one directory.
            # We need a fix to match the original input structure.
            preprend = "image-tiles_" 
            recycle_stitching_vector(stitch_path, convert_out_dir_vectors, preprend)

    # Montage outputs have been defined earlier before convert
    if(montage):
        if(dataset_type == DatasetType.NIST_MIST):
            logger.debug("stitching already present, no montage to perform.")
        elif dataset_type == DatasetType.BBBC:
            # TODO review all input / output mecanics
            inpDir = convert_out_dir.absolute()
            # TODO CHECK inpDir, outDir and remove absolute if ok
            outDir = convert_out_dir_vectors.absolute()
            montage_workflow = create_montage_workflow(
                dataset_name, 
                dataset_type, 
                cwl_path, 
                dataset_path, 
                wic_path, 
                inpDir, 
                outDir)
            run_workflow(montage_workflow, compute_path)
            partial_workflows.append(montage_workflow)

    # Define output dir for pyramid building.
    # TODO WORKAROUD once hierarchies are functional, change.
    pyramids_dir =  WORKING_DIR / (dataset_name + "_pyramids")

    if(assemble_and_build_pyramid):

        if convert_out_dir is None or convert_out_dir_vectors is None:
            raise Exception(f"Cannot run assemble workflow. Need Images and Stitching Vector, got : {img_path} and {stitch_path}")

        pyramid_workflow = create_pyramid_workflow(
            dataset_name, 
            dataset_type, 
            cwl_path, 
            dataset_path, 
            wic_path, 
            img_path=convert_out_dir, 
            stitch_path=convert_out_dir_vectors, 
            out_dir=pyramids_dir
        )

        run_workflow(pyramid_workflow, compute_path)
        partial_workflows.append(pyramid_workflow)

        if(build_full_viz_workflow):
            outDir = pyramids_dir
            viz_workflow = build_viz_workflow(partial_workflows, img_path, convert_out_dir_vectors, outDir)
            run_workflow(viz_workflow, compute_path)

def build_viz_workflow(partial_workflows : list[Workflow], img_path, stitch_path, outDir):
    """
    Build a full visualization workflow from the partial workflow.
    This is not ideal, but a workaround the current implemetation problems.
    Eventually this is going to be cleaner when we don't have to match steps manually
    (that's one of wic promise). For that, we would probably need better descriptions of IO types.
    """
    steps = []
    
    BbbcDownload = None
    FileRenaming, OmeConverter = None, None
    Montage = None
    ImageAssembler, PrecomputeSlide = None, None

    for workflow in partial_workflows:
        steps = steps + workflow.steps

    for step in steps:
        if(step.cwl_name == "BbbcDownload"):
            BbbcDownload = step
        elif(step.cwl_name == "FileRenaming"):
            FileRenaming = step
            if(BbbcDownload):
                FileRenaming.inpDir = BbbcDownload.outDir
            else:
                FileRenaming.inpDir = img_path
        elif(step.cwl_name == "OmeConverter"):
            OmeConverter = step
            OmeConverter.inpDir = FileRenaming.outDir
        elif (step.cwl_name == "Montage"):
            Montage = step
            Montage.inpDir = OmeConverter.outDir
        elif (step.cwl_name == "ImageAssembler"):
            ImageAssembler = step
            ImageAssembler.imgPath = OmeConverter.outDir
            if(Montage):
                ImageAssembler.stitchPath = Montage.outDir
            else:
                ImageAssembler.stitchPath = stitch_path
        elif (step.cwl_name == "PrecomputeSlide"):
            PrecomputeSlide = step
            PrecomputeSlide.inpDir = ImageAssembler.outDir
            PrecomputeSlide.outDir = outDir
    
    WFNAME_viz_workflow ="workflow_viz_" + dataset_name
    viz_workflow = Workflow(steps, WFNAME_viz_workflow, path=wic_path.absolute())
    viz_workflow.compile()
    return viz_workflow



def create_nist_mist_dataset(img_path, stitch_path):
    """
    Download the NIST MIST dataset.
    """

    # Make sure the target directories exist
    os.makedirs(img_path, exist_ok=True)
    os.makedirs(stitch_path, exist_ok=True)

    FOVS_URL = (
        "https://github.com/usnistgov/MIST/wiki/testdata/Small_Phase_Test_Dataset.zip"
    )

    STITCHING_VECTOR_URL = (
        "https://github.com/usnistgov/MIST/wiki/testdata/Small_Phase_Test_Dataset_Example_Results.zip"
    )

    r = requests.get(FOVS_URL)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(img_path)
    z.close()

    img_path = img_path / "Small_Phase_Test_Dataset" / "image-tiles/"

    if not  img_path.exists:
        raise FileNotFoundError(f"could not successfully download nist_mist_dataset images")
    
    r = requests.get(STITCHING_VECTOR_URL)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(stitch_path)
    z.close()

    stitch_path = stitch_path / "Small_Phase_Test_Dataset_Example_Results/img-global-positions-0.txt"

    if not  stitch_path.exists:
        raise FileNotFoundError(f"could not successfully download nist_mist_dataset stitching vector")

    return img_path, stitch_path.parent

def create_download_bbbc_workflow(
        dataset_name : str,
        cwl_path : Path, 
        dataset_path : Path, 
        wic_path: Path) -> Workflow :
        """
        Download any BBBC dataset.
        """

        bbbcdownload = "https://raw.githubusercontent.com/saketprem/polus-plugins/bbbc_download/utils/bbbc-download-plugin/plugin.json"

        steps = create_workflow_steps([bbbcdownload], cwl_path=cwl_path)
        
        download_workflow = configure_download_bbbc_workflow(steps, dataset_name, dataset_path, wic_path)
        download_workflow.compile()
        return download_workflow

def configure_download_bbbc_workflow(steps, dataset_name, dataset_path, wic_path):
    bbbc_download = steps[0]
    bbbc_download.name = dataset_name
    # TODO ignored by bbcDownload (it only uses the current working dir)
    # output directory after our download
    bbbc_download.outDir = dataset_path.absolute()
    WFNAME_download= "workflow_download_" + dataset_name
    download_workflow= Workflow(steps, WFNAME_download, path=wic_path.absolute())
    return download_workflow

def create_convert_dataset_workflow(
        dataset_name : str, 
        dataset_type : DatasetType, 
        cwl_path : Path, 
        dataset_path : Path, 
        wic_path: Path,
        out_dir : Path
    ) -> Workflow :
    """
    Create a workflow to standardize dataset (renaming to some conventions and transform images to scalable representations.)
    """

    filerenaming = "https://raw.githubusercontent.com/PolusAI/polus-plugins/master/formats/file-renaming-plugin/plugin.json"
    omeconverter = "https://raw.githubusercontent.com/PolusAI/polus-plugins/a2666916628ab8e7d04e87d866f9b7835a86ef55/formats/ome-converter-plugin/plugin.json"

    steps = create_workflow_steps([filerenaming, omeconverter], cwl_path=cwl_path)

    workflow = None

    if dataset_type == DatasetType.BBBC:
        workflow = configure_convert_workflow_bbbc(
            dataset_name=dataset_name,
            dataset_path=dataset_path,
            wic_path=wic_path,
            out_dir=out_dir,
            steps=steps        
        )
    elif dataset_type == DatasetType.NIST_MIST:
        workflow = configure_convert_workflow_nist_mist(
            dataset_name=dataset_name,
            dataset_path=dataset_path,
            wic_path=wic_path,
            out_dir = out_dir,
            steps=steps        
        )

    if(workflow is None):
        raise Exception("Could not create workflow")
    workflow.compile()

    return workflow

def configure_convert_workflow_bbbc(
                dataset_name : str, 
                dataset_path : Path,
                wic_path: Path,
                out_dir : Path,
                steps
):
    """
    Generic configuration of the conversion workflow for the BBBC datasets.
    """

    # TODO FIX For now we reuse Sakhet's original json file and naive implementation.
    # We should revisit to at least create a better datastructure for lookup.
    config = None
    bbbc_conversion_config =  utils.load_json(BBBC_CONVERSION_CONFIG_FILE)
    for dataset_config in bbbc_conversion_config:
        if dataset_config["name"] == dataset_name:
            config = dataset_config
            break
    if config == None:
        raise Exception(f"could not find config in {BBBC_CONVERSION_CONFIG_FILE} for dataset : {dataset_name}")

    # find Images directory (Same for each BBBC_dataset)
    image_path = dataset_path / "BBBC" / dataset_name / "raw" / "Images" 
    if(not image_path.exists() and not image_path.is_dir()):
        raise Exception(f"Could not find Images directory for {dataset_name} in {image_path}")

    filerenaming, omeconverter = steps 

    filerenaming.inpDir = Path(image_path)
    filerenaming.filePattern = config["rename_filePattern"]
    filerenaming.outFilePattern = config["rename_outFilePattern"]
    #TODO CHECK is this supposed to be user defined? Why? Then make it a param.
    filerenaming.mapDirectory= 'raw'
    
    omeconverter.inpDir =  filerenaming.outDir
    #TODO REPORT bad filepattern just crash with error 1. Better reporting needed
    omeconverter.filePattern = config["ome_filePattern"]
    #TODO CHECK For now we enforce converting to .ome.tiff but it could be .ome.zarr. Make it a param?
    # it should not matter much since we generate zarr pyramids...
    omeconverter.fileExtension = ".ome.tif"
    #TODO ignored if not top-level. Need to be provided at the top level of the working directory
    omeconverter.outDir= out_dir

    WFNAME_convert="workflow_convert_" + dataset_name
    return Workflow(steps, WFNAME_convert, path=wic_path)

def configure_convert_workflow_nist_mist(
                dataset_name : str, 
                dataset_path : Path,
                wic_path: Path,
                out_dir : Path,
                steps
):
    """
    NOTE each dataset requires its own peculiar set of steps.
    """ 
    # find Images directory
    image_path = None
    image_files = []
    for dir_path, _ , _ in os.walk(dataset_path.absolute() / dataset_name):
        if(dir_path.split("/")[-1] == "image-tiles"):
            image_path = dir_path
            for _ , _ , files in os.walk(dir_path):
                for file in files:
                    if(file.endswith(".tif")):
                        image_files.append(os.path.join(dir_path, file))
    # TODO remove when the workflow execution will be more robust
    logger.debug(f"path to downloaded images : {image_path}")
    logger.debug(f"tif files downloaded : {image_files}")

    # single well. Take last part. A is well row, 03 well column, p position, d channel.
    # TODO CHECK run in isolation to verify behavior
    nist_mist = {
        "name": "NIST_MIST",
        "ome_filePattern": ".*.tif",
        "rename_filePattern": "img_r{row:ddd}_c{col:ddd}.tif",
        "rename_outFilePattern": "img_r{row:ddd}_c{col:ddd}.tif",
    }
    
    if image_path == None:
        raise Exception(f"Could not find {image_path} directory in {dataset_path}")

    filerenaming, omeconverter = steps 

    filerenaming.inpDir = Path(image_path)
    filerenaming.filePattern = nist_mist["rename_filePattern"]
    filerenaming.outFilePattern = nist_mist["rename_outFilePattern"]
    filerenaming.fileExtension = ".tif"
    filerenaming.mapDirectory= 'raw'

    omeconverter.inpDir =  filerenaming.outDir
    #TODO REPORT bad filepattern just crash with error 1. Better reporting needed
    omeconverter.filePattern = nist_mist["ome_filePattern"]
    omeconverter.fileExtension = ".ome.tif"
    omeconverter.outDir= out_dir

    WFNAME_convert="workflow_convert_" + dataset_name
    return Workflow(steps, WFNAME_convert, path=wic_path.absolute())

def recycle_stitching_vector(stitch_path : Path, out_dir : Path, prepend : str):
    """
    Temporary method that rewrite the stitching vectors according to the modifications made by
    the ome-converter/filerenaming workflow.
    """
    for vector in stitch_path.iterdir():
        with open(vector, "r") as file:
            output_vector = out_dir / vector.name
            with open(output_vector, "w") as output_file:
                # bad for very large files, replace with a stream api
                lines : list[str] = file.readlines()
                for line in lines:
                    line = line.replace(".tif",".ome.tif")
                    pattern = '([a-zA-Z_0-9])+.ome.tif'
                    result = re.search(pattern, line)
                    if result:
                        line = re.sub(pattern, prepend + result.group(), line)
                        output_file.write(line)

def create_montage_workflow(
        dataset_name : str, 
        dataset_type : DatasetType, 
        cwl_path : Path, 
        dataset_path : Path, 
        wic_path: Path,
        inpDir: Path,
        outDir: Path
    ) -> Workflow :

    montage  = "https://raw.githubusercontent.com/PolusAI/polus-plugins/master/transforms/images/montage-plugin/plugin.json"

    steps = create_workflow_steps([montage], cwl_path=cwl_path)

    workflow = None

    if dataset_type == DatasetType.BBBC:
        workflow = configure_montage_workflow_bbbc(
            dataset_name=dataset_name,
            dataset_path=dataset_path,
            wic_path=wic_path,
            inpDir= inpDir,
            outDir= outDir,
            steps=steps        
    )
    
    if(workflow is None):
        raise Exception("Could not create workflow")
    
    workflow.compile()

    return workflow

def configure_montage_workflow_bbbc(
                dataset_name : str, 
                dataset_path : Path,
                wic_path: Path,
                inpDir : Path,
                outDir : Path,
                steps
):

    montage = steps[0]

    if dataset_name == "BBBC001":
        # TODO MAKE THAT PART OF BBBC CONFIG
        montage.inpDir = inpDir
        montage.filePattern = "human_ht29_colon_cancer_1_images_x00_y03_p{p:dd}_c0.ome.tif"
        montage.layout = 'p'
        montage.outDir = outDir
    else :
        raise Exception(f"Montage : dataset not yet supported : {dataset_name}. Add configuration.")

    WFNAME_montage="workflow_montage_" + dataset_name
    return Workflow(steps, WFNAME_montage, path=wic_path.absolute())

def create_pyramid_workflow(
        dataset_name : str, 
        dataset_type : DatasetType, 
        cwl_path : Path, 
        dataset_path : Path, 
        wic_path: Path,
        img_path : Path,
        stitch_path : Path,
        out_dir : Path
    ) -> Workflow :

    image_assembler  = "https://raw.githubusercontent.com/agerardin/polus-plugins/new/image-assembler-plugin-1.4.0-dev0/transforms/images/image-assembler-plugin/plugin.json"
    precompute_slide  = "https://raw.githubusercontent.com/agerardin/polus-plugins/update/precompute-slide-fp2/visualization/precompute-slide-plugin/plugin.json"

    steps = create_workflow_steps([image_assembler, precompute_slide], cwl_path=cwl_path)

    workflow = configure_pyramid_workflow(
        dataset_name=dataset_name,
        dataset_path=dataset_path,
        wic_path=wic_path,
        steps=steps,
        img_path=img_path,
        stitch_path=stitch_path,
        out_dir=out_dir
    )
    workflow.compile()

    return workflow

def configure_pyramid_workflow(
                dataset_name : str, 
                dataset_path : Path,
                wic_path: Path,
                steps : list[Step],
                img_path: Path,
                stitch_path: Path,
                out_dir: Path
) -> Workflow :
    
    image_assembler, precompute_slide  = steps

    image_assembler.timesliceNaming = False
    image_assembler.imgPath = img_path
    image_assembler.stitchPath = stitch_path

    precompute_slide.inpDir = image_assembler.outDir
    precompute_slide.pyramidType = "Zarr"
    precompute_slide.imageType = "image"
    # TODO CHECK omitting filepattern should be fine
    # precompute_slide.filePattern = "*.*"
    precompute_slide.outDir = out_dir

    WFNAME_assemble="workflow_assemble_and_build_pyramids_" + dataset_name
    return Workflow(steps, WFNAME_assemble, path=wic_path.absolute())

def create_workflow_steps( 
        plugin_urls: list[Tuple[str,str]],
        cwl_path : Path
) -> list[Step] :
    """
    Given a list of plugins, return a list of workflow steps.
    """
    steps = []
    for plugin_url in plugin_urls:
        manifest = pp.submit_plugin(plugin_url, refresh=True)
        plugin_classname = name_cleaner(manifest.name)
        pp.refresh()
        cwl = pp.get_plugin(plugin_classname).save_cwl(cwl_path / f"{plugin_classname}.cwl")
        step = Step(cwl)
        steps.append(step)

    return steps

def run_workflow(workflow: Workflow, compute_path: Path = None):
    """
    if global RUN_LOCAL flag is set, will try to run the workflow with wic-provided cwl runner.
    otherwise will generate compute workflow spec.
    """
    if RUN_LOCAL:
        logger.debug("attempt to run workflow...")
        workflow.run(True)
    else:
        compute_workflow = create_ict_workflow(workflow)
        utils.save_json(compute_workflow, compute_path / f"{workflow.name}.json")

# TODO wic_path and compute_path and in context, but should be explicitly passed to the function
def create_ict_workflow(workflow: Workflow) :
    if workflow:
        logger.debug(f"generate a compute workflow spec for {workflow.name}...")
        workflow_spec : Path = wic_path / "autogenerated" / (workflow.name + ".cwl")
        if(not workflow_spec.exists()):
            raise FileNotFoundError(f"could not find the generated cwl worflow spec : {workflow_spec}")
        workflow_inputs : Path = wic_path / "autogenerated" / (workflow.name + "_inputs.yml")
        if(not workflow_inputs.exists()):
            raise FileNotFoundError(f"could not find the generated cwl worflow inputs : {workflow_inputs}")
        
        compute_workflow = convert_to_ict_workflow(
            workflow,
            cwl_workflow=workflow_spec,
            cwl_inputs=workflow_inputs
        )

        return compute_workflow

    

# TODO create a pydantic model for Compute? Reference it?
def convert_to_ict_workflow(
        workflow: Path,
        cwl_workflow : Path, 
        cwl_inputs: Path, 
) :
    """
    Compute defines its own standard for workflow.
    This function transform a wic generated cwl workflow into 
    a compute workflow.
    NOTE : For now we only generated a compute workflow using the argo driver
    TODO - make the driver a parameter.
    TODO - check that remove fields are not important for further processing
    """
    
    # workflow definition generated by wic
    compute = utils.load_yaml(cwl_workflow)

    # missing properties
    workflow_name = cwl_workflow.stem
    compute.update({'name': workflow_name})
    compute.update({'driver': 'argo'})

    # workflow inputs generated by wic
    inputs = utils.load_yaml(cwl_inputs)
    compute.update({'cwlJobInputs': inputs})

    # TODO CHECK Trim down unsused attributes to conform to Simo's example
    # # dollar prefixed schemas and namespaces must be rewritten
    # # workflow['schemas']= workflow['$schemas']
    del compute['$schemas']
    # # workflow['namespaces']= workflow['$namespaces']
    del compute['$namespaces']
    del compute['class']
    del compute['cwlVersion']

    for compute_step in compute["steps"]:
        if(COMPUTE_COMPATIBILITY):
            rewrite_io_paths_as_string(compute["steps"][compute_step])
            rewrite_location_as_path(compute["cwlJobInputs"])
        update_run_with_clt_definition(compute["steps"][compute_step], workflow)

    return compute

def rewrite_location_as_path(cwlJobInputs):
    """
    NOTE : COMPUTE_COMPATIBILITY
    Replace Directory `location` attribute with `path`
    """
    for input in cwlJobInputs:
        if isinstance(cwlJobInputs[input],dict) and cwlJobInputs[input]["class"] == "Directory":
            if cwlJobInputs[input].get("location"):
                cwlJobInputs[input]["path"] = cwlJobInputs[input]["location"]
                del cwlJobInputs[input]["location"]

# TODO REMOVE. This is from polus plugins. Polus plugins needs to fix this.
# The problem being that names are rewritten in polus plugins but the manifest is not updated.
# We should either enforce a strict name, generate a standardized handle, or update the manifest
# we send back when submitting plugins.
def name_cleaner(name: str) -> str:
    """Generate Plugin Class Name from Plugin name in manifest."""
    replace_chars = "()<>-_"
    for char in replace_chars:
        name = name.replace(char, " ")
    return name.title().replace(" ", "").replace("/", "_")

def base_command_exists(cwl_name, compute_step):
    """
    NOTE : COMPUTE_COMPATIBILITY
    Verify that base command are present in the cwl workflow for each clt.
    This should not be mandatory as each plugin container MUST defined an entrypoint.
    NOTE : this mechanism is brittle as we need to match the plugin's name with its generated clt cwl_name
    (TODO CHECK it is enforced) up to some conversion rules defined in the code.
    """
    try:
        compute_step["run"]["baseCommand"]
    except KeyError:
        plugin_found = False
        for plugin in pp.list_plugins():
            if(plugin == cwl_name):
                plugin_found = True
                baseCommand = pp.get_plugin(plugin).baseCommand
                if(not baseCommand):
                    raise ValueError(f"not found {plugin}.baseCommand. Check {plugin} plugin.json")
                compute_step["run"]["baseCommand"] = baseCommand
        if(not plugin_found):
            raise ValueError(f"Plugin not found : {cwl_name} in list of plugins : {pp.list_plugins()}. " +
                             f"Make sure the plugin's name in plugin.json is {cwl_name}")

def update_run_with_clt_definition(compute_step, workflow):
    """
    Update the run field of the workflow by replacing the path to a local clt
    with its full definition, according to compute workflow spec.
    """
    cwl_name = Path(compute_step["run"]).stem
    clt_file = None
    for step in workflow.steps:
        if cwl_name == step.cwl_name:
            clt_path = step.cwl_path
            clt_file = utils.load_yaml(clt_path)
            # TODO CHECK an id is necessary for compute to process the step correctly.
            # we add it.
            clt_file["id"] = cwl_name
            compute_step["run"] = clt_file
    if not clt_path.exists():
        raise Exception(f"missing plugin cwl {step.cwl_name} in {clt_path}")
    
    if(COMPUTE_COMPATIBILITY):
        base_command_exists(cwl_name, compute_step)

def rewrite_io_paths_as_string(compute_step):
    """
    NOTE : COMPUTE_COMPATIBILITY
    Compute does not currently support paths object.
    We replace them by strings.
    """
    for input in compute_step["in"]:
        compute_step["in"][input] = compute_step["in"][input]["source"] 

if __name__ == "__main__":
    # TODO CHECK everything for now must happen in the working directory
    # this seems to be a limitation for the wic integration.
    WORKING_DIR = Path("").absolute() # preprend to all path to make them absolute

    # We need a database of configuration for each BBBC dataset,
    # so we reuse Sakhet's and modify as we test them.
    # TODO REPLACE with `workflow_config.json` and update code accordingly
    # we end up recreating our own workflow description format.
    # it may be better to reuse wic format at this point.
    # Reviewing WIC API will help us decide.
    BBBC_CONVERSION_CONFIG_FILE = WORKING_DIR / "bbbc_conversion_config.json"

    # where to create CLT for WIC API? Requirement from WIC API
    cwl_path = WORKING_DIR / "data" / Path("cwl")
    # where to download datasets...
    dataset_path = WORKING_DIR / Path("datasets")
    # where to create all files related to wic. 
    # TODO CHECK this is very brittle.
    wic_path =  WORKING_DIR / "data" /  Path("wic")
    # where to create compute workflow
    compute_path = WORKING_DIR / "data" /  Path("compute")

    # Set to True to run workflow with wic-provided cwl runner.
    RUN_LOCAL=False
    # Set to True to modify wic-generated workflow to align with Compute restrictions regarding cwl.
    COMPUTE_COMPATIBILITY = True

    # For now, we need to provide both a dataset name and matching type
    # dataset_name="BBBC004"
    dataset_name="BBBC001"
    dataset_type = DatasetType.BBBC
    # dataset_name="NIST_MIST"
    # dataset_type = DatasetType.NIST_MIST

    logging.getLogger("WIC Python API").setLevel("DEBUG")

    viz_workflow(dataset_name=dataset_name,
                 dataset_type= dataset_type, 
                 cwl_path = cwl_path,
                 dataset_path = dataset_path,
                 wic_path = wic_path,
                 compute_path = compute_path,
                 download=True,
                 convert=True,
                 montage=True,
                 assemble_and_build_pyramid=True,
                 build_full_viz_workflow=True
                 )
    
    
