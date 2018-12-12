#!/usr/bin/env cwl-runner

class: CommandLineTool
id: "pubMunch-docker"
label: "pubMunch-docker tool"
cwlVersion: v1.0 
doc: |
    ![build_status](https://quay.io/repository/brca_challenge/pubmunch-brca/status)
    A Docker container for running the Literature Searching pipeline for BRCA Exchange. Documentation for PubMunch can be found at github.com/almussel/pubmunch

dct:creator:
  "@id": "almussel@ucsc.edu"
  foaf:name: Audrey Musselman-Brown
  foaf:mbox: "mailto:almussel@ucsc.edu"

requirements:
  - class: DockerRequirement
    dockerPull: "quay.io/brca_challenge/pubmunch-brca"

inputs:
  username:
    type: string
    doc: "Username for access to Synapse"
    inputBinding:
      prefix: -u
      position: 1

  password:
    type: string
    doc: "Password for access to Synapse"
    inputBinding:
      prefix: -p
      position: 2

  test:
    type: boolean
    doc: "Run the pipeline in test mode, on 20 publications"
    inputBinding:
      prefix: -t
      position: 3

outputs: []

#baseCommand: ["bash", "/opt/wrapper.sh"]
