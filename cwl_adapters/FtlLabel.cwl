class: CommandLineTool
cwlVersion: v1.2
inputs:
  binarizationThreshold:
    inputBinding:
      prefix: --binarizationThreshold
    type: double
  connectivity:
    inputBinding:
      prefix: --connectivity
    type: string
  inpDir:
    inputBinding:
      prefix: --inpDir
    type: Directory
  outDir:
    inputBinding:
      prefix: --outDir
    type: Directory
outputs:
  outDir:
    outputBinding:
      glob: $(inputs.outDir.basename)
    type: Directory
requirements:
  DockerRequirement:
    dockerPull: polusai/ftl-label-plugin:0.3.12-dev5
  EnvVarRequirement:
    envDef:
      HOME: /home/polusai
  InitialWorkDirRequirement:
    listing:
    - entry: $(inputs.outDir)
      writable: true
  InlineJavascriptRequirement: {}
  NetworkAccess:
    networkAccess: true
