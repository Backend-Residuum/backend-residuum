# RF021 - Painel da Cooperativa: Mapa/Listagem de Pontos de Coleta

Este guia explica como preparar o ambiente local e validar a RF021 do Residuum: o painel da cooperativa para visualizar os pontos de coleta sob sua responsabilidade, com quantidade atual, capacidade, percentual de preenchimento e status de capacidade.

## 1. O Que Foi Implementado

A RF021 adiciona um endpoint para a cooperativa autenticada consultar apenas os pontos de coleta vinculados a ela.

Endpoint principal:

```http
GET /cooperativa/painel/pontos-coleta
```

Esse endpoint:

- exige autenticação via JWT;
- exige usuário com `role="cooperativa"`;
- retorna somente pontos onde `ponto_coleta.cooperativa_id` é igual ao id da cooperativa logada;
- não retorna pontos de outras cooperativas;
- usa o inventário atual do ponto para calcular ocupação;
- usa `capacidade_maxima` como limite/capacidade;
- retorna status de capacidade para destacar pontos quase cheios ou cheios;
- aparece no Swagger/ReDoc por ser uma rota FastAPI comum.

Também foi adicionada uma visualização simples no painel de testes:

```http
GET /painel-testes
```

## 2. Arquivos Alterados

Arquivos principais da RF021:

```text
app/routes/ponto_coleta.py
app/schemas/ponto_coleta.py
app/main.py
```

Não foi criada migration Alembic, porque o banco já possuía os campos necessários:

```text
ponto_coleta.cooperativa_id
ponto_coleta.capacidade_maxima
ponto_coleta.inventario
```

## 3. Modificações Realizadas Na Task

Esta seção resume exatamente o que foi alterado para implementar a RF021.

### `app/routes/ponto_coleta.py`

Principais alterações:

- removidos marcadores de conflito Git que existiam no arquivo, como `<<<<<<<`, `=======` e `>>>>>>>`;
- preservados os imports e funcionalidades existentes de pontos de coleta, horários e QR Code;
- adicionada a função `_status_capacidade_painel()`;
- adicionada a função `_serializar_ponto_painel_cooperativa()`;
- criado o endpoint:

```http
GET /cooperativa/painel/pontos-coleta
```

Esse endpoint:

- usa `require_role("cooperativa")`;
- identifica a cooperativa pelo usuário autenticado;
- filtra pontos por `PontoColeta.cooperativa_id == usuario_atual.id`;
- não permite que uma cooperativa veja pontos de outra;
- retorna mensagem adequada quando não há pontos vinculados;
- calcula `quantidade_atual` somando o inventário do ponto;
- calcula `percentual_preenchimento` com:

```text
quantidade_atual / limite_capacidade * 100
```

- classifica `status_capacidade` como `ativo`, `quase_cheio`, `cheio` ou `inativo`;
- respeita o status operacional já existente do ponto, usando `status_ponto_coleta()`.

### `app/schemas/ponto_coleta.py`

Principais alterações:

- criado o schema `PontoColetaPainelCooperativaItem`;
- criado o schema `PainelCooperativaResponse`;
- definidos os campos retornados pela RF021:

```text
id
nome
endereco
latitude
longitude
tipo_residuo
quantidade_atual
limite_capacidade
percentual_preenchimento
status_capacidade
```

Esses schemas também ajudam o endpoint a aparecer corretamente documentado no Swagger/ReDoc.

### `app/main.py`

Principais alterações:

- adicionada uma nova seção no `/painel-testes`:

```text
Seção 3: Painel da Cooperativa
```

- adicionada a função JavaScript `carregarPainelCooperativa()`;
- o painel visual chama:

```http
GET /cooperativa/painel/pontos-coleta
```

- os cards exibem:

```text
nome do ponto
endereço
tipos de resíduos
coordenadas
quantidade atual
capacidade
percentual preenchido
status de capacidade
```

- pontos são destacados visualmente:

