# 🚀 GUIA: Subindo o App no Streamlit Cloud

## O que você vai precisar
- Conta no GitHub (gratuita): https://github.com
- Conta no Streamlit Cloud (gratuita): https://streamlit.io/cloud

---

## PASSO 1 — Preparar os arquivos

Coloque estes 3 arquivos em uma pasta no seu computador:
- `app.py`
- `requirements.txt`
- `credenciais.json` ← o mesmo que já usa hoje

---

## PASSO 2 — Subir no GitHub

1. Entre em https://github.com e crie um repositório novo
   - Nome sugerido: `sistema-agendamento`
   - Marque como **Privado** (para segurança)
2. Faça upload dos 3 arquivos para o repositório

> ⚠️ IMPORTANTE: O `credenciais.json` NÃO deve ficar público.
> Para produção, use o sistema de Secrets do Streamlit (explicado abaixo).

---

## PASSO 3 — Conectar no Streamlit Cloud

1. Entre em https://streamlit.io/cloud
2. Clique em **"New app"**
3. Conecte sua conta do GitHub
4. Selecione o repositório `sistema-agendamento`
5. Em "Main file path" coloque: `app.py`
6. Clique em **Deploy**

---

## PASSO 4 — Configurar as credenciais com segurança (Secrets)

Em vez de subir o `credenciais.json` no GitHub, use o sistema de Secrets:

1. No painel do Streamlit Cloud, clique em **Settings > Secrets**
2. Cole o conteúdo do seu `credenciais.json` assim:

```toml
[gcp_service_account]
type = "service_account"
project_id = "seu_project_id"
private_key_id = "sua_key_id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n..."
client_email = "seu@email.iam.gserviceaccount.com"
client_id = "123456"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

> Os valores acima estão no seu arquivo `credenciais.json` atual.

---

## PASSO 5 — Imagem de fundo

Para a imagem de fundo funcionar na nuvem:
1. Adicione o arquivo `fundo_logistica.png` ao repositório GitHub
2. No `app.py`, mude a linha do caminho para:
   ```python
   CAMINHO_FUNDO = "fundo_logistica.png"
   ```

---

## Resultado final

Seu app ficará disponível em um link como:
`https://sistema-agendamento-seuusuario.streamlit.app`

- ✅ Funciona 24h sem precisar do seu PC ligado
- ✅ Abre no celular, tablet, qualquer navegador
- ✅ Login com filial + email + senha igual ao atual
- ✅ Conectado ao mesmo Google Sheets de hoje

---

## Comandos para testar localmente antes de subir

```bash
pip install streamlit gspread oauth2client pandas openpyxl Pillow
streamlit run app.py
```
