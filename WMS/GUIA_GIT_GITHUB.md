# Guia Rápido Git + GitHub (Jade-stock)

Objetivo: publicar seu projeto no GitHub e nunca mais ficar refém de um único PC.

## 1) Criar repositório no GitHub

No GitHub, crie `Jade-stock` com:

- `Owner`: sua conta
- `Repository name`: `Jade-stock`
- `Visibility`: Private (recomendado) ou Public
- `Add README`: Off
- `Add .gitignore`: None
- `Add license`: None

Tem que ser repositório vazio para não dar conflito no primeiro push.

## 2) Preparar local (uma vez só)

No terminal:

```bash
cd ~/meus_projetos/Jade-stock/WMS
git status
```

Se aparecer `.env` rastreado, remova só do git (sem apagar do disco):

```bash
git rm --cached .env
```

Commit de segurança:

```bash
git add .gitignore GUIA_GIT_GITHUB.md
git commit -m "chore: guia de publicacao e protecao de segredos"
```

## 3) Conectar no GitHub e subir

Troque `SEU_USUARIO` pelo seu usuário real do GitHub:

```bash
cd ~/meus_projetos/Jade-stock/WMS
git remote add origin https://github.com/SEU_USUARIO/Jade-stock.git
git branch -M main
git push -u origin main
git push origin --tags
```

## 4) Confirmar que subiu

```bash
git remote -v
git log --oneline -n 3
git tag --list
```

No GitHub, confira:

- arquivos do projeto apareceram
- tag `v1.0.0-rc1` apareceu em Releases/Tags

## 5) Rotina de backup (sempre que fechar dia)

```bash
cd ~/meus_projetos/Jade-stock/WMS
git add .
git commit -m "chore: backup diario"
git push
git push --tags
```

## 6) Se trocar de máquina

```bash
git clone https://github.com/SEU_USUARIO/Jade-stock.git
cd Jade-stock
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

Depois ajuste o `.env` com seu DSN real.

## 7) Erros comuns

`remote origin already exists`:

```bash
git remote set-url origin https://github.com/SEU_USUARIO/Jade-stock.git
```

`rejected (non-fast-forward)` no primeiro push:

- quase sempre é porque o repo remoto foi criado com README/licença.
- solução limpa: apagar repo remoto e criar vazio.

`Permission denied`:

- autentique no GitHub (token/prompt do git credential manager).

