# GitHub公開手順

## 公開前チェック

```bash
git status
```

次のファイルやフォルダが表示されていたら，公開してはいけない．

```text
.env
data/
backups/
images/
```

## 初回公開例

```bash
git init
git add README.md docker-compose.yml .env.example .gitignore LICENSE portal services configs scripts docs
git commit -m "Initial homelab-noc project"
git branch -M main
git remote add origin https://github.com/<your-name>/homelab-noc-v2.git
git push -u origin main
```

## LICENSE の変更

`LICENSE` の `YOUR_NAME` は，自分の名前またはGitHubハンドルに変更する．
