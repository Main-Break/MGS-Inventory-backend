# Inventário por Foto - API

O funcionário fotografa os itens do estoque, o modelo de IA reconhece e conta,
e fica registrado quem contou o quê.

## Rodar

Precisa de um banco MySQL ou MariaDB (só o usuário e os bancos vazios, as
tabelas são criadas sozinhas na subida, ver `docs/banco-de-dados.md`).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # preencha DB_*, DB_NAME_TEST, JWT_SECRET e ADMIN_PASSWORD

python main.py          # http://localhost:8000/docs  (API)  e  http://localhost:8000/app  (interface web)
```

Na primeira subida é criado um gestor com o `ADMIN_EMAIL` e o `ADMIN_PASSWORD` do `.env`, e o esquema do banco é aplicado sozinho (`database/database.sql`).

Funções administrativas pelo terminal (usuários, itens, verificações, treino):

```bash
python -m CLI.cli
```

## Testes

```bash
python -m pytest
```

34 testes de integração, contra o banco de teste (`DB_NAME_TEST` do `.env`),
cobrindo login, permissões, CRUD de materiais/itens/usuários e verificações.

## Estrutura

```
database/
    database.py      classe mãe Database, o único lugar do projeto com SQL
    database.sql     esquema completo das tabelas
    migrate.py       aplica o esquema sozinho na subida (ver docs/banco-de-dados.md)
models/
    user.py          DataUser, tabela users
    permissions.py   DataPermission, permissões extras de cada usuário
    materials.py     DataMaterial, tabela materials (PEAD, PP, POM... com a densidade)
    itens.py         DataItem, tabela itens
    verification.py  DataVerification, tabela verifications
    schemas.py       formato do que entra e sai da API (Pydantic)
routes/              API JSON, para outros sistemas (ERPs) consumirem, um arquivo por seção
views/               interface web (HTML), prefixo /app, mesmas regras de routes/
templates/           páginas HTML usadas por views/
static/              CSS da interface web
util/
    security.py      senha e token de acesso
neural/
    neural.py        classe Neural, reconhece e conta os itens na foto
    train.py         classe Train, treina o modelo
data/
    train/           imagens e datasets de treinamento
    database/        arquivos .db / .sqlite de cache
    backup/          backups do banco
    upload/          fotos enviadas nas verificações
tests/               testes automatizados (pytest)
docs/                documentação detalhada (arquitetura, banco, interface web, pendências)
CLI/cli.py           funções administrativas pelo terminal
core.py              configurações (.env), objetos compartilhados e o app FastAPI
register.py          registro das rotas (routes/ e views/)
main.py              sobe o servidor
```

Cada parte só conhece as anteriores:

```
database/  ->  models/  ->  core.py  ->  routes/ e views/  ->  register.py  ->  main.py
```

Documentação detalhada em `docs/`:

- [`docs/arquitetura.md`](docs/arquitetura.md): camadas, padrões usados, como estender.
- [`docs/banco-de-dados.md`](docs/banco-de-dados.md): esquema e migração automática.
- [`docs/interface-web.md`](docs/interface-web.md): telas e rotas de `/app`.
- [`docs/pendencias.md`](docs/pendencias.md): o que ficou de fora desta entrega.

## Regras do projeto

- **SQL só existe em `database/database.py`.** Os models herdam da classe
  `Database` e usam apenas as funções dela (`insert_table`, `update_table`,
  `delete_data`, `select_one`, `select_all`, `search_data`). Se a forma de
  falar com o banco mudar, só esse arquivo muda.
- **Proteção contra SQL Injection:** valores vão sempre como parâmetro (`%s`),
  e nomes de tabela e coluna passam pelo `check_names`.
- **Ids são UUID-4**, gerados pela `Database` no insert. Não dá para adivinhar
  o id de outro registro.
- **Status** (`active`, `disable`, `deleted`) em usuários e itens. Para apagar,
  use o status `deleted` (soft delete), assim o histórico das verificações continua.
- **Toda função dos models devolve `(sucesso, dado)`:** em caso de sucesso, o
  dado é o registro ou a lista; em caso de falha, é uma mensagem pronta para
  mostrar ao usuário.
- **Permissões por ação:** o gestor pode tudo. O funcionário pode o básico
  (enviar fotos, ver as próprias verificações, consultar itens e materiais) e
  o que o gestor liberar para ele, ação por ação (ex: `itens.create`,
  `materials.edit`). A lista fica em `models/permissions.py`. Só o gestor
  libera permissões, e quem não é gestor nunca cria nem altera um gestor.
- Senha guardada com PBKDF2-HMAC-SHA256.

## Rotas da API

(Rotas da interface web, em `/app`, estão em [`docs/interface-web.md`](docs/interface-web.md).)

O login é `POST /auth/login` (e-mail e senha, devolve o token). Todas as outras
pedem `Authorization: Bearer <token>`, menos `/health`.

Entre parênteses, a permissão exigida (o gestor sempre pode).

- `POST /users` (`users.create`), `GET /users?q=` (`users.list`), `PATCH /users/{id}/status?new_status=` (`users.status`)
- `GET /users/me`, `PUT /users/me`: qualquer usuário logado vê e edita os próprios dados (o `/me` traz as permissões)
- `GET /users/permissions/available`: lista de permissões que podem ser liberadas
- `GET`, `POST`, `DELETE /users/{id}/permissions/{permissão}`: só gestor, vê, libera e retira permissões
- `POST /materials` (`materials.create`), `PUT /materials/{id}` (`materials.edit`), `PATCH /materials/{id}/status` (`materials.status`)
- `GET /materials?q=`, `GET /materials/{id}`: qualquer usuário logado
- `POST /itens` (`itens.create`), `PUT /itens/{id}` (`itens.edit`), `PATCH /itens/{id}/status` (`itens.status`)
- `GET /itens?q=`, `GET /itens/{id}`: qualquer usuário logado, busca por nome, label, SKU ou código de barras
- `POST /verifications`: envia uma foto (`file`, `item_id` opcional) e recebe a contagem
- `GET /verifications`, `GET /verifications/{id}`: cada um vê as próprias, com `verifications.view_all` vê todas
- `PATCH /verifications/{id}/approve?approved=` (`verifications.approve`)

## Modelo de IA

Fica em `MODEL_PATH` (padrão `neural/producao.pt`). Sem esse arquivo,
`POST /verifications` responde 503. Para treinar um novo, coloque o dataset
(formato YOLO) em `data/train/` e use a opção de treino do CLI.
