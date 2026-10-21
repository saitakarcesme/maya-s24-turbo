#!/bin/sh
# run a command in the CUDA build/run container, as isa, repo + data mounted at the same paths
NAME=${CTR_NAME:-maya-run}
exec docker run --rm --name "$NAME" --gpus all --network host --ipc host \
  --ulimit memlock=-1 --ulimit nofile=65536 --cap-add SYS_NICE \
  --user 1000:1000 -e HOME=/home/USER -e USER=isa \
  -v /home/USER:/home/USER -w /home/USER/maya-bench/project-maya \
  --entrypoint "" ${CTR_EXTRA} \
  ghcr.io/0xsero/glm53-flash-offload@sha256:82eef823f95b89fcb14b8379d45315d3a632aaa054fb04e3418b62a3ec2ff1ff "$@"
