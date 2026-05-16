# Implementação Task 11 — Inventário de Resíduos do Usuário

Esta versão adiciona o módulo de inventário pessoal do usuário, permitindo cadastrar resíduos antes da transferência para um ponto de coleta.

## Novos arquivos

- `app/models/inventario_usuario.py`
- `app/schemas/inventario_usuario.py`
- `app/routes/inventario_usuario.py`
- `alembic/versions/task11_inventario_usuario.py`

## Alterações em arquivos existentes

- `app/main.py`: registra as rotas do inventário.
- `app/models/descarte.py`: adiciona `inventario_usuario_id`.
- `app/routes/descarte.py`: ao confirmar descarte vindo do inventário, baixa a quantidade confirmada do inventário do usuário e libera a quantidade reservada.
- `alembic/env.py`: importa o model `InventarioUsuario`.

## Novos endpoints

### POST `/me/inventario`
Cadastra um item no inventário pessoal do usuário autenticado.

Body:
```json
{
  "tipo_residuo": "plastico",
  "quantidade": 5,
  "descricao": "Garrafas PET acumuladas em casa",
  "observacao": "Teste"
}
```

### GET `/me/inventario`
Lista os itens do inventário do usuário.

Também aceita filtro opcional:

```txt
GET /me/inventario?status=disponivel
```

### GET `/me/inventario/{item_id}`
Busca um item específico do inventário.

### PUT `/me/inventario/{item_id}`
Atualiza um item, desde que não viole a quantidade reservada em descartes pendentes.

### DELETE `/me/inventario/{item_id}`
Remove logicamente o item, alterando status para `cancelado`. Não remove se houver quantidade reservada.

### POST `/me/inventario/{item_id}/descartar`
Cria um descarte pendente usando um item do inventário pessoal.

Body:
```json
{
  "quantidade": 2,
  "ponto_coleta_id": 1,
  "usuario_lat": -3.0759,
  "usuario_long": -60.06,
  "observacao": "Transferência a partir do inventário",
  "qrcode_token": null
}
```

## Fluxo esperado

1. Usuário cadastra resíduos em `/me/inventario`.
2. Usuário cria descarte a partir do item em `/me/inventario/{item_id}/descartar`.
3. O item fica com a quantidade reservada enquanto o descarte está pendente.
4. Admin confirma o descarte em `/descarte/{id_descarte}/confirmar`.
5. O sistema baixa a quantidade confirmada do inventário do usuário.
6. O inventário do ponto de coleta e a pontuação do usuário são atualizados.

## Rodar migration

```bash
python -m alembic upgrade head
```

A nova tabela esperada no banco é:

```txt
inventario_usuario
```

E a tabela `descarte` passa a ter:

```txt
inventario_usuario_id
```
