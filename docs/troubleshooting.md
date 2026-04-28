# トラブルシューティング

## 画面が開けない

まず状態を確認する．

```bash
./scripts/status.sh
./scripts/logs.sh
./scripts/show-urls.sh
```

ラズパイのIPアドレスが変わっている可能性があるため，次も確認する．

```bash
hostname -I
```

## 53番ポートが競合する

Pi-hole はDNS用に53番ポートを使う．既に別のDNSサービスが動いている場合，起動できないことがある．

```bash
./scripts/preflight.sh
```

systemd-resolved が競合することがあるが，いきなり停止せず，まずログを確認する．

## DNSが引けない

```bash
./scripts/check-dns.sh example.com
```

Pi-hole が起動しているか，Unbound が起動しているかを確認する．

```bash
docker compose ps
docker compose logs pihole
docker compose logs unbound
```

## NetAlertX に端末が出ない

`.env` の `HOME_SUBNET` と `LAN_INTERFACE` が自宅環境に合っているか確認する．

```bash
./scripts/detect-network.sh
```

有線LANなら `eth0`，Wi-Fiなら `wlan0` が多い．ただし環境によって異なる．

## Pi-hole を止めたらネットが使えない

端末やルータのDNSをPi-holeに向けている場合，Pi-hole停止中は名前解決できない可能性がある．端末のDNS設定を「自動」に戻すか，ルータのDNS設定を元に戻す．
