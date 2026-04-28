# メモ

## 短い説明

Raspberry Pi 5 上に，Docker Compose を用いて自宅ネットワーク監視基盤を構築した．Pi-hole と Unbound によるプライバシー重視のDNS基盤，NetAlertX によるLAN内端末検出，Uptime Kuma によるサービス死活監視を統合し，各管理画面へアクセスするための Portal 画面を自作した．

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
・Amazon価格監視サービスを追加する
・天気予報や電車遅延通知をPortalへ統合する
・研究室サーバの死活監視をUptime Kumaへ追加する
・Tailscaleで外出先から安全に管理画面へ接続する
・Grafanaなどで長期ログ可視化を行う
```
