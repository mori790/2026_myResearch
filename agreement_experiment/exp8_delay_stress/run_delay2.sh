#!/bin/bash
cd "$(dirname "$0")"
{ for r in 1 2 3 4 5; do echo "advisory $r delay"; echo "enforced $r delay"; done; for r in 6 7 8 9 10; do echo "baseline $r delay"; done; } |
  xargs -P 3 -L 1 bash -c 'python3 run_trial.py $0 $1 --stress $2 --model haiku'
python3 evaluate.py
