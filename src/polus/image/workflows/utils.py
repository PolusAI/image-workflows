import pydantic
from pathlib import Path
from typing import Dict
from typing import Union
import yaml


GITHUB_TAG = "https://raw.githubusercontent.com"


ANALYSIS_KEYS = ["name", "file_pattern", "out_file_pattern", "image_pattern", "seg_pattern", "ff_pattern", "df_pattern", "group_by", "map_directory", "features", "file_extension", "background_correction"]
SEG_KEYS = ["name", "file_pattern", "out_file_pattern", "image_pattern", "seg_pattern", "ff_pattern", "df_pattern", "group_by", "map_directory", "background_correction"]


class DataModel(pydantic.BaseModel):
    data: Dict[str, Dict[str, Union[str, bool]]]


class LoadYaml(pydantic.BaseModel):
    """Validation of Dataset yaml."""
    workflow:str
    config_path: Union[str, Path]

    @pydantic.validator("config_path", pre=True)
    @classmethod
    def validate_path(cls, value: Union[str, Path]) -> Union[str, Path]:
        """Validation of Paths."""
        if not Path(value).exists():
            msg = f"{value} does not exist! Please do check it again"
            raise ValueError(msg)
        if isinstance(value, str):
            return Path(value)
        return value
    
    @pydantic.validator("workflow", pre=True)
    @classmethod
    def validate_workflow_name(cls, value: str) -> str:
        """Validation of workflow name."""
        if not value in ["analysis", "segmentation", "visualization"]:
            msg = f"Please choose a valid workflow name i-e analysis segmentation visualization"
            raise ValueError(msg)
        return value

    def parse_yaml(self) -> Dict[str, Union[str, bool]]:
        """Parsing yaml configuration file for each dataset."""

        with open(f'{self.config_path}','r') as f: 
            data = yaml.safe_load(f)

        check_values = any([v for _, v in data.items() if f is None])

        if check_values is True:
            msg = f"All the parameters are not defined! Please do check it again"
            raise ValueError(msg)
        
        
        if self.workflow == "analysis":
            if data['background_correction'] == True:
                if list(data.keys()) != ANALYSIS_KEYS:
                    msg = f"Please do check parameters again for analysis workflow!!"
                    raise ValueError(msg)

        if self.workflow == "segmentation":
            if data['background_correction'] == True:
                if list(data.keys()) != SEG_KEYS:
                    msg = f"Please do check parameters again for segmentation workflow!!"
                    raise ValueError(msg)
        return data
