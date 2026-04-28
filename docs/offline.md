# オフライン寄り運用

## 目的

このプロジェクトのzipには，Pi-hole，NetAlertX，Uptime Kuma の本体コードやDocker imageを同梱していない．初回起動時にDockerが外部から取得する．

ただし，一度取得したDocker imageを保存しておけば，別のラズパイに持ち込んだり，再インストール時に再取得を減らしたりできる．

## Docker image の保存

インターネットに接続できる状態で，次を実行する．

```bash
./scripts/offline-export.sh
```

作成されるファイルは次である．

```text
images/homelab-noc-images.tar.gz
```

このファイルは大きくなる．数百MB以上になる可能性がある．

## Docker image の読み込み

別環境や再セットアップ時に，次を実行する．

```bash
./scripts/offline-import.sh images/homelab-noc-images.tar.gz
```

## 注意

オフライン寄りにすると，セキュリティアップデートやブロックリスト更新が止まる．完全に更新しない長期運用は推奨しない．定期的にアップデート内容を確認し，バックアップ後に更新する．
