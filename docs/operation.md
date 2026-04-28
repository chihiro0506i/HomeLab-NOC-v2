# 運用手順

## 初回

```bash
./scripts/setup.sh
nano .env
./scripts/preflight.sh
./scripts/start.sh
./scripts/show-urls.sh
```

## 毎回よく使う操作

```bash
./scripts/status.sh
./scripts/logs.sh
./scripts/stop.sh
./scripts/start.sh
```

## バックアップ

```bash
./scripts/backup.sh
```

バックアップには `.env` と `data/` が含まれるため，パスワードやネットワーク情報が含まれる可能性がある．GitHubには上げない．

## 更新

```bash
./scripts/update.sh
```

更新前にバックアップが作成される．Pi-hole や NetAlertX などは更新で挙動が変わる可能性があるため，家全体のDNSとして使っている場合は慎重に行う．

## 停止時の注意

Pi-hole を端末のDNSとして使っている場合，このプロジェクトを停止すると名前解決できなくなる可能性がある．停止する前に，必要なら端末やルータのDNS設定を自動に戻す．
