# 参照プロジェクトとライセンス

このテンプレートは複数の OSS を組み合わせて使うためのプロジェクトである．各 OSS 本体のライセンスについては，それぞれの公式リポジトリを参照すること．

```text
Pi-hole
  役割: DNS sinkhole / 広告・トラッカーブロック
  Image: pihole/pihole

Unbound
  役割: 再帰DNS resolver
  このテンプレートでは Alpine Linux 上に unbound パッケージを導入する Dockerfile を用意している

NetAlertX
  役割: LAN内端末検出・ネットワーク可視化
  Image: ghcr.io/netalertx/netalertx

Uptime Kuma
  役割: セルフホスト型死活監視
  Image: louislam/uptime-kuma

nginx
  役割: Portal の静的ファイル配信
  Image: nginx:alpine
```

このテンプレート自体は MIT License としている．
