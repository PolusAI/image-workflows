from pathlib import Path

from sophios.api.pythonapi import Step, Workflow

def workflow() -> Workflow:
    bbbcdownload = Step(clt_path='../image-workflows/cwl_adapters/bbbcdownload.cwl')
    # NOTE: object fields monkey patched at runtime from *.cwl file
    bbbcdownload.name = 'BBBC001'
    bbbcdownload.outDir = Path('bbbcdownload.outDir')

    subdirectory = Step(clt_path='../workflow-inference-compiler/cwl_adapters/subdirectory.cwl')
    subdirectory.directory = bbbcdownload.outDir
    subdirectory.glob_pattern = 'bbbcdownload.outDir/BBBC/BBBC001/raw/Images/human_ht29_colon_cancer_1_images/'

    filerenaming = Step(clt_path='../image-workflows/cwl_adapters/file-renaming.cwl')
    # NOTE: FilePattern {} syntax shadows python f-string {} syntax
    filerenaming.filePattern = '.*_{row:c}{col:dd}f{f:dd}d{channel:d}.tif'
    filerenaming.inpDir = subdirectory.subdirectory
    filerenaming.outDir = Path('file-renaming.outDir')
    filerenaming.outFilePattern = 'x{row:dd}_y{col:dd}_p{f:dd}_c{channel:d}.tif'

    omeconverter = Step(clt_path='../image-workflows/cwl_adapters/ome-converter.cwl')
    omeconverter.inpDir = filerenaming.outDir
    omeconverter.filePattern = '.*.tif'
    omeconverter.outDir = Path('omeconverter.outDir')

    montage = Step(clt_path='../image-workflows/cwl_adapters/montage.cwl')
    montage.inpDir = omeconverter.outDir
    montage.filePattern = 'x00_y03_p{p:dd}_c0.ome.tif'
    montage.layout = 'p'
    montage.outDir = Path('montage.outDir')

    image_assembler = Step(clt_path='../image-workflows/cwl_adapters/image_assembler.cwl')
    image_assembler.stitchPath = montage.outDir
    image_assembler.imgPath = omeconverter.outDir
    image_assembler.outDir = Path('image_assembler.outDir')

    # precompute_slide = Step(clt_path='../image-workflows/cwl_adapters/precompute_slide.cwl')
    # precompute_slide.inpDir = image_assembler.outDir
    # precompute_slide.pyramidType = 'Zarr'
    # precompute_slide.imageType = 'image'
    # precompute_slide.outDir = Path('precompute_slide.outDir')

    steps = [bbbcdownload,
             subdirectory,
             filerenaming,
             omeconverter,
             montage,
             image_assembler,
            #  precompute_slide
             ]
    filename = 'bbbc_py'  # .yml
    viz = Workflow(steps, filename)
    return viz


viz = workflow()
viz.compile() # Do NOT .run() here

if __name__ == '__main__':
    viz = workflow()
    viz.run()  # .run() here, inside main
