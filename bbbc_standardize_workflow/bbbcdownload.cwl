class: CommandLineTool
cwlVersion: v1.2
inputs:
  name:
    inputBinding:
      prefix: --name
    type: string
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
    dockerPull: polusai/bbbc-download-plugin:0.1.0-dev1
  InitialWorkDirRequirement:
    listing:
    - entry: $(inputs.outDir)
      writable: true
  InlineJavascriptRequirement: {}
