# Interface web

Dashboard, cadastros e listagens, servidos pelo próprio FastAPI (sem
projeto de front-end separado), no prefixo `/app`. Pensada para uso humano,
lado a lado com a API JSON (`routes/`), que continua existindo para outros
sistemas (ERPs) consumirem.

## Sessão

O login em `/app/login` (formulário HTML) gera o mesmo token JWT usado pela
API (`util/security.py::create_token`), mas grava num cookie `httponly`
chamado `access_token` (ver `views/auth.py`), em vez de devolver o token
para o cliente guardar. O cookie expira em 8 horas, igual ao token.

`core.py::extract_token` aceita tanto o cookie quanto o header
`Authorization: Bearer`, então as mesmas dependências de acesso
(`current_user`, `require_permission`, `current_manager`) valem para as
duas interfaces (ver `docs/arquitetura.md`).

Logout (`POST /app/logout`) apaga o cookie e volta para `/app/login`.

## Telas

| Rota | Tela | Quem acessa |
|---|---|---|
| `GET /app/login` | Formulário de login | Qualquer um |
| `GET /app` | Dashboard (contadores) | Qualquer usuário logado |
| `GET /app/me` | Meu perfil (editar nome, e-mail, senha) | Qualquer usuário logado |
| `GET /app/users` | Lista e busca de usuários | `users.list` |
| `GET/POST /app/users/novo` | Cadastro de usuário | `users.create` |
| `POST /app/users/{id}/status` | Ativar, desativar, apagar usuário | `users.status` |
| `GET /app/users/{id}/permissoes` | Ver, liberar e retirar permissões de um usuário | Só gestor |
| `GET /app/materials` | Lista e busca de materiais | Qualquer usuário logado |
| `GET/POST /app/materials/novo` | Cadastro de material | `materials.create` |
| `GET/POST /app/materials/{id}/editar` | Edição de material | `materials.edit` |
| `POST /app/materials/{id}/status` | Ativar, desativar, apagar material | `materials.status` |
| `GET /app/itens` | Lista e busca de itens | Qualquer usuário logado |
| `GET/POST /app/itens/novo` | Cadastro de item | `itens.create` |
| `GET/POST /app/itens/{id}/editar` | Edição de item | `itens.edit` |
| `POST /app/itens/{id}/status` | Ativar, desativar, apagar item | `itens.status` |
| `GET /app/verifications` | Lista de verificações (foto, detecções, status) | Qualquer usuário logado (próprias, ou todas com `verifications.view_all`) |
| `POST /app/verifications/{id}/approve` | Aprovar ou reprovar | `verifications.approve` |

A lista de permissões e suas descrições está em
`models/permissions.py::DataPermission.PERMISSIONS`. O gestor sempre pode
tudo, independente de permissão cadastrada.

## Templates

- `templates/base.html`: layout com o menu superior (só aparece com usuário
  logado) e o bloco `conteudo`, estendido por todas as outras páginas.
- `templates/erro.html`: página genérica de erro (403, 404) dentro da
  interface web, usada pelo `exception_handler` de `core.py`.
- Cada seção (`users/`, `materials/`, `itens/`, `verifications/`) tem seus
  próprios templates de lista e formulário.
- `static/style.css`: único arquivo de estilo, sem framework de CSS ou JS.

## O que não existe (de propósito)

- Edição do cadastro de **outro** usuário (nome/e-mail) pelo gestor. A API
  também não tem essa operação (só `PUT /users/me`, o próprio usuário edita
  a si mesmo), então a interface web não inventa uma regra que o backend
  não tem. O gestor pode ativar, desativar, apagar e gerenciar permissões de
  qualquer usuário, só não edita o nome/e-mail de outra pessoa por ele.
- Envio de foto pela interface web. O envio (`POST /verifications`) é
  pensado para o app que tira a foto, não para o navegador. A tela web só
  lista e aprova o que já foi enviado.