```text
ativo        -> verde
quase_cheio -> amarelo
cheio        -> vermelho
inativo      -> cinza
```

- a tela foi integrada aos fluxos do painel de testes para atualizar depois de login, descarte e confirmação.

### O Que Não Foi Alterado

Para reduzir risco de regressão, a RF021 não alterou:

- regra de pontuação;
- confirmação de descarte;
- validação por QR Code;
- geofencing;
- inventário do usuário;
- transferência de resíduos para o ponto;
- autenticação JWT;
- autorização global da API;
- estrutura de banco de dados.

Também não foi adicionada dependência obrigatória de Google Maps, porque a integração externa não faz parte obrigatória do MVP.

## 4. O Que Você Precisa Ter Instalado

### Opção Recomendada: Com Docker

Instale:

- Docker Desktop;
- Git;
- um terminal, como PowerShell ou Windows Terminal.

Com Docker, você não precisa instalar PostgreSQL manualmente.

### Opção Sem Docker

Instale:

- Python 3.11 ou superior;
- PostgreSQL;
- Git;
- um editor, como VS Code;
- opcionalmente, Postman ou Insomnia.

Verifique as versões:

```powershell
python --version
pip --version
git --version
```

Se usar Docker:

```powershell
docker --version
docker compose version
```

## 5. Preparando O Projeto

Na pasta do projeto:

```powershell
cd "C:\Users\HERICK LEAL\Documents\PROJETO RESIDUUM\backend-residuum"
```

Confira se os arquivos existem:

```powershell
dir
```

Você deve ver arquivos como:

```text
requirements.txt
docker-compose.yml
alembic.ini
app/
alembic/
```

## 6. Configurando Variáveis De Ambiente

Copie o arquivo de exemplo:

```powershell
copy .env.example .env
```

Abra o `.env` e confira a variável `DATABASE_URL`.

Exemplo com PostgreSQL local:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/residuum
SECRET_KEY=sua-chave-secreta
```

Exemplo comum com Docker Compose:

```env
DATABASE_URL=postgresql://usuario:senha@db:5432/residuum
SECRET_KEY=sua-chave-secreta
```

Use os valores compatíveis com o seu `docker-compose.yml`.

## 7. Rodando Com Docker

Suba os containers:

```powershell
docker compose up --build
```

Em outro terminal, aplique as migrations:

```powershell
docker compose exec api alembic upgrade head
```

Se o serviço da API tiver outro nome no `docker-compose.yml`, substitua `api` pelo nome correto.

Exemplo:

```powershell
docker compose ps
```

A API deve ficar disponível em algo como:

```text
http://localhost:8000
```

ou:

```text
http://localhost:8080
```

Confira no terminal qual porta foi exposta.

## 8. Rodando Sem Docker

Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Instale as dependências:

```powershell
pip install -r requirements.txt
```

Aplique as migrations:

```powershell
alembic upgrade head
```

Suba a API:

```powershell
uvicorn app.main:app --reload
```

Acesse:

```text
http://localhost:8000
```

## 9. Conferindo Swagger E ReDoc

Abra no navegador:

```text
http://localhost:8000/docs
```

ou:

```text
http://localhost:8000/redoc
```

Procure pela tag:

```text
Cooperativa
```

E pelo endpoint:

```text
GET /cooperativa/painel/pontos-coleta
```

Se ele aparecer no Swagger/ReDoc, a rota foi registrada corretamente.

## 10. Criando Usuários Para Teste

Você precisa de pelo menos:

- 1 usuário admin;
- 1 usuário cooperativa;
- opcionalmente, 1 usuário comum.

O cadastro público cria usuário comum:

```http
POST /usuarios
```

Body:

```json
{
  "nome": "Cooperativa Norte",
  "email": "coop.norte@residuum.com",
  "telefone": "92999990000",
  "senha": "123456"
}
```

Depois, promova esse usuário para cooperativa usando um admin:

```http
PATCH /admin/usuarios/{usuario_id}/role
```

Body:

```json
{
  "role": "cooperativa"
}
```

Também crie outra cooperativa para testar isolamento:

```json
{
  "nome": "Cooperativa Sul",
  "email": "coop.sul@residuum.com",
  "telefone": "92999990001",
  "senha": "123456"
}
```

Promova também para:

```json
{
  "role": "cooperativa"
}
```

## 11. Fazendo Login

Use:

```http
POST /login
```

Body:

```json
{
  "email": "coop.norte@residuum.com",
  "senha": "123456"
}
```

A resposta deve conter um token:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "usuario_id": 2
}
```

