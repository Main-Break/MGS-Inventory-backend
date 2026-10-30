# Pendências conhecidas

Pontos deixados de fora de propósito nesta entrega (MVP), ou que ficaram
como próximo passo para quem continuar o projeto.

## Modelo de IA não treinado

Fora do escopo desta entrega. A classe `Neural` (`neural/neural.py`) e a
rota `POST /verifications` já tratam essa ausência: sem o arquivo do
modelo em `MODEL_PATH` (padrão `neural/producao.pt`), a rota responde `503
Service Unavailable` em vez de quebrar. Isso está coberto em teste
automatizado (`tests/test_verifications.py::test_envio_de_foto_sem_modelo_treinado_responde_503`).

Para treinar um modelo:

1. Monte um dataset no formato YOLO em `data/train/` (imagens + anotações).
2. Use a opção de treino do CLI (`python -m CLI.cli`, classe `Train` em
   `neural/train.py`).
3. Copie o resultado para o caminho de `MODEL_PATH` (`.env`).

A biblioteca `ultralytics` (usada só nesse ponto) é pesada e fica fora da
instalação padrão, conforme comentário em `requirements.txt`.

## Edição de outro usuário

A API não tem rota para o gestor editar nome/e-mail de **outro** usuário
(só o próprio usuário edita a si mesmo, em `PUT /users/me`). O gestor
consegue ativar, desativar, apagar (soft delete) e gerenciar permissões de
qualquer um, só não troca o nome ou e-mail de outra pessoa. Se isso for
necessário, é preciso: acrescentar uma rota em `routes/users.py` (ex: `PUT
/users/{id}`, só para gestor), e a tela correspondente em `views/users.py`
e `templates/users/form.html`.

## Backup do banco

`data/backup/` existe como pasta prevista, mas gerar o backup
(`mariadb-dump`) ainda não é automático. Fica como próximo passo: um
comando no CLI, ou uma tarefa agendada no servidor.

## Upload de foto pela interface web

A interface web (`/app/verifications`) só lista e aprova verificações já
enviadas. O envio da foto continua sendo feito por `POST /verifications`
na API, pensado para um app/dispositivo que tira a foto, não para o
navegador. Se um dia for necessário enviar foto também pela tela web, dá
para acrescentar um formulário com `<input type="file">` em
`views/verifications.py`, chamando a mesma lógica da rota da API.

## Integração direta com o BrERP

O batimento por peso (contagem × peso unitário vs. kg do ERP) e a fila de
divergências (`/app/divergencias`, `models/itens.py::list_with_divergence`)
já funcionam, mas o saldo em quilos (`stock_kg_erp`) chega hoje por dois
caminhos manuais: digitado no formulário do item, ou importado por CSV
(`/app/itens/importar`). Não existe ainda uma integração direta com o
BrERP (API, arquivo agendado, etc.) que mantenha esse campo sincronizado
sozinho. Enquanto isso não existir, alguém precisa exportar o relatório do
ERP e importar por CSV periodicamente.

## Front-end separado (histórico)

O projeto já previa, antes desta entrega, um front-end em outro endereço
(variável `FRONTEND_ORIGIN`, liberada no CORS). Essa configuração continua
valendo, caso outro sistema (fora da rede local) precise consumir a API
JSON de outro domínio. A interface web nova (`/app`) não depende dela, por
rodar no mesmo processo/porta da API.
