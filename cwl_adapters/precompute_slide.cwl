#!/usr/bin/env cwl-runner
class: CommandLineTool
cwlVersion: v1.0

label: Precompute Slide

doc: |-
  This plugin generates image pyramids in multiple viewing formats.
  https://github.com/PolusAI/polus-plugins/tree/master/visualization/polus-precompute-slide-plugin

baseCommand: python3
arguments: ["-m", "polus.plugins.visualization.precompute_slide"]

requirements:
  DockerRequirement:
    dockerPull: polusai/precompute-slide-plugin:1.7.0-dev0
  # See https://www.commonwl.org/v1.0/CommandLineTool.html#InitialWorkDirRequirement
  InitialWorkDirRequirement:
    listing:
    - entry: $(inputs.outDir)
      writable: true  # Output directories must be writable
  InlineJavascriptRequirement: {}

inputs:
  inpDir:
    label: Input generic data collection to be processed by this plugin
    doc: |-
      Input generic data collection to be processed by this plugin
    type: Directory
    inputBinding:
      prefix: --inpDir

  pyramidType:
    label: Build a DeepZoom, Neuroglancer, Zarr pyramid
    doc: |-
      Build a DeepZoom, Neuroglancer, Zarr pyramid
    type: string  # enum: DeepZoom, Neuroglancer, Zarr
    inputBinding:
      prefix: --pyramidType

  imageType:
    label: Image is either Segmentation or Image
    doc: |-
      Image is either Segmentation or Image
    inputBinding:
      prefix: --imageType
    type: string

  filePattern:
    label: Filename pattern used to parse data
    doc: |-
      Filename pattern used to parse data
    type: string?
    inputBinding:
      prefix: --filePattern

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

$namespaces:
  edam: https://edamontology.org/

$schemas:
- https://raw.githubusercontent.com/edamontology/edamontology/master/EDAM_dev.owl

# 