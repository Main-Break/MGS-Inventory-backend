# mgs-inventario-backend

API em **Python / FastAPI** do projeto de **inventário de estoque por foto** da MGS Plásticos de Engenharia.
Recebe as contagens sincronizadas pelo app, faz o **batimento por peso** contra o ERP (contagem × peso unitário vs. kg registrados),
gerencia a fila de divergências e o import/export por planilha.

Parte de um projeto acadêmico com 7 engenheiros. App em: `mgs-inventario-mobile`.

## Stack

- **Python 3.11+** + **FastAPI**
- **SQLAlchemy** + **Alembic** (ORM e migrations)
- **Pydantic** (schemas)
- **Ultralytics (YOLOv8/v11)** — treino e inferência de fallback no servidor
- **OpenCV** — processamento de imagem
- **openpyxl / pandas** — import/export de planilha

## Escopo do MVP

- Import da planilha do ERP (código, descrição, peso unitário, saldo em kg)
- Endpoint de detecção (fallback quando o celular não roda on-device)
- Batimento por peso com tolerância por SKU + fila de divergências
- Export dos registros para planilha (formato de batimento com o ERP)
- Endpoint de sincronização do lote offline com idempotência

Fora do MVP: soma de seções (stitching), integração direta com o BrERP, painel web.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # ajuste as variáveis
alembic upgrade head               # cria as tabelas
uvicorn app.main:app --reload      # sobe em http://localhost:8000
```

Documentação interativa da API: `http://localhost:8000/docs`

## Estrutura (referência)

```
app/
├── main.py               # app FastAPI + middlewares
├── models.py             # ORM (SQLAlchemy) + schemas (Pydantic)
├── database.py           # sessão/conexão
├── routes/
│   ├── detection.py      # POST /detect (YOLO)
│   ├── sync.py           # recebe lote offline do app
│   └── inventory.py      # registros, divergências, export
└── services/
    ├── validation.py     # batimento por peso
    └── spreadsheet.py    # import/export planilha
alembic/                  # migrations
```

## Variáveis de ambiente (`.env`)

```
DATABASE_URL=sqlite:///./inventario.db
MODEL_PATH=./models/yolo-bastoes.pt
UPLOAD_DIR=./uploads
```

## Convenções

- Branches: `feat/...`, `fix/...`, `chore/...`
- Formatação com `black` + `ruff`; PR com 1 revisão antes do merge em `main`

> Plano de sprints e critérios de aceite do MVP: ver documento do projeto.
