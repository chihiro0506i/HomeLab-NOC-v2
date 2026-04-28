# Windows から Raspberry Pi へ送る方法

## scp を使う場合

Windows PowerShell で実行する．

```powershell
scp .\homelab-noc-v2 pi@<RaspberryPi-IP>:/home/pi/
```

ラズパイにSSHログインする．

```powershell
ssh pi@<RaspberryPi-IP>
```

ラズパイ側で展開する．

```bash
cd homelab-noc-v2
./scripts/setup.sh
```

## USBメモリを使う場合

WindowsでzipをUSBメモリにコピーし，ラズパイ側で展開してもよい．ただし，最終的にはラズパイ上でDockerイメージを取得するため，初回はインターネット接続が必要になる．
