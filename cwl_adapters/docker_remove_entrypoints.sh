#! /bin/bash -e

# This script will remove / overwrite the entrypoints in the following docker images.

# The reason is that we want to simultaneously allow
# 1. release environments, where users will simply run code in a docker image and
# 2. dev/test environments, where developers can run the latest code on the host machine and/or in the CI.

# With entrypoints, there is no easy way to switch between 1 and 2; developers will
# have to manually prepend the entrypoint string to the baseCommand, and/or possibly
# modify paths to be w.r.t. their host machine instead of w.r.t. the image. (/opt/.../main.py)

# Without entrypoints, to switch between 1 and 2, simply comment out DockerRequirement ... that's it!

images=(
    polusai/bbbc-download-plugin:0.1.0-dev1
    polusai/file-renaming-plugin:0.2.1-dev0  # NOTE: 0.2.3 not pushed yet
    polusai/ome-converter-plugin:0.3.0
    polusai/montage-plugin:0.5.0
    polusai/image-assembler-plugin:1.4.0-dev0
    polusai/precompute-slide-plugin:1.7.0-dev0
)

for image in ${images[@]}; do
  echo "FROM ${image}" > Dockerfile_tmp
  echo "ENTRYPOINT []" >> Dockerfile_tmp
  sudo docker build -f Dockerfile_tmp -t ${image} .
  rm Dockerfile_tmp
done