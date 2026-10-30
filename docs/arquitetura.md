# Arquitetura

Este documento explica como o projeto está organizado e por quê, para quem
for dar continuidade ao trabalho sem nunca ter visto o código.

## Visão geral

O sistema é uma única aplicação FastAPI com duas famílias de rotas:

- **API JSON** (`routes/`): pensada para outros sistemas consumirem (outros
  ERPs na mesma rede). Autenticação por token (JWT) no header
  `Authorization: Bearer <token>`.
- **Interface web** (`views/` + `templates/`): dashboard, cadastros e
  listagens para uso humano, no prefixo `/app`. Autenticação pelo mesmo
  token, mas guardado em cookie (login em `/app/login`).

As duas interfaces compartilham a mesma base de regras de negócio
(`models/`) e as mesmas checagens de acesso (`core.py`). Nenhuma regra de
permissão existe duplicada entre as duas.

## Camadas

A regra do projeto é que cada camada só conhece as anteriores:

```
database/  ->  models/  ->  core.py  ->  routes/ e views/  ->  register.py  ->  main.py
```

| Camada | Responsabilidade |
|---|---|
| `database/database.py` | Classe `Database`: único lugar do projeto com SQL. Os models herdam dela. |
| `database/migrate.py` | Aplica `database.sql` no banco sozinho, na subida do sistema. |
| `models/` | Uma classe por tabela (`DataUser`, `DataItem`, `DataMaterial`, `DataVerification`, `DataPermission`). Regra de negócio de cada entidade. |
| `core.py` | Lê o `.env`, cria os objetos compartilhados (models, rede neural, templates), define quem está logado e o que cada um pode fazer. |
| `routes/` | Rotas da API JSON. Controllers finos: validam entrada (Pydantic), chamam o model certo, devolvem o resultado ou um erro HTTP. |
| `views/` | Rotas da interface web. Mesma ideia dos controllers de `routes/`, mas devolvem uma página HTML (via `templates/`) em vez de JSON. |
| `register.py` | Registra as rotas de `routes/` e `views/` no app. |
| `main.py` | Sobe o servidor (`uvicorn`). |
| `CLI/cli.py` | Funções administrativas pelo terminal, fora da API, direto nos models. |

## Por que a interface web não duplica regra de negócio

Um controller de `views/` segue exatamente o mesmo caminho de um controller
de `routes/`:

1. Depende de `current_user`, `require_permission("...")` ou `current_manager`
   (definidos em `core.py`) para checar quem está logado e o que pode fazer.
2. Chama o mesmo model (`users`, `itens`, `materials`, `verifications`,
   `permissions`, instanciados uma vez em `core.py`) para ler ou alterar
   dados.
3. A única diferença é a resposta: `routes/` devolve JSON (`response_model`
   do Pydantic), `views/` devolve uma página (`templates.TemplateResponse`).

Por isso, se uma regra de permissão mudar, ela muda em um lugar só
(`core.py` ou no model correspondente) e vale para as duas interfaces.

## Padrões usados

- **Repository**: `Database` (em `database/database.py`) expõe operações
  genéricas (`insert_table`, `update_table`, `delete_data`, `select_one`,
  `select_all`, `search_data`) e cada model (`DataUser`, `DataItem`...) usa
  essas operações para a sua tabela, sem escrever SQL novo.
- **Dependency Injection**: o FastAPI injeta `current_user`,
  `require_permission("...")` etc. nas rotas via `Depends(...)`. A rota não
  sabe como o token é lido ou como a permissão é checada, só declara o que
  precisa.
- **Factory de checagem**: `require_permission(permissão)` (em `core.py`)
  constrói, na hora, a dependência certa para a permissão pedida. É assim
  que `itens.create`, `materials.edit` etc. reaproveitam a mesma função em
  vez de uma checagem escrita à mão em cada rota.
- **Controllers finos**: nenhuma rota (API ou view) decide regra de negócio.
  Ela só valida entrada, chama o model e traduz o resultado em uma resposta
  HTTP ou numa página.
- **SRP (responsabilidade única)**: cada arquivo faz uma coisa. SQL só em
  `database/database.py`. Validação de dado só em `models/schemas.py`.
  Segurança de senha e token só em `util/security.py`.

## Autenticação: um token, dois jeitos de chegar

`core.py` define `extract_token(request, credentials)`, que é o único ponto
de verdade de autenticação:

- Se vier o header `Authorization: Bearer <token>` (API, outros sistemas),
  usa esse token.
- Senão, procura o cookie `access_token` (interface web, gravado no login em
  `/app/login`).

Dessa forma, `current_user`, `require_permission` e `current_manager`
funcionam sem alteração nas duas interfaces.

## Erros: JSON para a API, página para a interface web

Um `@API.exception_handler(HTTPException)` em `core.py` decide o formato da
resposta de erro pela URL:

- Rotas `routes/` (qualquer caminho fora de `/app`): sempre JSON
  (`{"detail": "..."}`), como qualquer API REST.
- Rotas `views/` (prefixo `/app`): sem login redireciona para
  `/app/login`; sem permissão mostra a página `templates/erro.html`.

## Onde mexer para adicionar algo novo

- **Uma tabela nova**: acrescente o `CREATE TABLE` em
  `database/database.sql`, crie o model em `models/` herdando de `Database`,
  e (se fizer sentido) o schema Pydantic em `models/schemas.py`. A migração
  automática cria a tabela na próxima subida, sem passo manual.
- **Uma permissão nova**: acrescente a chave em
  `models/permissions.py::DataPermission.PERMISSIONS` e use
  `require_permission("chave")` na rota. A tabela `user_permissions` não
  muda, ela guarda qualquer texto.
- **Uma rota nova na API**: crie em `routes/`, registre em `register.py`.
- **Uma tela nova na interface web**: crie o controller em `views/` e o(s)
  template(s) em `templates/`, registre em `register.py`.
