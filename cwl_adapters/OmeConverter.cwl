class: CommandLineTool
cwlVersion: v1.2
inputs:
  fileExtension:
    inputBinding:
      prefix: --fileExtension
    type: string
  filePattern:
    inputBinding:
      prefix: --filePattern
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
    dockerPull: polusai/ome-converter-tool:0.3.2
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