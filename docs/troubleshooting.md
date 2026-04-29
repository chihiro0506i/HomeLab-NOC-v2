# トラブルシューティング

## 画面が開けない

まずサービスの状態を確認する．

```bash
./scripts/status.sh
./scripts/logs.sh
./scripts/show-urls.sh
```

ラズパイの IP アドレスが変わっている可能性があるため，次のコマンドでも確認する．

```bash
hostname -I
```

## 53 番ポートが競合する

Pi-hole は DNS 用に 53 番ポートを使用する．すでに別の DNS サービスが動作している場合，起動できないことがある．

```bash
./scripts/preflight.sh
```

systemd-resolved が競合する場合があるが，いきなり停止せず，まずログを確認すること．

## DNS が引けない

```bash
./scripts/check-dns.sh example.com
```

Pi-hole と Unbound がそれぞれ起動しているかを確認する．

```bash
docker compose ps
docker compose logs pihole
docker compose logs unbound
```

## NetAlertX に端末が表示されない

`.env` の `HOME_SUBNET` と `LAN_INTERFACE` が自宅環境に合っているか確認する．

```bash
./scripts/detect-network.sh
```

有線 LAN の場合は `eth0`，Wi-Fi の場合は `wlan0` であることが多い．ただし環境によって異なる．

## Pi-hole を停止したらインターネットが使えない

端末やルータの DNS を Pi-hole に向けている場合，Pi-hole の停止中は名前解決ができなくなる可能性がある．端末の DNS 設定を「自動」に戻すか，ルータの DNS 設定を元に戻すこと．
