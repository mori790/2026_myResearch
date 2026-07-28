# Day 3: KmMR

## 1. Problem

標準Kubernetesの問題は何か。
Raftで合意をとっているため、マシーンのシンプルな停止にしか対応していない。sofaware error, malicious attacksなどのByzantine行動には対応していない。

## 2. Proposed Method

KmMRは何をどのように変更したか。
標準k8sの問題をBFT-SMaRtベースでk8s環境に対応させることによりByzantineに対応できるようにし、サービスの継続性を保証した。
また、Byzantine状況下では一般的なRaftに比べ平均1000倍も短い時間で合意に至った。
## 3. Fault Model

何が故障すると仮定しているか。
Master nodeが故障すると仮定し、それぞれのnodeにBFT-SMaRtを適応している。

## 4. Evaluation

どのような実験をしたか。
DDoS攻撃はHping3コマンドを用いてByzantin的な挙動を再現した。
DDoSベースの"CPU Load", "Network Flooding"を扱った。

## 5. Main Results

どのような結果が出たか。

## 6. Possible Limitations

論文が扱っていない可能性があるものは何か。

## 7. Difference from My Study

今回の自分の実験とは何が違うか。