# Guia de Deploy - Invexa no Render.com

Este guia passo a passo ajudará você a colocar o Invexa no ar usando o Render.com com banco de dados PostgreSQL.

## 1. Preparação (Já Feito ✅)
- [x] Arquivo `Dockerfile` criado (Python 3.11).
- [x] `requirements.txt` atualizado com driver PostgreSQL (`psycopg2-binary`).
- [x] Configuração do App (`config.py`) ajustada para ler variáveis do Render.

## 2. GitHub (Seu Código)
O Render precisa pegar o código do GitHub.
1. Crie um novo repositório no GitHub (ex: `invexa-app`).
2. Suba o código do seu PC para lá:
   ```bash
   git init
   git add .
   git commit -m "Primeiro deploy"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/invexa-app.git
   git push -u origin main
   ```

## 3. Criar Banco de Dados (Render)
1. Crie uma conta no [dashboard.render.com](https://dashboard.render.com).
2. Clique em **New +** -> **PostgreSQL**.
3. **Name:** `invexa-db`
4. **Database:** `invexa`
5. **User:** `invexa_user`
6. **Region:** `Ohio (US East)` (Ou a mais barata/próxima).
7. **Instance Type:** Escolha **Starter** ($7/mês) ou **Free** (tem limitações de 30 dias).
8. Clique em **Create Database**.
9. **IMPORTANTE:** Quando criar, copie a **"Internal Database URL"** (começa com `postgres://...`). Vamos usar logo mais.

## 4. Criar o Site (Web Service)
1. No dashboard, clique em **New +** -> **Web Service**.
2. Conecte seu GitHub e escolha o repositório `invexa-app`.
3. **Name:** `invexa-app`
4. **Region:** Mesma do banco de dados (`Ohio`).
5. **Branch:** `main`
6. **Runtime:** `Docker`.
7. **Instance Type:** `Starter` ($7/mês).
8. **Environment Variables** (A parte mais importante!):
   Clique em "Add Environment Variable" e adicione:
   
   | Key | Value |
   | --- | --- |
   | `DATABASE_URL` | Cole a **Internal Database URL** que você copiou do banco. |
   | `SECRET_KEY` | Crie uma senha longa e aleatória (ex: `s3cr3t_invexa_prod_123`). |
   | `MP_ACCESS_TOKEN` | Seu token de produção do Mercado Pago. |
   
9. Clique em **Create Web Service**.

## Opção Alternativa: Blueprint (Mais Fácil)
Como adicionei o arquivo `render.yaml`, você pode:
1. No Render, vá em **Blueprints** -> **New Blueprint Instance**.
2. Conecte seu repositório.
3. O Render vai detectar o `render.yaml` e criar o Banco e o Site automaticamente para você.
4. Você só precisará preencher o `MP_ACCESS_TOKEN`.


## 5. Primeiro Acesso
O Render vai começar o "Build". Pode demorar uns 5-10 minutos na primeira vez.
Acompanhe os "Logs". Quando aparecer `Application startup complete`, seu site estará no ar em:
`https://invexa-app.onrender.com`

Se precisar rodar as migrações (criar tabelas), o Invexa já faz isso automaticamente ao iniciar (`run.bat` local ou `app/main.py` no servidor), então deve funcionar de primeira!
