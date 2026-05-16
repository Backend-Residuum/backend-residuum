# Alterações — Histórico com nomes reais e Perfil completo

Esta versão adiciona ajustes para alinhar o backend com o front e com a task RF006 de perfil.

## 1. Histórico e pendentes com nomes reais

Os endpoints abaixo continuam existindo, mas agora retornam respostas enriquecidas:

- `GET /descarte/historico`
- `GET /descarte/historico/geral`
- `GET /descarte/pendentes`

Campos adicionados ao retorno:

- `usuario_nome`
- `usuario_email`
- `ponto_coleta_nome`
- `ponto_coleta_endereco`
- `inventario_item_descricao`

Isso evita que o front mostre apenas `usuario_id` e `ponto_coleta_id` nas tabelas de histórico e pendentes.

## 2. Novo endpoint de perfil completo

Foi adicionado:

- `GET /perfil`

O endpoint retorna:

- dados pessoais do usuário;
- endereço;
- pontuação total;
- resumo do inventário;
- inventário ativo do usuário;
- histórico resumido de descartes;
- descartes pendentes.

Esse endpoint atende melhor ao RF006 e permite que o front monte a tela de perfil/dashboard com uma única chamada.

## 3. Arquivo auxiliar criado

Foi criado:

- `app/services/serializacao_service.py`

Ele centraliza a montagem de respostas JSON enriquecidas.

## 4. Testes sugeridos no Swagger

1. Faça login e autorize com Bearer token.
2. Teste `GET /perfil`.
3. Teste `GET /descarte/historico`.
4. Com usuário admin, teste `GET /descarte/historico/geral`.
5. Com usuário admin, teste `GET /descarte/pendentes`.

Os retornos devem exibir nomes reais em vez de apenas IDs.
