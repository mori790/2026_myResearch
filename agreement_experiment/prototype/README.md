# agent-agreement（試作 v0.1）

複数のエージェントが「どれも妥当だが両立しない選択」を先に1つに決め、その後の成果物を決定に従わせるための部品。
**スキル（エージェント側）** と **ハーネス（基盤側）** に分かれていて、片方だけでも両方でも使える。

```
agent-agreement/            ← スキル本体（Agent Skills 形式、移植可能）
  SKILL.md                  ← いつ・どう合意するかの手順
  scripts/agree.py          ← 共有の決定ログを操作するCLI
harness/
  agreement_gate.py         ← ハーネス側の強制（Claude Code のフック用）
demo_data_analysis/         ← 使用例 U2（データ分析の除外ルール）
  run_demo.sh
```

## 操作（抽象定義のインターフェースとの対応）

| 定義 | コマンド |
|---|---|
| propose(τ, d) | `agree.py propose TOPIC 'VALUE_JSON' --why ...` |
| respond(τ, accept/object) | `agree.py respond TOPIC accept` / `object --why ...` |
| commit(τ) | `agree.py commit TOPIC`（全員 accept で確定、反対があれば abort） |
| lookup(τ) | `agree.py lookup TOPIC` |
| check(o, τ) | `agree.py check TOPIC OUTPUT`（登録した検査器で Conf(o, d) を判定） |
| revise(τ) | 同じ TOPIC に `propose`（新しい版になる） |
| announce-deviation | `agree.py deviate TOPIC --why ...` |

- 決定ログは追記専用の JSONL。各行が前の行のハッシュを持つので、書き換えると `status` で `BROKEN` と出る。
- 検査器は分野ごとに差し替える（`agree.py checker TOPIC "COMMAND"`）。検査器には `$DECISION_FILE` と `$OUTPUT_PATH` が渡る。

## ハーネス側（Claude Code のフック設定例）

```json
{
  "hooks": {
    "PreToolUse": [{"matcher": "Edit|Write|MultiEdit",
      "hooks": [{"type": "command", "command": "python3 harness/agreement_gate.py pre-tool"}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "python3 harness/agreement_gate.py stop"}]}]
  }
}
```

- `pre-tool`：未確定の論点に関わるファイルへの書き込みを止める（exit 2）
- `stop`：自分の成果物が決定に従っていない、かつ逸脱の宣言もない場合、完了を止める（exit 2）
- どのファイルがどの論点に関わるかは `$AGREE_SCOPE` の JSON で指定する

## 2×2 実験での使い方

| | ハーネスなし | ハーネスあり |
|---|---|---|
| スキルなし | 何も入れない | フックとログだけ（手順は教えない） |
| スキルあり | SKILL.md と CLI だけ | 両方 |

## 未実装・既知の制限

- ログはローカルファイル。別マシンのエージェントで共有するには MCP サーバ化が必要
- 参加者全員の賛成で確定する方式のみ（多数決や期限付きは未対応）
- `pre-tool` は Edit/Write 系のみを見ている。bash で直接書き込む場合は止められない
- 決定値の妥当性（Valid_τ）の検査は未実装
