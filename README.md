# Inventário por Foto - API

API em Python/FastAPI do inventário de estoque por foto: o funcionário
fotografa as peças, o modelo de rede neural conta, e fica registrado quem
contou, quanto contou e o quanto a contagem bate com a recontagem manual.

## Como funciona, em 4 partes

1. **Usuários**: dois papéis, `gestor` e `funcionario`. Só o gestor cadastra
   pessoas e controla o acesso.
2. **Itens**: o catálogo do estoque. O `label` de cada item é o nome exato da
   classe que o modelo devolve, e é o que liga a foto ao item cadastrado.
3. **Verificações**: uma ou mais fotos enviadas de uma vez, contadas pelo
   modelo e somadas por item.
4. **Modelo**: um arquivo `.pt` do YOLO apontado por `MODEL_PATH`. Treinado
   fora da API pelo `treinar.py`.

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env     # defina pelo menos ADMIN_PASSWORD
python main.py           # sobe em http://localhost:8000
```

As tabelas são criadas sozinhas no start, não existe migração para rodar na
mão. Na primeira subida, se não houver nenhum gestor no banco, um é criado
com o `ADMIN_EMAIL`/`ADMIN_PASSWORD` do `.env`. Troque a senha em
`PATCH /users/me` logo depois do primeiro login.

Documentação interativa: `http://localhost:8000/docs`

## Rotas

| Rota | Quem pode | O que faz |
| --- | --- | --- |
| `POST /auth/login` | qualquer um | Troca e-mail e senha por um token JWT |
| `POST /users` | gestor | Cadastra usuário |
| `GET /users` | gestor | Lista todos |
| `GET /users/{id}` | gestor | Vê um usuário |
| `PATCH /users/{id}/active` | gestor | Ativa ou desativa o acesso |
| `GET /users/me` | logado | Os próprios dados |
| `PATCH /users/me` | logado | Muda nome, e-mail ou senha |
| `POST /items` | gestor | Cadastra item |
| `PATCH /items/{id}` | gestor | Edita item |
| `GET /items?q=termo` | logado | Busca por nome ou label |
| `GET /items/{id}` | logado | Vê um item |
| `POST /verifications` | logado | Envia as fotos e recebe a contagem |
| `GET /verifications` | logado | Funcionário vê as dele, gestor vê todas |
| `GET /verifications/{id}` | dono ou gestor | Vê uma verificação |
| `PATCH /verifications/{id}/manual-count` | dono | Informa a recontagem manual |
| `PATCH /verifications/{id}/approval` | gestor | Aprova ou reprova |

Todas as rotas, fora o login e o `/health`, pedem o cabeçalho
`Authorization: Bearer <token>`.

### Enviando fotos

`POST /verifications` é `multipart/form-data`, com o campo `files` (uma ou
mais imagens) e, opcionalmente, `expected_item_id` (o item que o funcionário
selecionou para contar).

A resposta traz, por item contado:

- `count`: quantas peças o modelo contou, somando todas as fotos.
- `ai_confidence_pct`: a confiança média que o próprio modelo reportou.
- `manual_accuracy_pct`: o quanto a contagem da IA bate com a recontagem
  manual, preenchido depois que o funcionário informa o `manual_count`.
- `diverge_do_esperado`: `true` quando apareceu na foto algo diferente do
  item que o funcionário disse que ia contar.

## Modelo de detecção

Coloque o `.pt` treinado no caminho do `MODEL_PATH` (por padrão
`./modelos/producao.pt`). Enquanto ele não existir, toda a API funciona e só
`POST /verifications` responde 503 com a mensagem explicando o motivo.

Para treinar, com um dataset em formato YOLO (pastas `images/` e `labels/`
mais um `dataset.yaml`):

```bash
python treinar.py caminho/do/dataset.yaml
```

O treino copia sozinho o melhor peso gerado para o `MODEL_PATH`.

## Estrutura

```
main.py          sobe a API, roda as migrações e registra as rotas
config.py        lê o .env
database.py      conexão com o banco e as 3 operações usadas nas rotas
migrations.py    cria e atualiza as tabelas sozinho no start
seguranca.py     hash de senha, token JWT e quem pode fazer o quê
neural.py        roda o modelo na foto e devolve a contagem
treinar.py       script de treino, rodado na mão
database.sql     o schema completo, só para consulta
models/          o que a API recebe e devolve
routes/          uma rota por assunto, com o SQL escrito à vista
```

Sem ORM: todo SQL fica visível na rota, escrito à mão e sempre com
parâmetros nomeados, que é o que protege contra SQL injection. As senhas são
guardadas com PBKDF2-HMAC-SHA256.
