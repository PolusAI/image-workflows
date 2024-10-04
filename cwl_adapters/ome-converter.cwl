#!/usr/bin/env cwl-runner
class: CommandLineTool
cwlVersion: v1.0

label: OME Zarr Converter

doc: |-
  This WIPP plugin converts BioFormats supported data types to the OME Zarr file format.
  https://github.com/PolusAI/polus-plugins/tree/master/formats/ome-converter-plugin

requirements:
  DockerRequirement:
    dockerPull: sameeul/ome-converter-tool:0.3.3-dev0
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

  filePattern:
    label: A filepattern, used to select data for conversion
    doc: |-
      A filepattern, used to select data for conversion
    type: string
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

# manifest: https://raw.githubusercontent.com/PolusAI/polus-plugins/master/formats/ome-converter-plugin/plugin.json
