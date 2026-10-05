# Inventário por Foto - API

Funcionário fotografa as peças, o modelo conta, e fica registrado quem
contou o quê.

## Rodar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # defina ADMIN_PASSWORD e JWT_SECRET
python main.py         # http://localhost:8000/docs
```

As tabelas são criadas sozinhas na primeira subida, junto com um gestor
(`ADMIN_EMAIL`/`ADMIN_PASSWORD` do `.env`).

## Rotas

Login é `POST /auth/login` (e-mail+senha, devolve token JWT). Tudo o resto
pede `Authorization: Bearer <token>`, exceto `/health`.

- `POST /users`, `GET /users` - só gestor, cadastra e lista usuário
- `GET /users/me`, `PUT /users/me` - qualquer logado vê/edita os próprios dados
- `PATCH /users/{id}/active` - só gestor, ativa/desativa acesso
- `POST /items` - só gestor, cadastra item do catálogo
- `GET /items?q=`, `GET /items/{id}` - busca/vê item
- `POST /verifications` - manda uma foto (`file`, `item_id` opcional), volta a contagem
- `GET /verifications`, `GET /verifications/{id}` - funcionário vê as próprias, gestor vê tudo
- `PATCH /verifications/{id}/approve` - só gestor, aprova/reprova

## Modelo

Fica em `MODEL_PATH` (padrão `neural/producao.pt`). Sem esse arquivo,
`POST /verifications` responde 503. Pra treinar um novo, joga o dataset
(formato YOLO) em `uploads/train/` e roda `python cli.py`, opção de treino.

## Arquivos

- `config.py` - o inicial: lê o `.env`, define caminhos e variáveis de ambiente
- `main.py` - monta o app, roda a migração do banco e junta as rotas de `routes/`
- `cli.py` - o que não é rota: criar usuário/gestor pelo terminal, treino
- `security.py` - senha, token, quem pode fazer o quê
- `schemas.py` - formato do que entra e sai da API (Pydantic)
- `models/` - acesso ao banco, uma classe por tabela (`user.py`, `item.py`, `verification.py`), mais `database.py` (conexão/execução de SQL) e `schema.py` (cria/confere as tabelas)
- `routes/` - um arquivo por seção (auth, users, items, verifications)
- `neural/` - roda e treina o modelo
- `data/` - onde fica o `.db`
- `uploads/` - fotos enviadas, e `uploads/train/` com dataset de treino

SQL é escrito à mão nos `models/`, sempre com `?` como parâmetro - nada de
concatenar valor em string, é isso que evita SQL injection. Sem ORM de
propósito, pra continuar fácil de mexer direto no banco. Senha guardada
com PBKDF2-HMAC-SHA256.
