# Alterações Task 8 e Task 9 — Pontos de Coleta

## Implementado

### Task 8 — Detalhes do Ponto (RF008)
Foram adicionados novos campos ao ponto de coleta:

- `capacidade_maxima`: capacidade estimada do ponto em kg.
- `tipos_residuos_aceitos`: lista de resíduos aceitos pelo ponto.
- `horario_funcionamento`: descrição textual do horário de funcionamento.
- `status`: `ativo`, `cheio` ou `inativo`.

As respostas de pontos agora também trazem:

- `status_calculado`: calcula `cheio` quando o inventário atinge a capacidade máxima.
- `total_inventario`: soma total em kg do inventário do ponto.
- `percentual_ocupacao`: percentual de ocupação do ponto quando há capacidade configurada.
- `distancia_km`: distância calculada quando a listagem recebe latitude/longitude do usuário.

### Task 9 — GET /pontos com filtros
A rota `GET /pontos-coleta` agora aceita filtros:

```txt
GET /pontos-coleta?tipo_residuo=plastico&lat=-3.08&long=-60.01&distancia_km=5
```

Parâmetros disponíveis:

- `tipo_residuo`: filtra pontos que aceitam aquele tipo de resíduo.
- `lat`: latitude do usuário.
- `long`: longitude do usuário.
- `distancia_km`: distância máxima em quilômetros.
- `incluir_inativos`: se `true`, inclui pontos inativos na resposta.

Também foi criado o alias:

```txt
GET /pontos
```

Esse alias usa a mesma lógica de `/pontos-coleta`, para ficar compatível com a task do Word.

## Migration

Nova migration:

```txt
alembic/versions/task8_task9_pontos_detalhes_filtros.py
```

Depois de substituir o backend, rode:

```bash
python -m alembic upgrade head
```

## Exemplo de criação de ponto

```json
{
  "nome": "Ponto de Coleta Centro",
  "endereco": "Av. Eduardo Ribeiro, Centro, Manaus - AM",
  "latitude": -3.131633,
  "longitude": -60.023437,
  "raio_operacao": 1000,
  "capacidade_maxima": 500,
  "tipos_residuos_aceitos": ["plastico", "papel", "aluminio"],
  "horario_funcionamento": "Segunda a sábado, 08h às 18h",
  "status": "ativo"
}
```

## Exemplo de filtro

```txt
GET /pontos?tipo_residuo=plastico&lat=-3.1316&long=-60.0234&distancia_km=2
```
