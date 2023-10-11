
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

class NotAWicNameError(Exception):
    """Raise if parameter's string does not abide to wic conventions."""

class ConfigFileNotFound(FileNotFoundError):
    """Exception raised when the config file is not found.
    """
    def __init__(self, message="Config file not found"):
        self.message = message
        super().__init__(self.message)

def _configure_steps(steps : list[Step], config):
    for step, step_config in zip(steps, config):
            step_name = next(iter(step_config.keys()))
            for key, value in step_config[step_name]['params'].items():
                # retrieve every param that needs to be linked
                if isinstance(value, dict):
                    if value['type'] == 'Path' and value.get('link'):
                        previous_step_name, previous_param_name = value['link'].split(".")
                        # find step that referenced and link them
                        for previous_step in steps:
                            if previous_step.cwl_name == previous_step_name:
                                step.__setattr__(key, previous_step.__getattribute__(previous_param_name))
                    elif value['type'] == 'Path' and value.get('path'):
                        step.__setattr__(key, Path(value['path']))
                else:
                    step.__setattr__(key, value)
    return steps

def _create_step(step_config):
    step_name = next(iter(step_config.keys()))
    plugin_manifest = step_config[step_name]['plugin']['manifest']

    if plugin_manifest:
        manifest = pp.submit_plugin(plugin_manifest, refresh=True)
        # TODO CHECK how plugin name's are renamed to abide to python class name convention is hidden 
        # in polus plugin, so we need to apply the same function here (we have cut and pasted the code)
        plugin_classname = name_cleaner(manifest.name)
        plugin_version = manifest.version.version
        # TODO CHECK if that even solves the problem or not. 
        # Plugins are not registered right away, but need the interpreter to be restarted.
        # We may have to re-run the script the first time anyhow.
        pp.refresh()
        cwl = pp.get_plugin(plugin_classname, plugin_version).save_cwl(cwl_path / f"{plugin_classname}.cwl")
        step = Step(cwl)
        logger.debug(f"create {step.cwl_name}")
    else:
        logger.warn(f"no plugin manifest in config for step {step_name}")
        # TODO use some generic plugin manifest

    return step

def _rewrite_bbbcdowload_outdir(compute_workflow, sub_path):
    bbbc_download = compute_workflow['steps']['bbbcdownload']
    if(bbbc_download):
        collection_path = Path(sub_path)
        mount_path = Path(compute_workflow['cwlJobInputs']['bbbcdownload___outDir']['path'])
        compute_workflow['cwlJobInputs']['bbbcdownload___outDir']['path'] = (mount_path / collection_path).as_posix()

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
    try: 
        config : list = utils.load_yaml(WORKING_DIR / "config" / dataset_type.name / (dataset_name + ".yaml"))
    except FileNotFoundError as e:
        raise ConfigFileNotFound("Workflow config file not found :" + e.filename)

    steps_config = config['steps']

    logger.debug(f"workflow has {len(steps_config)} steps")
    step_names = [next(iter(step.keys())) for step in steps_config]
    logger.debug(f"steps are : {step_names}")

    steps = []
    for step_config in steps_config:
        step = _create_step(step_config)
        steps.append(step)

    steps = _configure_steps(steps, steps_config)

    logger.debug([step.inputs for step in steps])

    workflow_name = "viz_workflow_" + dataset_name
    # TODO CHECK HOW WE REWRITE PATHS BECAUSE THIS IS PLAINLY IGNORED
    steps[-1].outDir = Path("POOOOOOWWW")
    workflow = Workflow(steps, workflow_name, path=wic_path)
    # TODO should be stored in workflow object rather than returned by compile()
    workflow_cwl = workflow.compile()

    if RUN_LOCAL:
        logger.debug("Running workflow locally with cwl runner...")
        workflow.run(True)
    else:
        compute_workflow = create_ict_workflow(workflow, workflow_cwl)
        # TODO REMOVE when subpath will be supported
        _rewrite_bbbcdowload_outdir(compute_workflow, config['inputs']['filerenaming.subPath'])
        utils.save_json(compute_workflow, compute_path / f"{workflow_name}.json")


def modify_bbbcdownload_output_compute_workflow(compute_workflow):
    bbbc_download = compute_workflow['steps']['bbbcdownload']
    if(bbbc_download):
        collection_path = Path(dataset_name) / "raw" / "Images" / "human_ht29_colon_cancer_1_images"
        mount_path = Path(compute_workflow['cwlJobInputs']['bbbcdownload___outDir']['path'])
        compute_workflow['cwlJobInputs']['bbbcdownload___outDir']['path'] = (mount_path / dataset_path.name / collection_path).as_posix()


