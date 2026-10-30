#!/usr/bin/env bash
# Demo: two analysis agents share an outlier rule (use case U2).
set -u
cd "$(dirname "$0")"
A="python3 ../agent-agreement/scripts/agree.py"
G="python3 ../harness/agreement_gate.py"
export AGREE_LOG=$PWD/log.jsonl AGREE_SCOPE=$PWD/scope.json
rm -f log.jsonl ch1.json ch2.json
cat > scope.json <<J
{"agent1": {"ch1.json": ["data.outlier_rule"]},
 "agent2": {"ch2.json": ["data.outlier_rule"]}}
J

echo "== (a) WITHOUT agreement: each agent picks its own valid rule"
python3 analysis.py '{"method":"sd","k":3}'    ch1.json
python3 analysis.py '{"method":"iqr","k":1.5}' ch2.json
echo

echo "== (b) WITH agreement skill"
AGENT_ID=agent1 $A init --participants agent1,agent2
echo "-- harness: agent1 tries to write ch1.json before commit"
echo '{"tool_name":"Write","tool_input":{"file_path":"ch1.json"}}' | AGENT_ID=agent1 $G pre-tool; echo "   exit=$?"
AGENT_ID=agent1 $A propose data.outlier_rule '{"method":"sd","k":3}' --why "common default"
AGENT_ID=agent2 $A respond data.outlier_rule object --why "RT is skewed; prefer IQR"
AGENT_ID=agent1 $A commit  data.outlier_rule
AGENT_ID=agent2 $A propose data.outlier_rule '{"method":"iqr","k":1.5}' --why "robust to skew"
AGENT_ID=agent1 $A respond data.outlier_rule accept
AGENT_ID=agent1 $A commit  data.outlier_rule
$A checker data.outlier_rule "python3 $PWD/check_exclusion.py"
echo "-- harness: agent1 tries again after commit"
echo '{"tool_name":"Write","tool_input":{"file_path":"ch1.json"}}' | AGENT_ID=agent1 $G pre-tool; echo "   exit=$?"
echo

echo "-- agent1 follows the decision; agent2 silently keeps its old habit (3SD)"
python3 analysis.py "$(AGENT_ID=agent1 $A lookup data.outlier_rule | python3 -c 'import json,sys;print(json.dumps(json.load(sys.stdin)["value"]))')" ch1.json
python3 analysis.py '{"method":"sd","k":3}' ch2.json
echo "-- harness: stop-time conformance check"
echo '{}' | AGENT_ID=agent1 $G stop; echo "   agent1 exit=$?"
echo '{}' | AGENT_ID=agent2 $G stop; echo "   agent2 exit=$?"
echo
$A status
