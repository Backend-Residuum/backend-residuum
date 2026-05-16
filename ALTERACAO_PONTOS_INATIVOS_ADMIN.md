# Alteração: pontos inativos visíveis para admin

## O que foi ajustado

- `GET /pontos` e `GET /pontos-coleta` agora aceitam `incluir_inativos=true`.
- Usuários comuns continuam vendo apenas pontos ativos/disponíveis.
- Apenas usuários com `role = admin` conseguem listar pontos inativos usando `incluir_inativos=true`.
- Isso permite que o admin encontre, edite e reative pontos inativos.

## Exemplo

```http
GET /pontos?incluir_inativos=true
```

Com token de admin: retorna pontos ativos, cheios e inativos.
Com token de usuário comum: ignora `incluir_inativos` e retorna apenas pontos ativos.
