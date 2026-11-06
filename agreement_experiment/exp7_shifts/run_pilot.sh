#!/bin/bash
cd "$(dirname "$0")"
N=${N:-5}; P=${P:-3}
for r in $(seq 1 $N); do for c in baseline advisory enforced; do echo "$c $r"; done; done |
  xargs -P $P -L 1 bash -c 'python3 run_trial.py $0 $1 --model haiku'
python3 evaluate.py
