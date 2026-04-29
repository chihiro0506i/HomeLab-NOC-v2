# アーキテクチャ

## 全体像

```text
[PC / iPhone / iPad]
        |
        | DNS問い合わせ
        v
[Pi-hole container] ----> [Unbound container] ----> DNS階層
        |
        | Web UI
        v
[Portal]

[NetAlertX]   : host networkで自宅LANを観測
[Uptime Kuma] : HTTP/Ping監視
```

## Docker Compose を使う理由

複数のサービスを 1 台のラズパイで動かすため，サービスごとにコンテナとして分離する．Docker Compose を使うことで，起動・停止・更新・バックアップの管理単位をそろえやすくなる．

## Unbound を導入する理由

Pi-hole だけでも広告ブロックは可能である．しかし，Pi-hole の上流 DNS に Google DNS や Cloudflare DNS を直接指定すると，問い合わせ履歴が特定の外部 DNS 事業者に集中しやすい．Unbound を使えば，Pi-hole の上流をラズパイ内の再帰 DNS にでき，外部 DNS 事業者への依存を軽減できる．

ただし，Unbound もインターネット上の DNS 階層へ問い合わせを行うため，外部通信が完全にゼロになるわけではない．

## NetAlertX に host network を使う理由

NetAlertX は LAN 内端末の検出を行うため，Docker の bridge network では自宅 LAN を正しく観測しにくい．そのため，公式の推奨に近い形で host network を使用する．これは便利な反面，自分が管理していないネットワークでは使わないことが重要である．
