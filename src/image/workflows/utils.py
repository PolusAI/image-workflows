import pydantic
from pathlib import Path
from typing import Dict
from typing import Union
import yaml


GITHUB_TAG = "https://raw.githubusercontent.com"

OUT_PATH = Path.cwd()



MANIFEST_URLS = {
            "bbbc_download": f"{GITHUB_TAG}/saketprem/polus-plugins/bbbc_download/utils/bbbc-download-plugin/plugin.json",
            "file_renaming": f"{GITHUB_TAG}/hamshkhawar/image-tools/filepattern_filerenaming/formats/file-renaming-tool/plugin.json",
            "ome_converter": f"{GITHUB_TAG}/hamshkhawar/image-tools/refs/heads/fix_endian_bug_omeconverter/formats/ome-converter-tool/plugin.json",
            "estimate_flatfield": f"{GITHUB_TAG}/PolusAI/image-tools/refs/heads/master/regression/basic-flatfield-estimation-tool/plugin.json",
            "apply_flatfield": f"{GITHUB_TAG}/PolusAI/image-tools/refs/heads/master/transforms/images/apply-flatfield-tool/plugin.json",
            "kaggle_nuclei_segmentation": f"{GITHUB_TAG}/hamshkhawar/image-tools/refs/heads/kaggle_update_dependencies/segmentation/kaggle-nuclei-segmentation-tool/plugin.json",
            "ftl_plugin": f"{GITHUB_TAG}/nishaq503/image-tools/fix/ftl-label/transforms/images/polus-ftl-label-plugin/plugin.json",
            "nyxus_plugin": f"{GITHUB_TAG}/hamshkhawar/image-tools/refs/heads/nyxus_fix_entrypoint/features/nyxus-tool/plugin.json",
            "montage_url" :f"{GITHUB_TAG}/PolusAI/image-tools/refs/heads/master/transforms/images/montage-tool/plugin.json",
            "image_assembler_url": f"{GITHUB_TAG}/PolusAI/image-tools/refs/heads/master/transforms/images/image-assembler-tool/plugin.json",
            "precompute_slide_url": f"{GITHUB_TAG}/PolusAI/image-tools/refs/heads/master/visualization/precompute-slide-tool/plugin.json"
        }


# Define keys as frozensets for immutability
ANALYSIS_KEYS = frozenset([
    "name", "file_pattern", "out_file_pattern", "image_pattern", "seg_pattern", 
    "ff_pattern", "df_pattern", "group_by", "map_directory", "features", 
    "file_extension", "background_correction"
])

SEG_KEYS = frozenset([
    "name", "file_pattern", "out_file_pattern", "image_pattern", "seg_pattern", 
    "ff_pattern", "df_pattern", "group_by", "map_directory", "background_correction"
])

VIZ_KEYS = frozenset([
    "name", "file_pattern", "out_file_pattern", "image_pattern", "seg_pattern", 
    "layout", "pyramid_type", "image_type", "ff_pattern", "df_pattern", "group_by", 
    "map_directory", "background_correction"
])

# Mapping workflows to their respective keys
WORKFLOW_KEYS = {
    "analysis": ANALYSIS_KEYS,
    "segmentation": SEG_KEYS,
    "visualization": VIZ_KEYS,
}


class DataModel(pydantic.BaseModel):
    data: Dict[str, Dict[str, Union[str, bool]]]


class LoadYaml(pydantic.BaseModel):
    """Validation of Dataset YAML."""
    workflow: str
    config_path: Union[str, Path]

    @pydantic.validator("config_path", pre=True)
    @classmethod
    def validate_path(cls, value: Union[str, Path]) -> Path:
        """Validate the configuration file path."""
        path = Path(value)
        if not path.exists():
            raise ValueError(f"{value} does not exist! Please check the path again.")
        return path

    @pydantic.validator("workflow", pre=True)
    @classmethod
    def validate_workflow_name(cls, value: str) -> str:
        """Validate workflow name."""
        valid_workflows = WORKFLOW_KEYS.keys()
        if value not in valid_workflows:
            raise ValueError(f"Invalid workflow: {value}. Please choose one of {', '.join(valid_workflows)}.")
        return value

    def parse_yaml(self) -> Dict[str, Union[str, bool]]:
        """Parse the YAML configuration file for each dataset."""
        with open(self.config_path, 'r') as f:
            data = yaml.safe_load(f)

        # Check missing values in the YAML
        if any(v is None for v in data.values()):
            raise ValueError("All parameters are not defined! Please check the YAML file.")

        # Validate keys against the workflow's expected keys
        self._validate_workflow_keys(data)
        
        return data

    def _validate_workflow_keys(self, data: Dict[str, Union[str, bool]]) -> None:
        """Validate that the keys in the YAML match the expected keys for the selected workflow."""
        expected_keys = WORKFLOW_KEYS[self.workflow]
        if data.get("background_correction", False) and set(data.keys()) != expected_keys:
            raise ValueError(f"Invalid parameters for {self.workflow} workflow. Expected keys: {expected_keys}")