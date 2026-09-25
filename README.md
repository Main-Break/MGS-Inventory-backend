# mgs-inventario-backend

API em Python/FastAPI do projeto de inventário de estoque por foto da MGS
Plásticos de Engenharia: o funcionário fotografa as peças, um modelo de IA
(YOLO) conta, e fica registrado quem contou o quê.

Parte de um projeto acadêmico com 7 engenheiros. App em: `mgs-inventario-mobile`.

> Esta branch (`simplificacao-api`) é uma reescrita enxuta da versão anterior
> do backend (preservada na branch `feat/auth-upload-contagem-itens`): sem
> ORM, sem fila de treino via Celery, sem sistema de anotação de imagens e
> sem migração versionada - só o essencial pra API funcionar, fácil de ler e
> de mexer. O que ficou de fora dessa versão em relação à anterior:
> anotação/retreino do modelo pela API, recontagem manual, múltiplas fotos
> por verificação, suporte a MySQL/MariaDB. Se o time precisar de algo disso
> de volta, dá pra resgatar da outra branch.

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

| Rota | Quem | O que faz |
| --- | --- | --- |
| `POST /auth/login` | qualquer um | e-mail+senha → token JWT |
| `POST /users` | gestor | cadastra usuário |
| `GET /users` | gestor | lista usuários |
| `GET /users/me` `PUT /users/me` | logado | vê/edita os próprios dados |
| `PATCH /users/{id}/active` | gestor | ativa/desativa acesso |
| `POST /items` | gestor | cadastra item do catálogo |
| `GET /items?q=` `GET /items/{id}` | logado | busca/vê item |
| `POST /verifications` | logado | envia uma foto (`file`, `item_id` opcional), recebe a contagem da IA |
| `GET /verifications` `GET /verifications/{id}` | logado | funcionário vê as próprias, gestor vê todas |
| `PATCH /verifications/{id}/approve` | gestor | aprova/reprova |

Todas as rotas, fora login e `/health`, pedem `Authorization: Bearer <token>`.

## Modelo de IA

Coloque o `.pt` treinado em `MODEL_PATH` (padrão `modelos/producao.pt`). Sem
ele, `POST /verifications` responde 503. O dataset e os pesos treinados da
versão anterior continuam na pasta `app/neural/` (fora do git, local); para
treinar um modelo novo a partir de um `dataset.yaml`:

```bash
python treinar.py caminho/do/dataset.yaml
```

## Arquivos

```
main.py       app FastAPI, todas as rotas
config.py     lê o .env
database.py   conexão SQLite + criação das tabelas no start
security.py   senha, token JWT, quem pode fazer o quê
ai.py         roda o modelo na foto
models.py     formatos de entrada/saída
treinar.py    script de treino, rodado na mão
database.sql  schema completo, só para consulta
```

Sem ORM: o SQL fica na rota, escrito à mão, sempre com `?` como parâmetro
(protege contra SQL injection). Senha guardada com PBKDF2-HMAC-SHA256.