def modify_bbbcdownload_output_cwl_workflow(viz_workflow):
    first_step = viz_workflow.steps[0]
    if(first_step.cwl_name == "BbbcDownload"):
        # TODO HACK while we figure out why wic refuses to 
        # compile convert_workflow with filrenaming `subPath`` parameter.
        collection_path = Path("BBBC") / dataset_name / "raw" / "Images" / "human_ht29_colon_cancer_1_images"
        first_step.outDir = dataset_path / collection_path


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
    # filerenaming.mapDirectory= 'raw'

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

# TODO wic_path and compute_path and in context, but should be explicitly passed to the function
def create_ict_workflow(workflow: Workflow, workflow_cwl : Path) :
    logger.debug(f"Generating compute workflow spec for {workflow.name}...")

    # TOD workflow_cwl should be stored in the workflow object
    if(not workflow_cwl.exists()):
        raise FileNotFoundError(f"could not find the generated cwl worflow : {workflow_cwl}")
    
    # TODO should be stored in the workflow object
    workflow_inputs : Path = wic_path / "autogenerated" / (workflow.name + "_inputs.yml")
    if(not workflow_inputs.exists()):
        raise FileNotFoundError(f"could not find the generated cwl worflow inputs : {workflow_inputs}")
    
    compute_workflow = convert_to_compute_workflow(
        workflow,
        cwl_workflow=workflow_cwl,
        cwl_inputs=workflow_inputs
    )

    return compute_workflow

