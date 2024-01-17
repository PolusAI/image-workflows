class: CommandLineTool
cwlVersion: v1.1

label: BBBC Download

doc: |-
  Downloads the datasets on the Broad Bioimage Benchmark Collection website
  https://github.com/saketprem/polus-plugins/tree/bbbc_download/utils/bbbc-download-plugin

# See docker_remove_entrypoints.sh
baseCommand: python3
arguments: ["-m", "polus.plugins.utils.bbbc_download"]

requirements:
  DockerRequirement:
    dockerPull: polusai/bbbc-download-plugin:0.1.0-dev1
  # See https://www.commonwl.org/v1.0/CommandLineTool.html#InitialWorkDirRequirement
  InitialWorkDirRequirement:
    listing:
    - entry: $(inputs.outDir)
      writable: true  # Output directories must be writable
  InlineJavascriptRequirement: {}
  # NOTE: By default, "tools must not assume network access, except for localhost"
  # See https://www.commonwl.org/v1.1/CommandLineTool.html#NetworkAccess
  NetworkAccess:
    networkAccess: true

inputs:
  name:
    label: The name of the dataset(s) to be downloaded (separate the datasets with a comma. eg BBBC001,BBBC002,BBBC003)
    doc: |-
      The name of the dataset(s) to be downloaded (separate the datasets with a comma. eg BBBC001,BBBC002,BBBC003)
    inputBinding:
      prefix: --name
    type: string
    # default: BBBC001

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

$namespaces:
  edam: https://edamontology.org/

$schemas:
- https://raw.githubusercontent.com/edamontology/edamontology/master/EDAM_dev.owl

# manifest: "https://raw.githubusercontent.com/saketprem/polus-plugins/bbbc_download/utils/bbbc-download-plugin/plugin.json"