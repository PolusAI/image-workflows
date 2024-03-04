import wic.api.pythonapi as api
import polus.plugins as pp
from pathlib import Path
import yaml
import logging
import typing
import re
import shutil
from utils import GITHUB_TAG

# Initialize the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CWLSegmentationWorkflow:
    """
    A CWL Nuclear Segmentation pipeline.

    Attributes:
        name : Name of imaging dataset of Broad Bioimage Benchmark Collection (https://bbbc.broadinstitute.org/image_sets).
        file_pattern : Pattern for parsing raw filenames.
        out_file_pattern : Preferred format for filenames
        image_pattern : Pattern for parsing intensity image filenames after renaming when using map_directory
        seg_pattern : Pattern use to parse segmentation image filenames
        map_directory :  Mapping of folder name
        ff_pattern: The filename pattern employed to select flatfield components from the ffDir.
        df_pattern:The filename pattern employed to select darkfield components from the ffDir
        group_by: Grouping variables for filePattern
    """
    def __init__(
        self,
        name: str,
        file_pattern: str,
        out_file_pattern: str,
        image_pattern: str,
        seg_pattern: str,
        ff_pattern: str,
        df_pattern: str,
        group_by: str,
        map_directory: typing.Optional[bool] = False,
    ):
        self.name = name
        self.file_pattern = file_pattern
        self.out_file_pattern = out_file_pattern
        self.map_directory = map_directory
        self.ff_pattern = ff_pattern
        self.df_pattern = df_pattern
        self.group_by = group_by
        self.wic_path = api._WIC_PATH
        self.PATH = Path(self.wic_path.parent).joinpath(Path(__file__).parts[-3])
        self.cwl_path, self.workflow_path = self._create_directories()
        self.image_pattern = image_pattern
        self.seg_pattern = seg_pattern

    def _create_directories(self) -> None:
        """Create directories for CWL outputs"""
        cwl_path = self.PATH.joinpath("cwl_adapters")
        cwl_path.mkdir(parents=True, exist_ok=True)
        workflow_path = self.PATH.joinpath("workflows").resolve()
        workflow_path.mkdir(exist_ok=True)
        return cwl_path, workflow_path

    def _clean(self) -> None:
        """Cleaning of redundant directories generating on running CWL"""
        logger.info("Cleaning directories!!!")
        destination_path = self.workflow_path.joinpath("experiment")
        dir_names = ("autogenerated", "cachedir", "RUNS", "provenance")
        for i, d in zip(self.wic_path.iterdir(), self.PATH.iterdir()):
            if i.name.endswith(dir_names):
                shutil.rmtree(d)
            if d.name.endswith(dir_names):
                shutil.rmtree(d)

        for d in destination_path.iterdir():
            if d.name.endswith("cwl_adapters"):
                shutil.rmtree(d)
        for d in self.PATH.iterdir():
            if d.name.endswith("cwl_adapters"):
                shutil.move(d, destination_path)

        return

    def _move_outputs(self) -> None:
        """Transfer outputs from the WIC directory to the workflow path"""
        logger.info("Move outputs to workflow path!!!")
        for d in self.wic_path.iterdir():
            if d.name.endswith("outdir"):
                shutil.move(d, self.workflow_path)
        return

    def _camel(self, name: str) -> str:
        """Convert plugin name to camel case."""
        name = re.sub(r"(_|-)+", " ", name).title().replace(" ", "")
        return "".join([name[0].upper(), name[1:]])

    def _string_after_period(self, x):
        """Get a string after period."""
        match = re.search(r"\.(.*)", x)
        if match:
            # Get the part after the period
            return f".*.{match.group(1)}"
        else:
            return ""

    def _add_backslash_before_parentheses(self, x):
        """Add backslash to generate ff_pattern and df_pattern"""
        # Define the regular expression pattern to match parenthesis
        pattern_1 = r"(\()|(\))"
        # Use re.sub() to add a backslash before starting and finishing parenthesis
        result = re.sub(pattern_1, r"\\\1\2", x)
        pattern_2 = r"\d"
        result = (
            result.split("_c")[0]
            + "_c{c:d}"
            + re.sub(pattern_2, "", result.split("_c")[1])
        )
        return result

    def create_step(self, url: str) -> api.Step:
        """Generate the plugin class name from the plugin name specified in the manifest"""
        manifest = pp.submit_plugin(url)
        plugin_version = str(manifest.version)
        cwl_tool = pp.get_plugin(self._camel(manifest.name), plugin_version).save_cwl(
            self.cwl_path.joinpath(f"{self._camel(manifest.name)}.cwl")
        )
        step = api.Step(cwl_tool)
        return step

    def manifest_urls(self, x: str) -> str:
        """URLs on GitHub for plugin manifests"""
        urls = {
            "bbbc_download": f"{GITHUB_TAG}/saketprem/polus-plugins/bbbc_download/utils/bbbc-download-plugin/plugin.json",
            "file_renaming": f"{GITHUB_TAG}/hamshkhawar/image-tools/filepattern_filerenaming/formats/file-renaming-tool/plugin.json",
            "ome_converter": f"{GITHUB_TAG}/hamshkhawar/image-tools/basecontainer_omecontainer/formats/ome-converter-plugin/plugin.json",
            "estimate_flatfield": f"{GITHUB_TAG}/nishaq503/image-tools/fix/basic/regression/basic-flatfield-estimation-tool/plugin.json",
            "apply_flatfield": f"{GITHUB_TAG}/hamshkhawar/image-tools/cast_images/transforms/images/apply-flatfield-tool/plugin.json",
            "kaggle_nuclei_segmentation": f"{GITHUB_TAG}/hamshkhawar/image-tools/kaggle-nucleiseg/segmentation/kaggle-nuclei-segmentation-tool/plugin.json",
            "ftl_plugin": f"{GITHUB_TAG}/nishaq503/image-tools/fix/ftl-label/transforms/images/polus-ftl-label-plugin/plugin.json"
        }
        return urls[x]

    def modify_cwl(self) -> None:
        """Modify CWL to incorporate environmental variables and permission access"""
        for f in list(self.cwl_path.rglob("*.cwl")):
            if "cwl" in f.name:
                try:
                    with Path.open(f, "r") as file:
                        config = yaml.safe_load(file)
                        config["requirements"]["NetworkAccess"] = {
                                    "networkAccess": True
                                }
                        config["requirements"]["EnvVarRequirement"] = {
                                    "envDef": {"HOME": "/home/polusai"}
                                }
                        with open(f, "w") as out_file:
                            yaml.dump(config, out_file)
                except FileNotFoundError:
                    logger.info("Error: There was an unexpected error while processing the file.")
        return

    def workflow(self) -> None:
        """
        A CWL feature extraction pipeline.
        """
        # BBBCDownload
        bbbc = self.create_step(self.manifest_urls("bbbc_download"))
        bbbc.name = self.name
        bbbc.outDir = Path("bbbc.outDir")

        # Renaming plugin
        rename = self.create_step(self.manifest_urls("file_renaming"))
        rename.filePattern = self.file_pattern
        rename.outFilePattern = self.out_file_pattern
        rename.mapDirectory = self.map_directory
        rename.inpDir = bbbc.outDir
        rename.outDir = Path("rename.outDir")

        # OMEConverter
        ome_converter = self.create_step(self.manifest_urls("ome_converter"))
        ome_converter.filePattern = self._string_after_period(self.out_file_pattern)
        ome_converter.fileExtension = ".ome.tif"
        ome_converter.inpDir = rename.outDir
        ome_converter.outDir = Path("ome_converter.outDir")

        # Estimate Flatfield
        estimate_flatfield = self.create_step(self.manifest_urls("estimate_flatfield"))
        estimate_flatfield.inpDir = ome_converter.outDir
        estimate_flatfield.filePattern = self.image_pattern
        estimate_flatfield.groupBy = self.group_by
        estimate_flatfield.getDarkfield = True
        estimate_flatfield.outDir = Path("estimate_flatfield.outDir")

        # # Apply Flatfield
        apply_flatfield = self.create_step(self.manifest_urls("apply_flatfield"))
        apply_flatfield.imgDir = ome_converter.outDir
        apply_flatfield.imgPattern = self.image_pattern
        apply_flatfield.ffDir = estimate_flatfield.outDir
        apply_flatfield.ffPattern = self.ff_pattern
        apply_flatfield.dfPattern = self.df_pattern
        apply_flatfield.outDir = Path("apply_flatfield.outDir")
        apply_flatfield.dataType = True

        ## Kaggle Nuclei Segmentation
        kaggle_nuclei_segmentation = self.create_step(
            self.manifest_urls("kaggle_nuclei_segmentation")
        )
        kaggle_nuclei_segmentation.inpDir = apply_flatfield.outDir
        kaggle_nuclei_segmentation.filePattern = self.image_pattern
        kaggle_nuclei_segmentation.outDir = Path("kaggle_nuclei_segmentation.outDir")

        ## FTL Label Plugin
        ftl_plugin = self.create_step(self.manifest_urls("ftl_plugin"))
        ftl_plugin.inpDir = kaggle_nuclei_segmentation.outDir
        ftl_plugin.connectivity = 1
        ftl_plugin.binarizationThreshold = 0.5
        ftl_plugin.outDir = Path("ftl_plugin.outDir")

        logger.info("Initiating CWL Feature Extraction Workflow!!!")
        steps = [
            bbbc,
            rename,
            ome_converter,
            estimate_flatfield,
            apply_flatfield,
            kaggle_nuclei_segmentation,
            ftl_plugin
        ]
        workflow = api.Workflow(steps, "experiment", self.workflow_path)
        # # Saving CLT for plugins
        workflow._save_all_cwl(overwrite=True)
        # # Adding environmental variables for bbbc_download and ome_converter plugin
        self.modify_cwl()
        # # # Save yaml to run CWL tool
        workflow._save_yaml()
        # Compile and run using WIC python API
        workflow.compile(run_local=True, overwrite=False)
        # # print(workflow.yml_path)
        # # clean autognerated directories
        self._clean()
        self._move_outputs()
        logger.info("Completed CWL Feature Extraction Workflow.")
        return
    