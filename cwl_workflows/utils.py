import json
import pydantic
from pathlib import Path
from typing import Dict
from typing import Union

GITHUB_TAG = "https://raw.githubusercontent.com"


class DataModel(pydantic.BaseModel):
    data: Dict[str, Dict[str, Union[str, bool]]]


class LoadData(pydantic.BaseModel):
    path: Union[str, Path]
    name:str

    @pydantic.validator("path", pre=True)
    @classmethod
    def validate_path(cls, value: Union[str, Path]) -> Union[str, Path]:
        """Validation of Paths."""
        if not Path(value).exists():
            msg = f"{value} do not exist! Please do check it again"
            raise ValueError(msg)
        if isinstance(value, str):
            return Path(value)
        return value

    def parse_json(self) -> Dict[str, Union[str, bool]]:
        with open(self.path) as json_file:
            # Read the JSON data
            data = json.load(json_file)
        params = [v[self.name] for k, v in data.items()][0]
        if len(params) == 0:
            msg = f"{self.name} dataset donot exist! Please do check it again"
            raise ValueError(msg)
        return params


seg_params = {
    "BBBC039": {
        "name": "BBBC039",
        "file_pattern": "/.*/.*/.*/Images/(?P<directory>.*)/.*_{row:c}{col:dd}_s{s:d}_w{channel:d}.*.tif",
        "out_file_pattern": "x{row:dd}_y{col:dd}_p{s:dd}_c{channel:d}.tif",
        "image_pattern": "images_x{x:dd}_y{y:dd}_p{p:dd}_c{c:d}.ome.tif",
        "seg_pattern":"images_x{x:dd}_y{y:dd}_p{p:dd}_c1.ome.tif",
        "ff_pattern": "images_x\\(00-15\\)_y\\(01-24\\)_p0\\(1-9\\)_c{c:d}_flatfield.ome.tif",
        "df_pattern": "images_x\\(00-15\\)_y\\(01-24\\)_p0\\(1-9\\)_c{c:d}_darkfield.ome.tif",
        "group_by": "c",
        "map_directory": False
    }
}
model = DataModel(data=seg_params)
model_dict = model.dict()

json_dir = Path(Path(__file__).parents[1]).joinpath("bbbc_json")
json_dir.mkdir(parents=True, exist_ok=True)
FEAT_JSON_FILENAME = json_dir.joinpath("bbbc_segmentation.json")

with Path.open(FEAT_JSON_FILENAME, "w") as json_file:
    json.dump(model_dict, json_file, indent=2)
