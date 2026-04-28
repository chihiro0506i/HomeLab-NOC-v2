# セキュリティ注意事項

## 絶対に避けること

```text
・53番ポートをインターネットに公開する
・Pi-hole，NetAlertX，Uptime Kuma の管理画面をポート開放する
・初期パスワードのまま使う
・.env，data/，backups/ をGitHubに公開する
・大学や研究室のネットワークで無許可スキャンする
```

## 外出先から見たい場合

ポート開放ではなく，Tailscale や WireGuard などの VPN を使う．VPNを使うと，外出先の端末が自宅LAN内に安全に入る形になる．管理画面をインターネットへ直接さらすより安全である．

## NetAlertX の扱い

NetAlertX はネットワークスキャンに近い動作をする．自分が管理している自宅LAN内でのみ使用する．大学，研究室，公共Wi-Fi，バイト先などでは使わない．

## GitHub公開時

公開してよいものは，README，docker-compose.yml，portal，scripts，docs，.env.example である．公開してはいけないものは，.env，data，backups，images である．

公開前に次を実行する．

```bash
git status
```

`.env` や `data/` が表示されたら，公開してはいけない．
