#!/usr/bin/env bash
cd "$(dirname "$0")"
MODEL=${MODEL:-haiku}; PAR=${PAR:-5}
jobs=()
for r in $(seq 1 10); do for c in tool inline gate ci_barrier; do jobs+=("$c $r"); done; done
for r in $(seq 6 10); do for c in base skill ci skill_ci; do jobs+=("$c $r"); done; done
printf '%s\n' "${jobs[@]}" | xargs -P "$PAR" -L 1 bash -c 'python3 run_trial.py $0 $1 --model '"$MODEL"' --max-turns 40 --timeout 900'
python3 evaluate.py
