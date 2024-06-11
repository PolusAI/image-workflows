#!/usr/bin/env cwl-runner
class: CommandLineTool
cwlVersion: v1.0

label: Image Assembler

doc: |-
  This plugin assembles images into a stitched image using an image stitching vector.
  https://github.com/PolusAI/polus-plugins/tree/master/transforms/images/image-assembler-plugin

requirements:
  DockerRequirement:
    dockerPull: polusai/image-assembler-plugin:1.4.0-dev0
  # See https://www.commonwl.org/v1.0/CommandLineTool.html#InitialWorkDirRequirement
  InitialWorkDirRequirement:
    listing:
    - $(inputs.stitchPath)  # Must stage inputs for tools which do not accept full paths.
    - entry: $(inputs.outDir)
      writable: true  # Output directories must be writable
  InlineJavascriptRequirement: {}

inputs:
  stitchPath:
    label: Path to directory containing "stitching vector" file img-global-positions-0.txt
    doc: |-
      Path to directory containing "stitching vector" file img-global-positions-0.txt
    type: Directory
    inputBinding:
      prefix: --stitchPath

  imgPath:
    label: Path to input image collection
    doc: |-
      Path to input image collection
    type: Directory
    inputBinding:
      prefix: --imgPath

  timesliceNaming:
    label: Label images by timeslice rather than analyzing input image names
    doc: |-
      Label images by timeslice rather than analyzing input image names
    inputBinding:
      prefix: --timesliceNaming
    type: boolean?

  preview:
    label: Generate a JSON file describing what the outputs should be
    doc: |-
      Generate a JSON file describing what the outputs should be
    type: boolean?
    inputBinding:
      prefix: --preview

  outDir:
    label: Output collection
    doc: |-
      Output collection
    type: Directory
    inputBinding:
      prefix: --outDir

outputs:
  outDir:
    label: Output collection
    doc: |-
      Output collection
    type: Directory
    outputBinding:
      glob: $(inputs.outDir.basename)

  assembled_image:
    label: The assembled montage image
    doc: |-
      JSON file with outputs
    type: File?  # if not --preview
    # See https://bioportal.bioontology.org/ontologies/EDAM?p=classes&conceptid=format_3727
    format: edam:format_3727
    outputBinding:
      glob: "*.ome.tif"

  preview_json:
    label: JSON file with outputs
    doc: |-
      JSON file with outputs
    type: File?  # if --preview
    format: edam:format_3464
    outputBinding:
      glob: preview.json

$namespaces:
  edam: https://edamontology.org/

$schemas:
- https://raw.githubusercontent.com/edamontology/edamontology/master/EDAM_dev.owl

# manifest: https://raw.githubusercontent.com/PolusAI/polus-plugins/master/transforms/images/image-assembler-plugin/plugin.json