from pathlib import Path

from wic.api.pythonapi import Step, Workflow

def main():
    bbbcdownload = Step(cwl_path='cwl_adapters/bbbcdownload.cwl')
    # NOTE: object fields monkey patched at runtime from *.cwl file
    bbbcdownload.name = 'BBBC001'
    bbbcdownload.outDir = Path('bbbcdownload.outDir')

    subdirectory = Step(cwl_path='../workflow-inference-compiler/cwl_adapters/subdirectory.cwl')
    subdirectory.directory = bbbcdownload.outDir
    subdirectory.glob_pattern = 'bbbcdownload.outDir/BBBC/BBBC001/raw/Images/human_ht29_colon_cancer_1_images/'
    subdirectory.subdirectory = Path('subdirectory.subdirectory')

    filerenaming = Step(cwl_path='cwl_adapters/file-renaming.cwl')
    # NOTE: FilePattern {} syntax shadows python f-string {} syntax
    filerenaming.filePattern = '.*_{row:c}{col:dd}f{f:dd}d{channel:d}.tif'
    filerenaming.inpDir = subdirectory.subdirectory
    filerenaming.outDir = Path('file-renaming.outDir')
    filerenaming.outFilePattern = 'x{row:dd}_y{col:dd}_p{f:dd}_c{channel:d}.tif'

    omeconverter = Step(cwl_path='cwl_adapters/ome-converter.cwl')
    omeconverter.inpDir = filerenaming.outDir
    omeconverter.filePattern = '.*.tif'
    omeconverter.fileExtension = '.ome.tif'
    omeconverter.outDir = Path('omeconverter.outDir')

    montage = Step(cwl_path='cwl_adapters/montage.cwl')
    montage.inpDir = omeconverter.outDir
    montage.filePattern = 'x00_y03_p{p:dd}_c0.ome.tif'
    montage.layout = 'p'
    montage.outDir = Path('montage.outDir')

    image_assembler = Step(cwl_path='cwl_adapters/image_assembler.cwl')
    image_assembler.stitchPath = montage.outDir
    image_assembler.imgPath = omeconverter.outDir
    image_assembler.outDir = Path('image_assembler.outDir')

    precompute_slide = Step(cwl_path='cwl_adapters/precompute_slide.cwl')
    precompute_slide.inpDir = image_assembler.outDir
    precompute_slide.pyramidType = 'Zarr'
    precompute_slide.imageType = 'image'
    precompute_slide.outDir = Path('precompute_slide.outDir')

    steps = [bbbcdownload,
             subdirectory,
             filerenaming,
             omeconverter,
             montage,
             image_assembler,
             precompute_slide]
    filename = 'bbbc'  # .yml
    workingdir = './'
    viz = Workflow(steps, filename, workingdir)
    viz.compile()
    viz.run()


if __name__ == '__main__':
    main()