No Swagger, clique em `Authorize` e informe:

```text
Bearer eyJ...
```

No Postman/Insomnia, use o header:

```http
Authorization: Bearer eyJ...
```

## 12. Criando Pontos Vinculados À Cooperativa

Faça login como admin e crie pontos de coleta.

Endpoint:

```http
POST /pontos-coleta
```

Ponto da Cooperativa Norte:

```json
{
  "nome": "Ecoponto Centro",
  "endereco": "Av. Eduardo Ribeiro, Centro, Manaus - AM",
  "latitude": -3.131633,
  "longitude": -60.023437,
  "raio_operacao": 1000,
  "capacidade_maxima": 1000,
  "tipos_residuos_aceitos": ["plastico", "papel", "metal"],
  "horario_funcionamento": "Segunda a sexta, 08h às 17h",
  "status": "ativo",
  "cooperativa_id": 2
}
```

Ponto da Cooperativa Sul:

```json
{
  "nome": "Ecoponto Distrito",
  "endereco": "Distrito Industrial, Manaus - AM",
  "latitude": -3.095,
  "longitude": -59.982,
  "raio_operacao": 1000,
  "capacidade_maxima": 500,
  "tipos_residuos_aceitos": ["vidro", "aluminio"],
  "horario_funcionamento": "Segunda a sábado, 08h às 18h",
  "status": "ativo",
  "cooperativa_id": 3
}
```

Troque `cooperativa_id` pelos ids reais das cooperativas no seu banco.

## 13. Gerando Quantidade Atual No Inventário Do Ponto

A quantidade atual vem do campo `inventario` do ponto de coleta.

O fluxo correto do sistema é:

1. usuário solicita descarte;
2. cooperativa/admin confirma descarte;
3. o sistema transfere a quantidade confirmada para o inventário do ponto;
4. o painel da cooperativa passa a mostrar a nova ocupação.

### Fluxo Recomendado Para Teste

Crie um usuário comum:

```http
POST /usuarios
```

Body:

```json
{
  "nome": "Usuário Teste",
  "email": "usuario.teste@residuum.com",
  "telefone": "92999990002",
  "senha": "123456"
}
```

Faça login como esse usuário.

Crie item no inventário:

```http
POST /me/inventario
```

Body:

```json
{
  "tipo_residuo": "plastico",
  "quantidade": 850,
  "descricao": "Plásticos separados para descarte"
}
```

Solicite descarte do item:

```http
POST /me/inventario/{item_id}/descartar
```

Body:

```json
{
  "quantidade": 850,
  "ponto_coleta_id": 1,
  "usuario_lat": -3.131633,
  "usuario_long": -60.023437,
  "observacao": "Teste RF021"
}
```

Depois, faça login como a cooperativa responsável ou admin e confirme:

```http
PUT /descarte/{id_descarte}/confirmar
```

Body:

```json
{
  "quantidade_confirmada": 850
}
```

Agora o ponto deve ter `quantidade_atual` próxima de `850`.

## 14. Testando O Endpoint Da RF021

Faça login como a cooperativa responsável pelo ponto.

Chame:

```http
GET /cooperativa/painel/pontos-coleta
```

Resposta esperada:

