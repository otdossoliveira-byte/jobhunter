# JobHunter 🔎

Robô de monitoramento de vagas de emprego **para qualquer cargo, em
qualquer cidade** — você escolhe o que buscar, ele avisa quando algo
novo aparecer. Persistência em banco de dados e alertas automáticos
no Telegram.

Desenvolvido por **Otávio dos Santos Oliveira**.

## Arquitetura

```
JobHunter/
├── main.py                      # Orquestra tudo (ponto de entrada)
├── requirements.txt
├── .env.example                 # Modelo de variáveis de ambiente
├── LICENSE
├── config/
│   └── settings.py              # Config geral (banco, Telegram, comportamento)
├── perfis/
│   └── perfil_manager.py        # Menu interativo + perfis de busca salvos
├── database/
│   ├── models.py                # Modelo ORM (tabela `vagas`)
│   └── db.py                    # Engine, sessão e funções de CRUD
├── scrapers/
│   ├── base_scraper.py          # Contrato Strategy/Adapter + anti-bloqueio
│   ├── gupy_scraper.py          # Adapter para o portal Gupy
│   └── vagas_scraper.py         # Adapter para o portal Vagas.com
└── notifications/
    └── telegram_notifier.py     # Envio de alertas via Telegram Bot API
```

Cada site de vagas é um **Adapter** que implementa o mesmo contrato
(`BaseScraper.buscar_vagas()`), seguindo o padrão **Strategy**. Para
adicionar LinkedIn, Indeed ou qualquer outro site no futuro:

1. Crie `scrapers/linkedin_scraper.py` herdando de `BaseScraper`.
2. Implemente apenas o método `_extrair_vagas`.
3. Adicione a classe na lista `SCRAPERS_DISPONIVEIS` em `main.py`.

Nenhum outro arquivo precisa ser alterado.

## Como funciona a busca personalizada

Ao rodar `python main.py`, você escolhe:

- Rodar todos os **perfis de busca** já salvos (ex: "Admin em Salvador",
  "Dev Júnior em São Paulo")
- Criar um novo perfil (cargo + cidade, separados por vírgula se
  quiser mais de um)
- Fazer uma **busca avulsa**, sem salvar nada
- Rodar só perfis específicos da lista

Deixar a cidade em branco (ou digitar "qualquer") remove o filtro de
cidade — a vaga passa a ser aceita em qualquer lugar do Brasil.

Os perfis ficam salvos em `perfis/perfis.json` (não vai para o Git —
pode conter suas buscas pessoais).

---

## Passo a passo para rodar do zero

### 1. Pré-requisitos
- Python 3.10 ou superior instalado.
- Terminal (PowerShell, cmd, ou bash/zsh no Mac/Linux).

### 2. Baixe o projeto e entre na pasta
```bash
cd JobHunter
```

### 3. Crie e ative um ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Instale as dependências
```bash
pip install -r requirements.txt
```

### 5. Instale os navegadores do Playwright
```bash
playwright install chromium
```

### 6. Crie o Bot do Telegram (para receber os alertas)
1. No Telegram, procure por **@BotFather** e inicie uma conversa.
2. Envie `/newbot` e siga as instruções.
3. Guarde o **token** que ele te der.
4. Pegue seu **Chat ID**: envie qualquer mensagem para o seu bot,
   depois acesse (trocando `SEU_TOKEN`):
   `https://api.telegram.org/botSEU_TOKEN/getUpdates`
   e procure `"chat":{"id": ...}`. Ou use o bot **@userinfobot**.

### 7. Configure o arquivo `.env`
```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```
Preencha `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`. O resto já vem
com valores padrão sensatos.

⚠️ **Nunca** suba o `.env` para o GitHub — já está no `.gitignore`.

### 8. Rode o JobHunter
```bash
python main.py
```
Na primeira execução, você vai criar seu primeiro perfil de busca
respondendo às perguntas no terminal. Nas próximas vezes, o menu
mostra os perfis salvos.

### 9. Automatizar a execução periódica (opcional)
- **Windows:** Agendador de Tarefas.
- **Mac/Linux:** `crontab -e`, por exemplo a cada 3 horas:
  ```
  0 */3 * * * cd /caminho/completo/para/JobHunter && venv/bin/python main.py
  ```
  (rodar automaticamente sem perguntas no terminal exige adaptar o
  `main.py` para ler um perfil fixo em vez do menu interativo)

---

## Observações importantes

- **Seletores CSS podem quebrar**: sites como Gupy e Vagas.com mudam o
  layout com frequência. Se o robô parar de achar vagas, rode com
  `HEADLESS=False` no `.env` e confira os seletores com o DevTools (F12).
- **Uso responsável**: respeite os termos de uso dos sites; os
  `DELAY_MIN`/`DELAY_MAX` no `.env` já ajudam a espaçar as requisições.
- **Status da vaga**: o campo `status` pode ser atualizado manualmente
  (ex: `"Candidatado"`) direto no banco, com um visualizador de SQLite
  (ex: DB Browser for SQLite).

## Licença

MIT — veja o arquivo [LICENSE](LICENSE).
