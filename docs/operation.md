# 運用手順

## 初回セットアップ

```bash
./scripts/setup.sh
nano .env
./scripts/preflight.sh
./scripts/start.sh
./scripts/show-urls.sh
```

## よく使う操作

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

バックアップには `.env` と `data/` が含まれるため，パスワードやネットワーク情報が含まれる可能性がある．GitHub には公開しないこと．

## 更新

```bash
./scripts/update.sh
```

更新前にバックアップが自動作成される．Pi-hole や NetAlertX などは更新によって挙動が変わる可能性があるため，家全体の DNS として使用している場合は慎重に行うこと．

## 停止時の注意

Pi-hole を端末の DNS として使用している場合，このプロジェクトを停止すると名前解決ができなくなる可能性がある．停止する前に，必要に応じて端末やルータの DNS 設定を「自動」に戻すこと．
