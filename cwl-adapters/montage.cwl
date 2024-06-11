#!/usr/bin/env cwl-runner
class: CommandLineTool
cwlVersion: v1.0

label: Montage

doc: |-
  This plugin generates a stitching vector that will montage images together.
  https://github.com/PolusAI/polus-plugins/tree/master/transforms/images/montage-plugin

requirements:
  DockerRequirement:
    dockerPull: polusai/montage-plugin:0.5.0
  # See https://www.commonwl.org/v1.0/CommandLineTool.html#InitialWorkDirRequirement
  InitialWorkDirRequirement:
    listing:
    - entry: $(inputs.outDir)
      writable: true  # Output directories must be writable
  InlineJavascriptRequirement: {}

inputs:
  inpDir:
    label: Input image collection to be processed by this plugin
    doc: |-
      Input image collection to be processed by this plugin
    type: Directory
    inputBinding:
      prefix: --inpDir

  filePattern:
    label: Filename pattern used to parse data
    doc: |-
      Filename pattern used to parse data
    type: string
    inputBinding:
      prefix: --filePattern

  layout:
    label: Specify montage organization
    doc: |-
      Specify montage organization
    type: string?
    # optional array of strings?
    inputBinding:
      prefix: --layout

  gridSpacing:
    label: Specify spacing between images in the lowest grid
    doc: |-
      Specify spacing between images in the lowest grid
    inputBinding:
      prefix: --gridSpacing
    type: int?

  imageSpacing:
    label: Specify spacing multiplier between grids
    doc: |-
      Specify spacing multiplier between grids
    inputBinding:
      prefix: --imageSpacing
    type: int?

  flipAxis:
    label: Axes to flip when laying out images
    doc: |-
      Axes to flip when laying out images
    inputBinding:
      prefix: --flipAxis
    type: string?

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

  global_positions:
    label: The "stitching vector", i.e. the positions of the individual images in the montage
    doc: |-
      The "stitching vector", i.e. the positions of the individual images in the montage
    type: File?  # if not --preview
    outputBinding:
      glob: $(inputs.outDir.basename)/img-global-positions-0.txt

  preview_json:
    label: JSON file describing what the outputs should be
    doc: |-
      JSON file describing what the outputs should be
    type: File?  # if --preview
    format: edam:format_3464
    outputBinding:
      glob: preview.json

$namespaces:
  edam: https://edamontology.org/

$schemas:
- https://raw.githubusercontent.com/edamontology/edamontology/master/EDAM_dev.owl

# manifest: https://raw.githubusercontent.com/PolusAI/polus-plugins/master/transforms/images/montage-plugin/plugin.json