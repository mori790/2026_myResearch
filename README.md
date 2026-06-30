# Research Presentation Archive

このリポジトリでは、研究室発表・輪講・進捗報告などで使用したスライド資料を管理します。

## Purpose of This Repository

このリポジトリの目的は、研究活動に関する発表資料をGitHub上で管理し、研究の過程を継続的に記録することです。

具体的には、以下を目的としています。

* 研究室発表スライドの履歴を残す
* 過去の発表内容を振り返りやすくする
* 研究の進捗を整理する
* 論文輪講や技術調査の内容を蓄積する
* スライド作成時のテンプレートや図を再利用しやすくする
* 自分の研究テーマの変遷を追跡できるようにする
  
## About My Research

私は、分散システムおよび分散アルゴリズムに関心を持っています。

特に、複数のノードがネットワークを介して協調するシステムにおいて、障害やメッセージ遅延、不完全な情報が存在する状況でも、システム全体として正しく動作するための仕組みに興味があります。

現在は、分散システムにおける合意形成、耐障害性、メッセージ伝播、ノード間通信などを中心に学習・研究を進めています。

## Research Interests

主な関心分野は以下の通りです。

* Distributed Systems
* Distributed Algorithms
* Fault Tolerance
* Consensus Algorithms
* Message Passing
* Network Reliability
* Large-Scale Systems
* System Security


## Files in Each Presentation Directory

各発表ディレクトリには、必要に応じて以下のファイルを配置します。

```text
main.tex        # LaTeX / Beamer のソースファイル
slides.pdf      # 発表用PDF
script.md        # 発表メモ・補足説明
figures/        # 図・画像・スクリーンショット
references.bib  # 参考文献
```

## How to Build Slides

LaTeX / Beamer を使用する場合は、各発表ディレクトリ内で以下を実行します。

```bash
latexmk -pdf main.tex
```

または、Overleafで編集した `.tex` ファイルや出力したPDFをこのリポジトリに保存します。

## Notes on Confidentiality

研究内容や未公開情報を含む可能性があるため、公開範囲には注意します。

以下のような情報を含む場合は、private repositoryとして管理します。

* 未公開の研究アイデア
* 投稿前の論文内容
* 共同研究に関する情報
* 研究室内限定の資料
* 外部公開できないデータ
* 個人情報や内部資料

## Future Plans

今後、以下の内容を追加していく予定です。

* Beamerテンプレート
* 研究進捗報告用テンプレート
* 論文輪講用テンプレート
* 図表作成用スクリプト
* 参考文献管理
* PDF自動生成用GitHub Actions
* 研究テーマごとのまとめ資料

## License

このリポジトリ内の資料は、個人の研究活動および研究室内での利用を想定しています。
外部公開・再利用については、資料の内容に応じて個別に判断します。
