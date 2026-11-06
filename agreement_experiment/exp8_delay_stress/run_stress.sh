#!/bin/bash
# usage: STRESSES="delay replace" CONDS="baseline" N=5 P=3 ./run_stress.sh
cd "$(dirname "$0")"
N=${N:-5}; P=${P:-3}; STRESSES=${STRESSES:-"delay replace"}; CONDS=${CONDS:-baseline}
for r in $(seq 1 $N); do for st in $STRESSES; do for c in $CONDS; do echo "$c $r $st"; done; done; done |
  xargs -P $P -L 1 bash -c 'python3 run_trial.py $0 $1 --stress $2 --model haiku'
python3 evaluate.py