```json
{
  "cooperativa_id": 2,
  "total_pontos": 1,
  "mensagem": null,
  "pontos": [
    {
      "id": 1,
      "nome": "Ecoponto Centro",
      "endereco": "Av. Eduardo Ribeiro, Centro, Manaus - AM",
      "latitude": -3.131633,
      "longitude": -60.023437,
      "tipo_residuo": ["plastico", "papel", "metal"],
      "quantidade_atual": 850,
      "limite_capacidade": 1000,
      "percentual_preenchimento": 85,
      "status_capacidade": "quase_cheio"
    }
  ]
}
```

## 15. Como Validar Cada Status

Considere um ponto com:

```text
capacidade_maxima = 1000
```

### Status ativo

Quantidade:

```text
600 kg
```

Cálculo:

```text
600 / 1000 * 100 = 60%
```

Resultado esperado:

```json
"status_capacidade": "ativo"
```

### Status quase_cheio

Quantidade:

```text
850 kg
```

Cálculo:

```text
850 / 1000 * 100 = 85%
```

Resultado esperado:

```json
"status_capacidade": "quase_cheio"
```

### Status cheio

Quantidade:

```text
950 kg
```

Cálculo:

```text
950 / 1000 * 100 = 95%
```

Resultado esperado:

```json
"status_capacidade": "cheio"
```

## 16. Testando Isolamento Entre Cooperativas

Esse é um dos testes mais importantes da RF021.

### Cenário

Você tem:

```text
Cooperativa Norte: id 2
Cooperativa Sul: id 3
Ponto A: cooperativa_id 2
Ponto B: cooperativa_id 3
```

Faça login como `coop.norte@residuum.com`.

Chame:

```http
GET /cooperativa/painel/pontos-coleta
```

Resultado correto:

- deve aparecer o Ponto A;
- não deve aparecer o Ponto B.

Faça login como `coop.sul@residuum.com`.

Resultado correto:

- deve aparecer o Ponto B;
- não deve aparecer o Ponto A.

Se uma cooperativa vê ponto da outra, a RF021 falhou.

## 17. Testando Usuário Sem Permissão

Faça login como usuário comum e chame:

```http
GET /cooperativa/painel/pontos-coleta
```

Resultado esperado:

```http
403 Forbidden
```

Resposta esperada:

```json
{
  "detail": "Permissão insuficiente"
}
```

Faça o mesmo sem token.

Resultado esperado:

```http
401 Unauthorized
```

ou erro equivalente de autenticação Bearer.

## 18. Testando Cooperativa Sem Pontos

Crie uma cooperativa sem pontos vinculados.

Faça login com ela e chame:

```http
GET /cooperativa/painel/pontos-coleta
```

Resposta esperada:

```json
{
  "cooperativa_id": 4,
  "total_pontos": 0,
  "mensagem": "Nenhum ponto de coleta vinculado a esta cooperativa.",
  "pontos": []
}
```

## 19. Testando Pelo Painel Visual

Abra:

```text
http://localhost:8000/painel-testes
```

Faça login com uma conta de cooperativa.

Na seção:

```text
Seção 3: Painel da Cooperativa
```

Clique em:

```text
Atualizar Pontos da Cooperativa
```

Valide:

- pontos aparecem em cards;
- pontos ativos ficam destacados em verde;
- pontos quase cheios ficam destacados em amarelo;
- pontos cheios ficam destacados em vermelho;
- pontos inativos ficam destacados em cinza;
- a barra de preenchimento acompanha o percentual.

Observação: essa tela é apenas um painel visual de teste. A RF021 não depende de Google Maps.

## 20. Testando Via cURL

Login:

