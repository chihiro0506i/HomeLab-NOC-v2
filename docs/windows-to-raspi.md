# Windows から Raspberry Pi へ転送する方法

## scp を使う場合

Windows の PowerShell で次のコマンドを実行する．

```powershell
scp .\homelab-noc-v2 pi@<RaspberryPi-IP>:/home/pi/
```

ラズパイに SSH でログインする．

```powershell
ssh pi@<RaspberryPi-IP>
```

ラズパイ側でセットアップを行う．

```bash
cd homelab-noc-v2
./scripts/setup.sh
```

## USB メモリを使う場合

Windows で zip ファイルを USB メモリにコピーし，ラズパイ側で展開してもよい．ただし，初回は Docker イメージの取得にインターネット接続が必要になる．
