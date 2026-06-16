from pathlib import Path

from sophios.api.python.workflow import Step, Workflow


def workflow() -> Workflow:
    bbbcdownload = Step(clt_path='cwl_adapters/bbbcdownload.cwl')
    # NOTE: object fields monkey patched at runtime from *.cwl file
    bbbcdownload.name = 'BBBC001'
    bbbcdownload.outDir = Path('bbbcdownload.outDir')

    subdirectory = Step(clt_path='../sophios/cwl_adapters/subdirectory.cwl')
    subdirectory.directory = bbbcdownload.outDir
    subdirectory.glob_pattern = 'bbbcdownload.outDir/BBBC/BBBC001/raw/Images/human_ht29_colon_cancer_1_images/'

    filerenaming = Step(clt_path='cwl_adapters/file-renaming.cwl')
    # NOTE: FilePattern {} syntax shadows python f-string {} syntax
    filerenaming.filePattern = '.*_{row:c}{col:dd}f{f:dd}d{channel:d}.tif'
    filerenaming.inpDir = subdirectory.subdirectory
    filerenaming.outDir = Path('file-renaming.outDir')
    filerenaming.outFilePattern = 'x{row:dd}_y{col:dd}_p{f:dd}_c{channel:d}.tif'

    steps = [bbbcdownload, subdirectory, filerenaming]
    return Workflow(steps, 'bbbc_sub_py')


def workflow2() -> Workflow:
    bbbcdownload = Step(clt_path='cwl_adapters/bbbcdownload.cwl')
    # NOTE: object fields monkey patched at runtime from *.cwl file
    bbbcdownload.name = 'BBBC001'
    bbbcdownload.outDir = Path('bbbcdownload.outDir')

    subdirectory = Step(clt_path='../sophios/cwl_adapters/subdirectory.cwl')
    subworkflow = Workflow([subdirectory], 'bbbc_sub_sub_py')
    subworkflow.add_input('directory', 'Directory')
    subworkflow.add_input('glob_pattern', 'string')
    subdirectory.directory = subworkflow.inputs.directory
    subdirectory.glob_pattern = subworkflow.inputs.glob_pattern
    # Intentionally leave directory unbound; Sophios infers it from bbbcdownload.outDir.
    subworkflow.glob_pattern = 'bbbcdownload.outDir/BBBC/BBBC001/raw/Images/human_ht29_colon_cancer_1_images/'

    filerenaming = Step(clt_path='cwl_adapters/file-renaming.cwl')
    # NOTE: FilePattern {} syntax shadows python f-string {} syntax
    filerenaming.filePattern = '.*_{row:c}{col:dd}f{f:dd}d{channel:d}.tif'
    # Intentionally leave inpDir unbound; Sophios infers it from the preceding subworkflow output.
    filerenaming.outDir = Path('file-renaming.outDir')
    filerenaming.outFilePattern = 'x{row:dd}_y{col:dd}_p{f:dd}_c{channel:d}.tif'

    steps = [bbbcdownload, subworkflow, filerenaming]
    return Workflow(steps, 'bbbc_sub_py')


if __name__ == '__main__':
    viz = workflow2()
    viz.run()  # .run() here, inside main
