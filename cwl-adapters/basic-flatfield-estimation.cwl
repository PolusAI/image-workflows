#!/usr/bin/env cwl-runner
class: CommandLineTool
cwlVersion: v1.0

label: BaSiC Flatfield Estimation

doc: |-
  This WIPP plugin will take a collection of images and use the BaSiC flatfield correction algorithm to generate a flatfield image, a darkfield image, and a photobleach offset.
  https://github.com/PolusAI/polus-plugins/tree/master/regression/basic-flatfield-estimation-plugin

requirements:
  DockerRequirement:
    dockerPull: polusai/basic-flatfield-estimation-plugin:2.1.1
  # See https://www.commonwl.org/v1.0/CommandLineTool.html#InitialWorkDirRequirement
  InitialWorkDirRequirement:
    listing:
    - entry: $(inputs.outDir)
      writable: true  # Output directories must be writable
  InlineJavascriptRequirement: {}

# "jax._src.xla_bridge - WARNING  - An NVIDIA GPU may be present on this machine, but a CUDA-enabled jaxlib is not installed. Falling back to cpu."
hints:
  cwltool:CUDARequirement:
    cudaVersionMin: "11.4"
    cudaComputeCapabilityMin: "3.0"
    cudaDeviceCountMin: 1
    cudaDeviceCountMax: 1

inputs:
  inpDir:
    label: Path to input images
    doc: |-
      Path to input images
    type: Directory
    inputBinding:
      prefix: --inpDir

  getDarkfield:
    label: If 'true', will calculate darkfield image
    doc: |-
      If 'true', will calculate darkfield image
    type: boolean?
    inputBinding:
      prefix: --getDarkfield

  # photobleach:
  #   label: If 'true', will calculate photobleach scalar
  #   doc: |-
  #     If 'true', will calculate photobleach scalar
  #   type: boolean?
  #   inputBinding:
  #     prefix: --photobleach

  filePattern:
    label: File pattern to subset data
    doc: |-
      File pattern to subset data
    type: string?
    inputBinding:
      prefix: --filePattern

  groupBy:
    label: Variables to group together
    doc: |-
      Variables to group together
    type: string?
    inputBinding:
      prefix: --groupBy

  preview:
    label: Generate a JSON file describing what the outputs should be
    doc: |-
      Generate a JSON file describing what the outputs should be
    type: boolean?
    inputBinding:
      prefix: --preview

  outDir:
    label: Output image collection
    doc: |-
      Output image collection
    type: Directory
    inputBinding:
      prefix: --outDir

outputs:
  outDir:
    label: Output image collection
    doc: |-
      Output image collection
    type: Directory
    outputBinding:
      glob: $(inputs.outDir.basename)

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
  cwltool: http://commonwl.org/cwltool#

$schemas:
- https://raw.githubusercontent.com/edamontology/edamontology/master/EDAM_dev.owl

# manifest: https://raw.githubusercontent.com/PolusAI/polus-plugins/master/regression/basic-flatfield-estimation-plugin/plugin.json