# TODO create a pydantic model for Compute? Reference it?
def convert_to_compute_workflow(
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
    """
    # workflow definition generated by wic
    compute = utils.load_yaml(cwl_workflow)

    add_missing_workflow_properties(compute, cwl_workflow, cwl_inputs)
    remove_unused_workflow_properties(compute)

    for compute_step in compute["steps"]:
        if(COMPUTE_COMPATIBILITY):
            rewrite_io_paths_as_string(compute["steps"][compute_step])
            rewrite_location_as_path(compute["cwlJobInputs"])
        
        replace_run_with_clt_definition(compute["steps"][compute_step], workflow) 
        add_step_run_id(compute["steps"][compute_step])

        if(COMPUTE_COMPATIBILITY):
            add_step_run_base_command(compute["steps"][compute_step])

    update_all_paths_on_remote_target(compute["cwlJobInputs"])
    rewrite_all_plugin_prefixes(compute)

    return compute

def add_missing_workflow_properties(compute, cwl_workflow, cwl_inputs):
    # missing properties
    workflow_name = cwl_workflow.stem
    compute.update({'name': workflow_name})
    compute.update({'driver': DRIVER})

    # workflow inputs generated by wic
    inputs = utils.load_yaml(cwl_inputs)
    compute.update({'cwlJobInputs': inputs})

def remove_unused_workflow_properties(compute):
        # TODO CHECK Trim down unsused attributes to conform to Simo's example
    # previously dollar prefixed schemas and namespaces had to be rewritten
    # workflow['schemas']= workflow['$schemas']
    del compute['$schemas']
    # workflow['namespaces']= workflow['$namespaces']
    del compute['$namespaces']
    del compute['class']
    del compute['cwlVersion']

def rewrite_all_plugin_prefixes(compute):
    for section in [compute["cwlJobInputs"], compute["inputs"], compute["outputs"], compute["steps"]]:
        update_wic_keys(section)
    for step in compute["steps"]:
        update_wic_values(compute["steps"][step]["in"])
    for output in compute["outputs"]:
        update_wic_values(compute["outputs"][output])

def update_wic_values(step):
    for k,v in step.items():
        try:
            parsed_v = get_info_from_wic_name(v)
            if(parsed_v):
                dependency_param = parsed_v[2].split("/")
                if len(dependency_param) == 2:
                    new_v = sanitize_for_compute_argo(dependency_param[0]) + "/" + dependency_param[1]
                else:
                    new_v = sanitize_for_compute_argo(parsed_v[2])
                    if parsed_v[3] != None:
                        new_v = new_v + "___" + parsed_v[3]
                step[k] = new_v
        except NotAWicNameError:
            pass #ignore if not in wic format    

def update_wic_keys(json):
    keys = list(json)
    for k in keys:
        try:
            parsed_k = get_info_from_wic_name(k)
            if(parsed_k):
                new_k = sanitize_for_compute_argo(parsed_k[2])
                if parsed_k[3] != None:
                    new_k = new_k + "___" + parsed_k[3]
                json[new_k] = json.pop(k)
        except NotAWicNameError:
            pass #ignore if not in wic format

def _rewrite_all_plugin_prefixes(compute):
    all_things = walk_workflow(compute, None, None)
    for thing in all_things:
        context, entry, key = thing
        try: 
            result = get_info_from_wic_name(key)
            context.update({key: "___" + key})
        except NotAWicNameError:
            pass


def walk_workflow(context, entry, key):
    if isinstance(entry, dict):
        for k,v in entry.items():
            yield context, entry, k
            yield from walk_workflow(context, context[k], v)
    # elif isinstance(context, list):
    #     for index, item in enumerate(context):
    #         yield from walk_workflow(context[index], item)

def update_fully_qualified_name(json_input, input, index):
    try:
        workflow_name, step_index, step_name, param = get_info_from_wic_name(input)
        print("rewrite_all_plugin_prefixes : ", input)
        json_input[index] = "____" + input
    except ValueError:
        pass

def update_all_paths_on_remote_target(cwlJobInputs):
    """
    TODO NEEDS UPDATE
        wic-generated cwlJobInputs directory paths are of two kinds :
        - absolute path : when the directory's path is provided by the user
        - single directory name : when the directory is a staging directory
          generated by wic for a intermediary result.
        Compute argo driver will actually mount volumes for each container 
        running a step. We thus need to translate wic-generated paths to argo-compatible
        paths.
        - for absolute path, we translate for the host path to the path within the container
        - for single directory name, we translate to an argo compatible path within the container.
    """

    # check first with attribute we need to udpdate
    if(COMPUTE_COMPATIBILITY):
        directory_attr = "path"
    else: 
        directory_attr = "location"
    
    for input in cwlJobInputs:
        if isinstance(cwlJobInputs[input],dict) and cwlJobInputs[input]["class"] == "Directory":
            path : str = cwlJobInputs[input][directory_attr]
            if path.startswith(WORKING_DIR.as_posix()):
                argo_compatible_step_name = sanitize_for_compute_argo(get_info_from_wic_name(input)[0])
                target_path = (TARGET_DIR / argo_compatible_step_name).as_posix()
                cwlJobInputs[input][directory_attr] = path.replace(WORKING_DIR.as_posix(), target_path)
            else:
                try:
                    _ , _, step_name, _ = get_info_from_wic_name(input)
                    cwlJobInputs[input][directory_attr] = (TARGET_DIR / 
                    sanitize_for_compute_argo(step_name)).as_posix()
                except NotAWicNameError:
                    pass # ignore if not in wic format

def get_info_from_wic_name(wic_name: str):
    param = None
    step_or_param = wic_name.split("___")
    step = step_or_param[0]
    if(len(step_or_param) == 2):
        param = step_or_param[1]
    try: 
        workflow_name, _ , step_index, step_name = step.split("__")
        return workflow_name, step_index, step_name, param
    except:
        raise NotAWicNameError

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

def add_step_run_base_command(compute_step):
    """
    NOTE : COMPUTE_COMPATIBILITY
    Verify that base command are present in the cwl workflow for each clt.
    This should not be mandatory as each plugin container MUST defined an entrypoint.
    NOTE : this mechanism is brittle as we need to match the plugin's name with its generated clt cwl_name
    (TODO CHECK it is enforced) up to some conversion rules defined in the code.
    """
    cwl_name = compute_step["run"]["name"]
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


def sanitize_for_compute_argo(step_name : str):
    """
    Argo have specific requirements about how it forms its name that differs from
    those of wic.
    Argo abides by Kubernetes naming conventions. 
    Step names are supposed to be valid kubernetes container names
    [TODO add link to spec]
    """
    return step_name.replace("_","-").replace(" ","").lower()

def replace_run_with_clt_definition(compute_step, workflow):
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
            clt_file['name'] = cwl_name
            compute_step["run"] = clt_file
    if not clt_path.exists():
        raise Exception(f"missing plugin cwl {step.cwl_name} in {clt_path}")

def add_step_run_id(compute_step):
    """
    An id is necessary for compute to process the step correctly.
    Generate id based on the plugin name, 
    transformed to abide argo-driver spec for names.
    TODO CHECK if this is only an argo requirement or more generally
    a compute requirement.
    """
    cwl_name = compute_step["run"]["name"]
    compute_step["run"]["id"] = sanitize_for_compute_argo(cwl_name)

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

    # TODO HACK as it seems wic expects the workflow to be executed 
    # on the machine wic is run on.
    TARGET_DIR = Path("/data/outputs/")

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

    DRIVER= 'argo'

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
                 download=False,
                 convert=False,
                 montage=False,
                 assemble_and_build_pyramid=False,
                 build_full_viz_workflow=False
                 )
