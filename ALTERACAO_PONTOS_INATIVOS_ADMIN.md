# Alteração: listagem de pontos para admin

## O que foi ajustado

- Na tela `Pontos de coleta`, quando o usuário logado é admin, o frontend envia `incluir_inativos=true` para `GET /pontos`.
- Usuário comum continua vendo apenas pontos disponíveis.
- Admin agora consegue visualizar pontos inativos, editar e reativar alterando o status para `ativo`.
- A tela exibe uma mensagem diferente para admin explicando que ativos, cheios e inativos estão sendo listados.
