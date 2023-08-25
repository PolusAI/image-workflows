# BBBC STANDARDIZE WORKFLOW

The aim of this workflow is to download and standardize the all the datasets in the broad bioimage benchmark collection.

There are 3 steps to the workflow:
step1: downlaod the dataset using the bbbc download plugin
step2: rename the files to the standard format using the file renaming plugin
step3: convert the images to ome.tif using the ome converter plugin

The status of the workflow for the datasets 
| Name of Dataset | Status of raw Images                                                                              |  Status of Ground Truth |
|-----------------|---------------------------------------------------------------------------------------------------|-------------------------|
| BBBC001         | Working                                                                                           |No ground truth images   |
| BBBC002         | Not Working, multiple regular expression.                                                         |No ground truth images  |
| BBBC003         | Working                                                                                           |Not working as txt file is also present   |
| BBBC004         | Working                                                                                           |Working |
| BBBC005         | Working                                                                                           |working   |
| BBBC006         | Working                                                                                           |No ground truth images |
| BBBC007         | Not Working, multiple regular expression.                                                         |multiple regex   |
| BBBC008         | Working                                                                                           |Working   |
| BBBC009         | Working                                                                                           |Working  |
| BBBC010         | Working                                                                                           |ground truth and raw images are of different format  |
| BBBC011         | working                                                                                           |No ground truth images  |
| BBBC012         | Contains nested folder.                                                                           |No ground truth images   |
| BBBC013         | Contains 2 different image formats                                                                |No ground truth images  |
| BBBC014         | Working                                                                                           |No ground truth images   |
| BBBC015         |  Working                                                                                          |No ground truth images   |
| BBBC016         |  Working                                                                                          |No ground truth images   |
| BBBC017         |  Need to run ome converter first.                                                                 |No ground truth images   |
| BBBC018         | Working(run ome converter first)                                                                  | grounf truth is png and raw images is DIB  |
| BBBC019         | Contains nested folders                                                                           |Not tested as it contains nested folders |
| BBBC020         |  Contains multiple regex                                                                          |Not testes as it requires mutiple regex   |
| BBBC021         | Working                                                                                           |No ground truth images   |
| BBBC022         | Working                                                                                           |No ground truth images  |
| BBBC022         | Working                                                                                           |No ground truth images   |
| BBBC024         | Not Working                                                                                       |Not tested   |
| BBBC025         |  error while download dataset                                                                     |unable to download dataset   |
| BBBC026         | Working                                                                                           |Not tested   |
| BBBC027         | Working(need to do for each folder seperately)                                                    |Not tested  |
| BBBC028         | working                                                                                           |Not tested   |
| BBBC029         |  Not Working                                                                                      |Not tested   |
| BBBC030         | working                                                                                           |Not tested   |
| BBBC031         | Multiple regex                                                                                    |No ground truth images   |
| BBBC032         |  Working                                                                                          |Not tested   |
| BBBC033         | working                                                                                           |Not tested   |
| BBBC034         | working                                                                                           |No ground truth images   |
| BBBC035         |  Working                                                                                          |Not tested   |
| BBBC036         |  download not workinig                                                                            |not downloading  |
| BBBC037         |  download not working                                                                             |not downloading   |
| BBBC038         | Need to manually convert due to random image names                                                |not tested  |
| BBBC039         |  Working                                                                                          |Not tested  |
| BBBC041         |  Need to manually convert due to random image names                                               |not tested   |
| BBBC042         | working                                                                                           |Not tested   |
| BBBC044         |  Contains nested folder.                                                                          |Not tested   |
| BBBC045         |  Required multiple regex                                                                          |Not tested   |
| BBBC046         |  Cannot download dataset                                                                          |Cannot download dataset   |
| BBBC047         |  download not working                                                                             |download not working   |
| BBBC048         | contains subfolders                                                                               |contains subfolders    |
| BBBC050         | Contains subfolders                                                                               |contains subfolders    |
| BBBC051         | contains suubfolders                                                                              |contains subfolders    |
| BBBC052         |  Requires multiple regular expression and sepereate conversion as there are multiple sub folders. |contains subfolders    |
| BBBC053         |  contains subfolder                                                                               |contains subfolders    |
| BBBC054         | Working                                                                                           |No ground truth images   |

## How to use
Fork the WIC repository[Camilo's branch](https://github.com/camilovelezr/workflow-inference-compiler/tree/viz)
For the polus plugins repository [bbbc_download branch](https://github.com/saketprem/polus-plugins)

Install both the repositories as python packege using pip install

Install graphviz

Run the file run.py with the input argumets name and mapDirectory
## Options

This plugin takes 2 input arguments:

| Name            | Description                                                  | I/O    | Type        |
| --------------- | ------------------------------------------------------------ | ------ | ----------- |
| `--name  `      | The name of the datasets to be downloaded and standardized   | Input  | String      |
| `--mapDirectory`| Directory name (raw, map)                                    | Output | genericData |

Example of how to run:
`python run.py --name='BBBC001' --mapDirectory='raw'`

