# 参照プロジェクトとライセンス

このテンプレートは複数のOSSを組み合わせるためのプロジェクトである．各OSS本体のライセンスは，それぞれの公式リポジトリを確認すること．

```text
Pi-hole
  役割: DNS sinkhole / 広告・トラッカーブロック
  Image: pihole/pihole

Unbound
  役割: 再帰DNS resolver
  このテンプレートでは Alpine Linux 上に unbound パッケージを入れるDockerfileを用意している

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
