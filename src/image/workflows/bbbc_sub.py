from pathlib import Path

from sophios import plugins
from sophios.api import pythonapi
from sophios.api.pythonapi import Step, Workflow

def workflow() -> Workflow:
    bbbcdownload = Step(clt_path='cwl_adapters/bbbcdownload.cwl')
    # NOTE: object fields monkey patched at runtime from *.cwl file
    bbbcdownload.name = 'BBBC001'
    bbbcdownload.outDir = Path('bbbcdownload.outDir')

    subdirectory = Step(clt_path='../workflow-inference-compiler/cwl_adapters/subdirectory.cwl')
    subdirectory.directory = bbbcdownload.outDir
    subdirectory.glob_pattern = 'bbbcdownload.outDir/BBBC/BBBC001/raw/Images/human_ht29_colon_cancer_1_images/'

    filerenaming = Step(clt_path='cwl_adapters/file-renaming.cwl')
    # NOTE: FilePattern {} syntax shadows python f-string {} syntax
    filerenaming.filePattern = '.*_{row:c}{col:dd}f{f:dd}d{channel:d}.tif'
    filerenaming.inpDir = subdirectory.subdirectory
    filerenaming.outDir = Path('file-renaming.outDir')
    filerenaming.outFilePattern = 'x{row:dd}_y{col:dd}_p{f:dd}_c{channel:d}.tif'

    # Trivially wrap the subdirectory step in a subworkflow.
    # But notice that we are still linking the individual Steps above,
    # which defeats the whole purpose of having reusable black boxes.
    steps = [bbbcdownload,
             Workflow([subdirectory], 'bbbc_sub_sub_py'),
             filerenaming]
    filename = 'bbbc_sub_py'  # .yml
    return Workflow(steps, filename)


def workflow2() -> Workflow:
    bbbcdownload = Step(clt_path='cwl_adapters/bbbcdownload.cwl')
    # NOTE: object fields monkey patched at runtime from *.cwl file
    bbbcdownload.name = 'BBBC001'
    bbbcdownload.outDir = Path('bbbcdownload.outDir')

    subdirectory = Step(clt_path='../workflow-inference-compiler/cwl_adapters/subdirectory.cwl')
    subworkflow = Workflow([subdirectory], 'bbbc_sub_sub_py')  # fails validation, due to
    # https://workflow-inference-compiler.readthedocs.io/en/latest/dev/algorithms.html#deferred-satisfaction

    # First link all inputs within the subworkflow to the explicit inputs: tag.
    # i.e. This is the API for the subworkflow.
    subworkflow.steps[0].directory = subworkflow.directory
    subworkflow.steps[0].glob_pattern = subworkflow.glob_pattern

    # Then apply arguments at the call site.
    # Notice how the caller does not need to know about the internal details of the subworkflow
    # (For example, that the subdirectory step is index 0)
    subworkflow.directory = bbbcdownload.outDir
    subworkflow.glob_pattern = 'bbbcdownload.outDir/BBBC/BBBC001/raw/Images/human_ht29_colon_cancer_1_images/'

    filerenaming = Step(clt_path='cwl_adapters/file-renaming.cwl')
    # NOTE: FilePattern {} syntax shadows python f-string {} syntax
    filerenaming.filePattern = '.*_{row:c}{col:dd}f{f:dd}d{channel:d}.tif'
    filerenaming.inpDir = subworkflow.steps[0].subdirectory  # TODO: workflow outputs: tag
    filerenaming.outDir = Path('file-renaming.outDir')
    filerenaming.outFilePattern = 'x{row:dd}_y{col:dd}_p{f:dd}_c{channel:d}.tif'

    steps = [bbbcdownload,
             subworkflow,
             filerenaming]
    filename = 'bbbc_sub_py'  # .yml
    return Workflow(steps, filename)


# viz = workflow()
# viz.compile() # Do NOT .run() here

if __name__ == '__main__':
    pythonapi.global_config = plugins.get_tools_cwl(str(Path().home()))  # Use path fallback

    viz = workflow2()
    viz.run()  # .run() here, inside main