```powershell
curl -X POST "http://localhost:8000/login" `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"coop.norte@residuum.com\",\"senha\":\"123456\"}"
```

Copie o `access_token`.

Chame o painel:

```powershell
curl -X GET "http://localhost:8000/cooperativa/painel/pontos-coleta" `
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## 21. Testando Via Postman Ou Insomnia

Crie uma request:

```http
GET http://localhost:8000/cooperativa/painel/pontos-coleta
```

Headers:

```http
Authorization: Bearer SEU_TOKEN_AQUI
Content-Type: application/json
```

Envie e valide o JSON retornado.

## 22. Conferindo Se Não Houve Regressão

Depois de testar a RF021, confira os fluxos principais:

### Autenticação

```http
POST /usuarios
POST /login
GET /me
```

### Pontos de coleta

```http
GET /pontos-coleta
GET /pontos-coleta/{ponto_id}
POST /pontos-coleta
PUT /pontos-coleta/{ponto_id}
```

### Inventário do usuário

```http
POST /me/inventario
GET /me/inventario
POST /me/inventario/{item_id}/descartar
```

### Descarte e confirmação

```http
GET /descarte/pendentes
PUT /descarte/{id_descarte}/confirmar
```

### QR Code

```http
POST /qrcode-tokens
GET /qrcode-tokens/{ponto_id}
POST /qrcode-tokens/validar
```

### Geofencing

Teste descarte:

- com latitude/longitude próxima ao ponto;
- com latitude/longitude distante do ponto.

O descarte distante deve ser bloqueado quando não houver QR Code válido.

## 23. Checklist Dos Critérios De Aceite

Use esta lista para validar a task:

```text
[ ] Cooperativa autenticada consegue consultar seus pontos.
[ ] Usuário comum não consegue acessar o endpoint da cooperativa.
[ ] Requisição sem token é bloqueada.
[ ] O endpoint não retorna pontos de outras cooperativas.
[ ] Cada ponto retorna id, nome, endereço, latitude e longitude.
[ ] Cada ponto retorna tipo_residuo.
[ ] Cada ponto retorna quantidade_atual.
[ ] Cada ponto retorna limite_capacidade.
[ ] Cada ponto retorna percentual_preenchimento.
[ ] Cada ponto retorna status_capacidade.
[ ] Percentual é calculado por quantidade_atual / limite * 100.
[ ] Status abaixo de 70% retorna ativo.
[ ] Status entre 70% e 89% retorna quase_cheio.
[ ] Status a partir de 90% retorna cheio.
[ ] Cooperativa sem pontos recebe lista vazia e mensagem adequada.
[ ] Endpoint aparece no Swagger/ReDoc.
[ ] Painel visual exibe pontos e destaca quase cheios/cheios.
[ ] Fluxos de descarte, pontuação, QR Code, geofencing e inventário continuam funcionando.
```

## 24. Problemas Comuns

### Erro: ModuleNotFoundError: No module named 'fastapi'

As dependências não foram instaladas.

Resolva com:

```powershell
pip install -r requirements.txt
```

### Erro ao conectar no banco

Confira:

- PostgreSQL está rodando;
- `DATABASE_URL` está correta;
- usuário, senha, host, porta e database existem;
- migrations foram aplicadas.

Rode:

```powershell
alembic upgrade head
```

### Endpoint retorna 403

O usuário logado provavelmente não tem:

```text
role = cooperativa
```

Promova pelo endpoint admin:

```http
PATCH /admin/usuarios/{usuario_id}/role
```

### Endpoint retorna pontos vazios

Confira se os pontos têm:

```text
cooperativa_id = id da cooperativa logada
```

Você pode validar pelo endpoint admin/listagem de pontos ou diretamente no banco.

### Percentual retorna null

Isso acontece quando o ponto não tem `capacidade_maxima` definida ou a capacidade é zero.

Atualize o ponto com:

```json
{
  "capacidade_maxima": 1000
}
```

## 25. Resultado Esperado Final

Ao final dos testes, você deve conseguir demonstrar que:

- a cooperativa tem uma visão operacional dos seus próprios pontos;
- a resposta contém dados suficientes para exibir mapa/listagem;
- o nível de preenchimento é calculado corretamente;
- pontos quase cheios ou cheios são destacados;
- dados de outras cooperativas não são expostos;
- não foi criada dependência obrigatória de Google Maps;
- os fluxos existentes do Residuum continuam funcionando.
