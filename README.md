# Common Workflow Language (CWL) Workflows

CWL feature extraction workflow for imaging dataset

##  Workflow Steps:

create a [Conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#activating-an-environment) environment using python = ">=3.9,<3.12"

#### 1. Install polus-plugins.

- clone a image-tools repository
`git clone https://github.com/camilovelezr/image-tools.git ../`
- cd `image-tools`
- create a new branch
`git checkout -b hd2  remotes/origin/hd2`
- `pip install .`

#### 2. Install workflow-inference-compiler.
- clone a workflow-inference-compiler repository
`git clone https://github.com/camilovelezr/workflow-inference-compiler.git ../`
- cd `workflow-inference-compiler`
- create a new branch
`git checkout -b hd2  remotes/origin/hd2`
- `pip install -e ".[all]"`

#### 3. Install image-workflow.
- cd `image-workflows`
- poetry install

#### Note:
Ensure that the [docker-desktop](https://www.docker.com/products/docker-desktop/) is running in the background. To verify that it's operational, you can use the following command:
`docker run -d -p 80:80 docker/getting-started` 
This command will launch the `docker/getting-started container` in detached mode (-d flag), exposing port 80 on your local machine (-p 80:80). It's a simple way to test if Docker Desktop is functioning correctly.

## Details 
This workflow integrates eight distinct plugins, starting from data retrieval from [Broad Bioimage Benchmark Collection](https://bbbc.broadinstitute.org/), renaming files, correcting uneven illumination, segmenting nuclear objects, and culminating in the extraction of features from identified objects

Below are the specifics of the plugins employed in the workflow
1. [bbbc-download-plugin](https://github.com/saketprem/polus-plugins/tree/bbbc_download/utils/bbbc-download-plugin)
2. [file-renaming-tool](https://github.com/PolusAI/image-tools/tree/master/formats/file-renaming-tool)
3. [ome-converter-tool](https://github.com/PolusAI/image-tools/tree/master/formats/ome-converter-tool)
4. [basic-flatfield-estimation-tool](https://github.com/PolusAI/image-tools/tree/master/regression/basic-flatfield-estimation-tool)
5. [apply-flatfield-tool](https://github.com/PolusAI/image-tools/tree/master/transforms/images/apply-flatfield-tool)
6. [kaggle-nuclei-segmentation](https://github.com/hamshkhawar/image-tools/tree/kaggle-nuclei_seg/segmentation/kaggle-nuclei-segmentation)
7. [polus-ftl-label-plugin](https://github.com/hamshkhawar/image-tools/tree/kaggle-nuclei_seg/transforms/images/polus-ftl-label-plugin)
8. [nyxus-plugin](https://github.com/PolusAI/image-tools/tree/kaggle-nuclei_seg/features/nyxus-plugin)

## Execute CWL workflows
Three different CWL workflows can be executed for specific datasets
1. segmentation
2. analysis

During the execution of the segmentation workflow, `1 to 7` plugins will be utilized. However, for executing the analysis workflow, `1 to 8` plugins will be employed.
If a user wishes to execute a workflow for a new dataset, they can utilize a sample YAML file to input parameter values. This YAML file can be saved in the desired subdirectory of the `configuration` folder with the name `dataset.yml`

If a user opts to run a workflow without background correction, they can set `background_correction` to false. In this case, the workflow will skip steps `4 and 5`

`python -m polus.image.workflows  --name="BBBC001" --workflow=analysis`

A directory named `outputs` is generated, encompassing CLTs for each plugin, YAML files, and all outputs are stored within the `outdir` directory.
```
outputs
├── experiment
│   └── cwl_adapters
|   experiment.cwl
|   experiment.yml
|
└── outdir
    └── experiment
        ├── step 1 BbbcDownload
        │   └── outDir
        │       └── bbbc.outDir
        │           └── BBBC
        │               └── BBBC039
        │                   └── raw
        │                       ├── Ground_Truth
        │                       │   ├── masks
        │                       │   └── metadata
        │                       └── Images
        │                           └── images
        ├── step 2 FileRenaming
        │   └── outDir
        │       └── rename.outDir
        ├── step 3 OmeConverter
        │   └── outDir
        │       └── ome_converter.outDir
        ├── step 4 BasicFlatfieldEstimation
        │   └── outDir
        │       └── estimate_flatfield.outDir
        ├── step 5 ApplyFlatfield
        │   └── outDir
        │       └── apply_flatfield.outDir
        ├── step 6 KaggleNucleiSegmentation
        │   └── outDir
        │       └── kaggle_nuclei_segmentation.outDir
        ├── step 7 FtlLabel
        │   └── outDir
        │       └── ftl_plugin.outDir
        └── step 8 NyxusPlugin
            └── outDir
                └── nyxus_plugin.outDir

```
#### Note:
Step 7 and step 8 are executed only in the case of the `analysis` workflow.