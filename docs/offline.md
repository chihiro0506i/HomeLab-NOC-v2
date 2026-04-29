# オフライン寄り運用

## 目的

このプロジェクトの配布物には Pi-hole，NetAlertX，Uptime Kuma の本体コードや Docker image を同梱していない．初回起動時に Docker が外部から取得する．

ただし，一度取得した Docker image を保存しておけば，別のラズパイへ持ち込んだり，再セットアップ時の再取得を省いたりできる．

## Docker image の保存

インターネットに接続できる状態で，次のコマンドを実行する．

```bash
./scripts/offline-export.sh
```

次のファイルが作成される．

```text
images/homelab-noc-images.tar.gz
```

このファイルは数百 MB 以上になる可能性がある．

## Docker image の読み込み

別環境や再セットアップ時に，次のコマンドを実行する．

```bash
./scripts/offline-import.sh images/homelab-noc-images.tar.gz
```

## 注意

オフライン寄りの運用では，セキュリティアップデートやブロックリストの更新が行われなくなる．更新を行わない長期運用は推奨しない．定期的にアップデート内容を確認し，バックアップを取ったうえで更新すること．
