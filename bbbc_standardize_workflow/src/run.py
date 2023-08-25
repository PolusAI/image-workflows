"""Standardization Workflow."""

### links

# polus.plugins: https://github.com/camilovelezr/polus-plugins/tree/cwl3
# wic.api: https://github.com/camilovelezr/workflow-inference-compiler/tree/viz
# precomputeslide: https://github.com/agerardin/polus-plugins/tree/update/precompute-slide
# filerenaming: https://github.com/hamshkhawar/polus-plugins/tree/update/file-renaming
# assembler: https://github.com/agerardin/polus-plugins/tree/fix/image-assembler-plugin-v1.3.0-dev0
# omeconverter: https://github.com/hamshkhawar/polus-plugins/tree/omeconverter
# montage: current polus-plugins master


from pathlib import Path
import json
import os
import pydantic
import skimage.io as io
from typing import Union
import shutil
import time
from skimage import color
import logging
import typer
import logging

import polus.plugins as pp
from wic.api import Step, Workflow

ROOT_PATH = Path(__file__).parent.absolute()

# Initialize the logger
logging.basicConfig(
    format="%(asctime)s - %(name)-8s - %(levelname)-8s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logger = logging.getLogger("polus.plugins.utils.bbbc_download")
logger.setLevel(os.environ.get("POLUS_LOG", logging.INFO))

multiple_channels= [
    "BBBC015",
    "BBBC028",
    "BBBC030",
    "BBBC031",
    "BBBC033",
    "BBBC042",
    "BBBC011"]

multiple_channels_gt= [
    "BBBC004"]

ground_truth=[
    "BBBC003",#containis txt file
    "BBBC004",
    "BBBC005",
    "BBBC007",#multiple regex
    "BBBC008",
    "BBBC009",
    "BBBC010",#multiple formats gt has png and images as tif
    "BBBC018"# grounf truth is png
]

DIB_images=[
    "BBBC018"
]



# submit_plugin
pp.submit_plugin(
    "https://raw.githubusercontent.com/saketprem/polus-plugins/bbbc_download/utils/bbbc-download-plugin/plugin.json"
)
pp.submit_plugin(
    "https://raw.githubusercontent.com/PolusAI/polus-plugins/master/formats/file-renaming-plugin/plugin.json"
)
pp.submit_plugin(
    "https://raw.githubusercontent.com/PolusAI/polus-plugins/a2666916628ab8e7d04e87d866f9b7835a86ef55/formats/ome-converter-plugin/plugin.json"
)


pp.refresh()
print(pp.list)
app = typer.Typer()

# # # generate cwl clt
pp.BbbcDownload.save_cwl(ROOT_PATH.with_name("bbbcdownload.cwl"))
pp.FileRenaming.save_cwl(ROOT_PATH.with_name("filerenaming.cwl"))
pp.OmeConverter.save_cwl(ROOT_PATH.with_name("omeconverter.cwl"))

bbbcdownload=Step(ROOT_PATH.with_name("bbbcdownload.cwl"))
filerenaming = Step(ROOT_PATH.with_name("filerenaming.cwl"))
omeconverter = Step(ROOT_PATH.with_name("omeconverter.cwl"))
filerenaming1 = Step(ROOT_PATH.with_name("filerenaming.cwl"))
omeconverter1 = Step(ROOT_PATH.with_name("omeconverter.cwl"))

class dataset(pydantic.BaseModel):
    """Class that contains name of the dataset and the standardize function"""
    name: str

    @pydantic.validator("name")
    @classmethod
    def validate_dataset(cls,name: str)-> str:
        """Validates the name of the dataset.

        Args:
            name: The name of the dataset to be downloaded.

        Returns:
            The name provided if validation is successful.
        """
        json_file_path=ROOT_PATH.joinpath("imageInfo.json")
        with json_file_path.open("r") as file:
            data = json.load(file)
        check=0
        for row in data:
            if(name==row["name"]):
                check=1
        if(check==0):
            raise ValueError(
                name
                + " is an invalid dataset name. Valid dataset names belong to an existing BBBC dataset."
            )
        return name
    
    @classmethod
    def create_standard_dataset(cls, name: str) -> Union["dataset", None]:
        """Creates an object of the class.
        Args:
            name: The name of the dataset to be downloaded.
        Returns:
            The object of the class.
        """
        try:
            if name in DIB_images:
                return DIB_image(name=name)
            
            elif name in ground_truth:
                return dataWithGroundTruth(name=name)
            
            else:
                return dataset(name=name)
        except ValueError as e:
            print(e)

            return None


    def remove_channel(self, image_path: Path, file_pattern: str)-> None:
        """Converts RGB image to grayscale
        Args:
            image_path: Path to the images that need to be converted
            file_pattern: input file format.
        """
        print("removing excess channels")
        folders=[folders for folders in image_path.iterdir() if folders.is_dir()]
        image_pattern=file_pattern[1:]
        if(len(folders)==0):
            folders.append(image_path)
        for input_path in folders:
            for images in input_path.glob(image_pattern):
                if (image_pattern=="*.tif" or image_pattern=="*.TIF"):
                    color_image=io.imread(images)
                    gray_image = color.rgb2gray(color_image)
                    io.imsave(images,gray_image)
                else:
                    color_image=io.imread(images)
                    gray_image = color.rgb2gray(color_image)
                    grayscale_image_uint8 = (gray_image * 255).astype('uint8')
                    io.imsave(images,grayscale_image_uint8)



    

    def standard_download(self, mapDirectory: str):
        """Creates a workflow to downloads the dataset and standardize it.
         Args:
          mapDirectory: specifies the way to map directory for the file renaming plugin
          """
        json_file_path=ROOT_PATH.joinpath("imageInfo.json")
        with json_file_path.open("r") as file:
            data = json.load(file)

        for row in data:
            if(self.name==row["name"]):
                ome_filePattern=row["ome_filePattern"]
                rename_filePattern=row["rename_filePattern"]
                rename_outFilePattern=row["rename_outFilePattern"]

        bbbcdownload.name=self.name
        bbbcdownload.outDir=ROOT_PATH.joinpath("download")
        input_path=ROOT_PATH.joinpath("download","BBBC",self.name,"raw","Images")

        if(not input_path.exists()):
            WFNAME_download="download"+self.name
            wf1=Workflow([bbbcdownload], WFNAME_download, path=ROOT_PATH)
            try:
                wf1.compile()
            
            except Exception as e:
                print(f"Warning occured: {e}")
            wf1.run()
            
            # p1=pp.BbbcDownload
            # p1.name=self.name
            # p1.outDir=ROOT_PATH.joinpath("download")
            # p1.run(gpus=None)

            if self.name in multiple_channels:
                self.remove_channel(image_path=input_path, file_pattern=ome_filePattern)
            

        

        filerenaming.inpDir = input_path
        filerenaming.filePattern = rename_filePattern
        filerenaming.outFilePattern = rename_outFilePattern
        filerenaming.mapDirectory=mapDirectory

        omeconverter.inpDir =  filerenaming.outDir # CHANGEME
        omeconverter.filePattern = ome_filePattern  # CHANGEME
        omeconverter.fileExtension = ".ome.tif"  # CHANGEME
        omeconverter.outDir=ROOT_PATH.joinpath("outdir",self.name,"Images")

        WFNAME1 = self.name  # CHANGEME
        wf1 = Workflow([filerenaming, omeconverter], WFNAME1, path=ROOT_PATH)   
        try:
            wf1.compile()
        
        except Exception as e:
            print(f"Warning occured: {e}")
        os.chdir(omeconverter.outDir.value.parent)
        wf1.run()

class DIB_image(dataset):
    """If dataset contins DIB images this class object is created"""
    def standard_download(self, mapDirectory: str):
        """Creates a workflow to downloads the dataset and standardize it.
         Args:
          mapDirectory: specifies the way to map directory for the file renaming plugin
          """
        json_file_path=ROOT_PATH.joinpath("imageInfo.json")
        with json_file_path.open("r") as file:
            data = json.load(file)

        for row in data:
            if(self.name==row["name"]):
                ome_filePattern=row["ome_filePattern"]
                rename_filePattern=row["rename_filePattern"]
                rename_outFilePattern=row["rename_outFilePattern"]

        bbbcdownload.name=self.name
        bbbcdownload.outDir=ROOT_PATH.joinpath("download")
        input_path=ROOT_PATH.joinpath("download","BBBC",self.name,"raw","Images","BBBC018_v1_images")

        if(not input_path.exists()):
            WFNAME_download="download"+self.name
            wf1=Workflow([bbbcdownload], WFNAME_download, path=ROOT_PATH)
            try:
                wf1.compile()
            
            except Exception as e:
                print(f"Warning occured: {e}")
            wf1.run()


        omeconverter.inpDir =  input_path # CHANGEME
        omeconverter.filePattern = ome_filePattern  # CHANGEME
        omeconverter.fileExtension = ".ome.tif"  # CHANGEME
        

        filerenaming.inpDir = omeconverter.outDir
        filerenaming.filePattern = rename_filePattern
        filerenaming.outFilePattern = rename_outFilePattern
        filerenaming.outDir=ROOT_PATH.joinpath("outdir",self.name)

        WFNAME1 = self.name  # CHANGEME
        wf1 = Workflow([omeconverter, filerenaming], WFNAME1, path=ROOT_PATH)   
        try:
            wf1.compile()
        
        except Exception as e:
            print(f"Warning occured: {e}")
        os.chdir(filerenaming.outDir.value.parent)
        wf1.run()

class dataWithGroundTruth(dataset):
    """Class if the data consists of both ground truth and images"""
    def standard_download(self, mapDirectory: str):
        """Creates a workflow to downloads the dataset and standardize it.
         Args:
          mapDirectory: specifies the way to map directory for the file renaming plugin
          """
        json_file_path=ROOT_PATH.joinpath("imageInfo.json")
        with json_file_path.open("r") as file:
            data = json.load(file)

        for row in data:
            if(self.name==row["name"]):
                ome_filePattern=row["ome_filePattern"]
                rename_filePattern=row["rename_filePattern"]
                rename_outFilePattern=row["rename_outFilePattern"]

        data=["Images","Ground_Truth"]

        bbbcdownload.name=self.name
        bbbcdownload.outDir=ROOT_PATH.joinpath("download")
        
        input_path=ROOT_PATH.joinpath("download","BBBC",self.name,"raw")

        if(not input_path.exists()):
            WFNAME_download="download"+self.name
            wf1=Workflow([bbbcdownload], WFNAME_download, path=ROOT_PATH)
            try:
                wf1.compile()
            
            except Exception as e:
                print(f"Warning occured: {e}")
            wf1.run()

        for i in data:
            input_path=ROOT_PATH.joinpath("download","BBBC",self.name,"raw",i)
            # image_path=input_path.joinpath("Images")
            # truth_path=input_path.joinpath("Ground_Truth")

            if self.name in multiple_channels_gt and i=="Ground_Truth":
                self.remove_channel(image_path=input_path, file_pattern=ome_filePattern)

            filerenaming.inpDir = input_path
            filerenaming.filePattern = rename_filePattern
            filerenaming.outFilePattern = rename_outFilePattern
            filerenaming.mapDirectory=mapDirectory

            omeconverter.inpDir =  filerenaming.outDir # CHANGEME
            omeconverter.filePattern = ome_filePattern  # CHANGEME
            omeconverter.fileExtension = ".ome.tif"  # CHANGEME
            omeconverter.outDir=ROOT_PATH.joinpath("outdir",self.name,i)

            # filerenaming1.inpDir = truth_path
            # filerenaming1.filePattern = rename_filePattern
            # filerenaming1.outFilePattern = rename_outFilePattern
            # filerenaming1.mapDirectory='raw'

            # omeconverter1.inpDir =  filerenaming1.outDir # CHANGEME
            # omeconverter1.filePattern = ome_filePattern  # CHANGEME
            # omeconverter1.fileExtension = ".ome.tif"  # CHANGEME
            # omeconverter1.outDir=ROOT_PATH.joinpath("outdir",self.name,"Ground_Truth")

            WFNAME1 = self.name+"_"+i # CHANGEME
            wf1 = Workflow([filerenaming, omeconverter], WFNAME1, path=ROOT_PATH)   
            try:
                wf1.compile()
            
            except Exception as e:
                print(f"Warning occured: {e}")
            os.chdir(omeconverter.outDir.value.parent)
            wf1.run()

@app.command()
def main(
    name: str = typer.Option(
        ...,
        "--name",
        help="The name of the dataset that is to be downloaded.",
    ),
    mapDirectory: str = typer.Option(
        ...,
        "--mapDirectory",
        help="Method to map the directory.",
    )

) -> None:
    logger.info(f"name = {name}")
    d= dataset.create_standard_dataset(name)
    d.standard_download(mapDirectory=mapDirectory)

if __name__ == "__main__":
    app()
