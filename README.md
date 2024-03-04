# Common Workflow Language (CWL) Feature Extraction worflow

CWL feature extraction workflow for imaging dataset

##  Workflow Steps:

create a [Conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#activating-an-environment) environment using python = ">=3.9,<3.12"

#### 1. Install polus-plugins.

- clone a image-tools repository
`git clone https://github.com/camilovelezr/image-tools.git`
- cd `image-tools`
- `pip install .`

#### 2. Install workflow-inference-compiler.
- clone a workflow-inference-compiler repository
`git clone https://github.com/camilovelezr/workflow-inference-compiler.git`
- cd `workflow-inference-compiler`
- `pip install -e ".[all]"`

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

## Execute CWL feature extraction workflow

The parameters for each imaging dataset are pre-defined and stored in JSON format. A Pydantic model in a utils Python file can be utilized to store parameters for any new dataset

`python cwl_workflows/__main__.py --name="BBBC039" --workflow=feature`

A directory named `workflow` is generated, encompassing CLTs for each plugin, YAML files, and all outputs are stored within the `outdir` directory.
```
workflows
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
