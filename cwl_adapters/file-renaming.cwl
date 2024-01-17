class: CommandLineTool
cwlVersion: v1.0

label: File Renaming

doc: |-
  Rename and store image collection files in a new image collection
  https://github.com/PolusAI/polus-plugins/tree/master/formats/file-renaming-plugin

# See docker_remove_entrypoints.sh
baseCommand: python3
arguments: ["-m", "polus.plugins.formats.file_renaming"]

requirements:
  DockerRequirement:
    dockerPull: polusai/file-renaming-plugin:0.2.1-dev0  # NOTE: 0.2.3 not pushed yet
  # See https://www.commonwl.org/v1.0/CommandLineTool.html#InitialWorkDirRequirement
  InitialWorkDirRequirement:
    listing:
    - entry: $(inputs.outDir)
      writable: true  # Output directories must be writable
  InlineJavascriptRequirement: {}

inputs:
  inpDir:
    inputBinding:
      prefix: --inpDir
    type: Directory

  filePattern:
    inputBinding:
      prefix: --filePattern
    type: string

  mapDirectory:
    inputBinding:
      prefix: --mapDirectory
    type: string?  # enum: raw, map, default

  preview:
    label: Generate a JSON file describing what the outputs should be
    doc: |-
      Generate a JSON file describing what the outputs should be
    inputBinding:
      prefix: --preview
    type: boolean?

  outFilePattern:
    inputBinding:
      prefix: --outFilePattern
    type: string

  outDir:
    label: Output collection
    doc: |-
      Output collection
    inputBinding:
      prefix: --outDir
    type: Directory

outputs:
  outDir:
    label: Output collection
    doc: |-
      Output collection
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

$schemas:
- https://raw.githubusercontent.com/edamontology/edamontology/master/EDAM_dev.owl

# manifest: https://raw.githubusercontent.com/PolusAI/polus-plugins/master/formats/file-renaming-plugin/plugin.json