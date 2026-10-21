#!/bin/sh
# usage: runbench.sh LABEL  -> official --bench with current config, logs saved under logs/
L=$1; cd ~/maya-bench
CTR_NAME=maya-bench ./ctr.sh ./maya.sh --plain --bench > logs/bench-$L.log 2>&1
cp project-maya/maya-bench.log logs/engine-$L.log
cp project-maya/maya-maya-s24.json logs/config-$L.json
echo "BENCHDONE $L"; grep -E "tokens/s" logs/bench-$L.log | tail -6
