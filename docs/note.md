# メモ

## 概要

Raspberry Pi 5 上に Docker Compose を用いて自宅ネットワーク監視基盤を構築した．Pi-hole と Unbound によるプライバシー重視の DNS 基盤，NetAlertX による LAN 内端末検出，Uptime Kuma によるサービス死活監視を統合し，各管理画面へアクセスするための Portal 画面を自作した．

## 技術スタック

```text
Raspberry Pi 5
Raspberry Pi OS 64-bit
Docker / Docker Compose
Pi-hole
Unbound
NetAlertX
Uptime Kuma
nginx
HTML / CSS / JavaScript
Bash
DNS / LAN / HTTP / ICMP
```

## 今後の拡張案

```text
・Amazon 価格監視サービスを追加する
・天気予報や電車遅延の通知を Portal へ統合する
・研究室サーバの死活監視を Uptime Kuma へ追加する
・Tailscale で外出先から安全に管理画面へ接続する
・Grafana などで長期ログの可視化を行う
```
