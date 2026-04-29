# セキュリティ注意事項

## 絶対に避けるべきこと

```text
・53番ポートをインターネットに公開する
・Pi-hole，NetAlertX，Uptime Kuma の管理画面をポート開放する
・初期パスワードのまま使用する
・.env，data/，backups/ を GitHub に公開する
・大学や研究室のネットワークで無許可のスキャンを行う
```

## 外出先からアクセスしたい場合

ポート開放ではなく，Tailscale や WireGuard などの VPN を使用する．VPN を使えば，外出先の端末が自宅 LAN 内に安全に接続する形になる．管理画面をインターネットへ直接公開するよりも安全である．

## NetAlertX の取り扱い

NetAlertX はネットワークスキャンに近い動作をする．自分が管理している自宅 LAN 内でのみ使用すること．大学，研究室，公共 Wi-Fi，アルバイト先などでは使用しないこと．

## GitHub 公開時の注意

公開してよいもの: README，docker-compose.yml，portal，scripts，docs，.env.example

公開してはいけないもの: .env，data，backups，images

公開前に次のコマンドを実行し，機密ファイルが含まれていないことを確認する．

```bash
git status
```

`.env` や `data/` が表示された場合は，そのまま公開してはいけない．
