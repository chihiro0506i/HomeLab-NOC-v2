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

## なぜ Docker Compose を使うか

複数のサービスを1台のラズパイで動かすため，サービスごとにコンテナとして分離する．Docker Compose を使うことで，起動，停止，更新，バックアップの単位をそろえやすくなる．

## なぜ Unbound を入れるか

Pi-hole だけでも広告ブロックはできる．しかし，Pi-hole の上流DNSに Google DNS や Cloudflare DNS を直接指定すると，問い合わせ履歴が特定の外部DNS事業者に集まりやすい．Unbound を使うと，Pi-hole の上流をラズパイ内の再帰DNSにできるため，外部DNS事業者への依存を減らせる．

ただし，Unbound もインターネット上のDNS階層へ問い合わせるため，完全に外部通信ゼロにはならない．

## なぜ NetAlertX は host network か

NetAlertX はLAN内端末の検出を行うため，Docker の bridge network では自宅LANを正しく観測しにくい．そのため，公式例に近い形で host network を使う．これは便利な一方，自分が管理していないネットワークでは使わないことが重要である．
