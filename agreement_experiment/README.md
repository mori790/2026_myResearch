# エージェント間の合意：advisory と enforced の比較実験（2026年10〜11月）

複数の LLM エージェント（Claude Code, Claude Haiku）が「共有の選択」（金額の単位、関数名など、どれも正しいが両立しない選択肢）に合意し、
その合意に従って成果物を作れるかを調べる実験です。各実験フォルダに、実験プログラム、エージェントに実際に渡したプロンプト、結果を置いています。

- 10/29 の研究ミーティング：`prototype/`, `exp1_data_analysis/`, `exp2_coding/`
- 11/6 の研究ミーティング：`exp3_*` 〜 `exp8_*`

## 3つの条件

全条件に同じ合意ツール（`tools/agree.py`）を与え、ルールの与え方だけを変えています。

| 条件 | 合意ツール | ルールがプロンプトにある | 早すぎる書き込みを hook が止める |
|---|---|---|---|
| `baseline` | あり | なし | なし |
| `advisory` | あり | **あり** | なし |
| `enforced` | あり | なし（止められたときに表示） | **あり**（`harness/gate.py`, PreToolUse hook） |

ルール：「確定した決定が1つ以上あり、未決の提案がなくなるまで、自分の成果物を書かない。その後は、自分の習慣と違っても決定に従う」（`rule.py`）

## 実験の一覧と結果

数字は **成功回数 / 実行回数**（成功 = 全エージェントのファイルを組み合わせて隠しテストがすべて通る）。

| フォルダ | 内容 | baseline | advisory | enforced |
|---|---|---|---|---|
| `exp3_two_agents` | 2体、モジュール間の API を自由に決める | 5/5 | 5/5 | 4/5 |
| `exp4_incident_stopped` | 障害対応のシミュレーション（途中で中止、各2回） | — | — | — |
| `exp5_three_agents` | 3体（pricing / tax / invoice） | 5/5 | 2/5 | 4/5 |
| `exp6_conflicting_standards` | 3体 + 各エージェントに食い違うコーディング規約 + `withdraw` / `leave` | 5/5 | 5/5 | 5/5 |
| `exp7_shifts` | exp6 + エージェントが交代で作業する（`join` / `leave`） | 5/5 | 4/5 | 4/5 |
| `exp8_delay_stress` | exp6 + 通信の遅延（下の表） | 下の表 | 下の表 | 下の表 |

`exp8_delay_stress` の結果（`--stress` の値ごと）：

| stress | メッセージ板の遅延 | 決定ログの遅延 | baseline | advisory | enforced |
|---|---|---|---|---|---|
| （遅延なし = exp6） | なし | なし | 5/5 | 5/5 | 5/5 |
| `delay` | 20〜60 秒 | なし | 9/10 | 5/5 | 5/5 |
| `delay_long` | 60〜150 秒 | なし | 8/10 | 10/10 | 10/10 |
| `delay_both` | 60〜150 秒 | 60〜150 秒 | 6/10 | 10/10 | 9/10 |
| `replace` | なし（途中で agent2 を別のエージェントに交代） | なし | 5/5 | — | — |

1回あたりの平均時間（`delay_both`）：baseline 272 秒、advisory 696 秒、enforced 735 秒。
各実行の詳しい数字（テストの内訳、合意ツールの呼び出し回数、確定した話題、hook で止めた回数、費用）は各フォルダの `results.csv` にあります。

## 各実験フォルダの中身

| ファイル | 内容 |
|---|---|
| `run_trial.py` | 1回の実行。プロンプトを組み立て、エージェントを `claude -p` で並行に起動する |
| `rule.py` | advisory / enforced のルール文と判定 |
| `harness/gate.py` | enforced の hook（ルールを満たすまで成果物への書き込みを止める） |
| `tools/agree.py` | 合意ツール（propose / respond / commit / lookup / status / withdraw / leave など） |
| `tools/msg.py` | メッセージ板（exp8 では遅延つき） |
| `repo1/`〜`repo3/` | 各エージェントに配るリポジトリの雛形（データは担当エージェントだけが持つ） |
| `eval/` | 隠しテスト（`reference.py` が正解、`run_hidden.py` が組み合わせて実行） |
| `evaluate.py` | 全実行を採点して `results.csv` を作る |
| `run_*.sh` | まとめて実行するスクリプト |
| `results.csv` | 採点結果 |
| `runs/` | 各実行の記録（下の表） |

`runs/<条件>_r<番号>/` の中身：

| ファイル | 内容 |
|---|---|
| `agentN/prompt.txt` | **そのエージェントに実際に渡したプロンプト** |
| `agentN/repo/*.py` | 実行終了時点のエージェントのリポジトリ内の .py ファイル（自分の成果物と、他人のモジュールの仮置き） |
| `agentN/result.json` | 終了状態、ターン数、時間、費用、最後の応答 |
| `agentN/settings.json` | そのエージェントの Claude Code 設定（enforced では hook の定義） |
| `shared/messages.jsonl` | メッセージ板のやり取り（exp8 では `deliver_at` = 相手に届いた時刻） |
| `shared/agreement_log.jsonl` | 決定ログ（提案・投票・確定。exp8 の `delay_both` では `visible_at` = 他人に見えた時刻） |
| `shared/harness_events.jsonl` | enforced の hook が書き込みを止めた記録 |
| `trial.json` | 条件、モデル、全体の時間 |

## 含めていないもの

- エージェントの全行動の記録（`stream.jsonl`、合計約340MB）と `stderr.txt`。容量が大きく、実行環境の設定情報も含むため除いています。
- 実行時のログ（`*.log`）。

## 既知の問題

- enforced ではルールの文章が「書き込みを止められたとき」にしか見えないため、advisory との比較に「ルールが見えるか」の違いが混ざっています（次回の実験で修正予定）。
- exp5〜exp8 の agent3 のプロンプトで、注文の例が `{{"customer": ...}}` と波括弧が二重に表示されています（文字列整形の誤り）。正しくは `{"customer": ...}` です。
- タスクは自作で、各条件 5〜10 回、モデルは Claude Haiku のみです。

## 実行に必要なもの

- Python 3
- Claude Code（`claude -p` の非対話モード）。実行すると Claude の利用枠を消費します。
- 例：`cd exp8_delay_stress && python3 run_trial.py advisory 1 --stress delay_both`
  （`run_trial.py` は自分のフォルダの `runs/` に結果を書きます。パスはこの実験を行った環境（`/home/claude/exp8` など）のものが記録に残っています）
