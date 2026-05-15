# Residuum — Módulo de Inteligência e Logística de Descarte

## Visão Geral

Este repositório contém o **módulo de inteligência e logística** da plataforma **Residuum** — sistema responsável pelo registro, validação e confirmação de descartes de resíduos recicláveis, bem como pela geração automática de pontuação para os usuários. A API foi desenvolvida com foco em regras de negócio claras: validação de localização, verificação do tipo de resíduo aceito e cálculo proporcional de pontos com base no peso real confirmado pela cooperativa.

---

## Tecnologias

| Tecnologia | Versão |
|---|---|
| Python | 3.10+ |
| FastAPI | 0.136+ |
| SQLAlchemy | 2.0+ |
| PostgreSQL | 14+ |
| Pydantic | 2.x |
| Uvicorn | 0.46+ |

---

## Instalação

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd residuum
```

### 2. Criar e ativar o ambiente virtual

```bash
# Criar o venv
python -m venv venv

# Ativar no Windows
venv\Scripts\activate

# Ativar no Linux/macOS
source venv/bin/activate
```

### 3. Instalar as dependências

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary passlib[bcrypt] python-jose python-dotenv
```

Ou, se o arquivo `requirements.txt` já estiver presente:

```bash
pip install -r requirements.txt
```

---

## Configuração do Banco de Dados

### 1. Criar o banco no PostgreSQL

Acesse o `psql` ou o pgAdmin e execute:

```sql
CREATE DATABASE residuum;
```

### 2. Restaurar o script SQL (se fornecido)

```bash
psql -U postgres -d residuum -f script_residuum.sql
```

### 3. Aplicar o schema com Alembic

O projeto usa **Alembic** para versionar mudanças no banco. Toda alteração de modelo (adicionar coluna, criar tabela, etc.) gera uma migration que é aplicada de forma controlada — **não** confie em `Base.metadata.create_all` para evoluir o schema.

#### Aplicar as migrations existentes

Com o banco vazio (recém-criado) e o `.env` configurado, rode:

```bash
alembic upgrade head
```

Isso aplica todas as migrations da pasta `alembic/versions/` em ordem, deixando o banco no estado mais recente.

#### Criar uma nova migration após mudar um modelo

1. Edite o modelo SQLAlchemy em `app/models/` (adicionar coluna, alterar tipo, etc.).
2. Gere a migration automaticamente comparando modelos × banco:

   ```bash
   alembic revision --autogenerate -m "descrição curta da mudança"
   ```

3. **Revise** o arquivo gerado em `alembic/versions/` antes de aplicar — o autogenerate é bom mas não infalível (atenção a renomeações de coluna, que ele interpreta como drop+add).
4. Aplique:

   ```bash
   alembic upgrade head
   ```

#### Comandos úteis

| Comando | Descrição |
|---|---|
| `alembic current` | Mostra a revision atualmente aplicada no banco |
| `alembic history` | Lista todas as migrations e a ordem |
| `alembic downgrade -1` | Reverte a última migration aplicada |
| `alembic downgrade base` | Reverte tudo (volta ao banco vazio) |
| `alembic stamp head` | Marca o banco como atualizado sem rodar migrations (use só se o schema já bate manualmente) |

> **Importante:** o `env.py` do Alembic carrega o `.env` automaticamente e usa `DATABASE_URL` para conectar. Não há `sqlalchemy.url` hardcoded no `alembic.ini`.

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```env
DATABASE_URL=postgresql://postgres:<sua_senha>@localhost:5432/residuum
SECRET_KEY=sua_chave_secreta_aqui
```

> Substitua `<sua_senha>` pela senha do seu usuário PostgreSQL e defina uma `SECRET_KEY` forte para a geração de tokens JWT.

---

## Como Rodar

Com o ambiente virtual ativado e o banco configurado, execute:

```bash
uvicorn app.main:app --reload
```

A API estará disponível em:

- **Base:** `http://127.0.0.1:8000`
- **Documentação interativa (Swagger):** `http://127.0.0.1:8000/docs`
- **Documentação alternativa (ReDoc):** `http://127.0.0.1:8000/redoc`

---

## Fluxo de Teste

O fluxo principal do módulo envolve duas etapas: **registro** e **confirmação** do descarte.

### Etapa 1 — Registrar um descarte (status: `pendente`)

Envie uma requisição `POST /descarte/` com o payload abaixo. O sistema valida a quantidade, o tipo de resíduo (`garrafa pet`) e a proximidade do ponto de coleta antes de salvar.

```json
POST /descarte/
{
  "quantidade": 5.0,
  "tipo_residuo": "garrafa pet",
  "observacao": "Sacos separados por cor",
  "usuario_id": 1,
  "usuario_lat": -23.5505,
  "usuario_long": -46.6333,
  "ponto_lat": -23.5510,
  "ponto_long": -46.6340
}
```

**Resposta esperada:** descarte salvo com `status: "pendente"`.

### Etapa 2 — Confirmar o descarte e gerar pontos

A cooperativa confirma o peso real recebido. Envie uma requisição `PUT /descarte/{id}/confirmar`:

```json
PUT /descarte/1/confirmar
{
  "quantidade_confirmada": 4.5
}
```

**Regra de pontuação:** `10 pontos por kg confirmado`.  
No exemplo acima: **4,5 kg × 10 = 45 pontos** creditados ao usuário.

> Se a cooperativa confirmar um peso menor que o declarado, os pontos são calculados apenas sobre o peso real confirmado, garantindo integridade no sistema de recompensas.

---

## Estrutura do Projeto

```
residuum/
├── alembic/
│   ├── versions/                # Scripts de migration versionados
│   ├── env.py                   # Bootstrap do Alembic (lê .env e Base.metadata)
│   └── script.py.mako           # Template usado para gerar novas migrations
├── app/
│   ├── core/
│   │   ├── decorators.py        # Decorator @public para marcar rotas sem auth
│   │   └── security.py          # Geração e validação de tokens JWT
│   ├── dependencies/
│   │   └── auth.py              # get_current_user e require_role
│   ├── models/
│   │   ├── descarte.py          # Modelo ORM da tabela de descartes
│   │   ├── endereco.py          # Modelo ORM da tabela de endereços
│   │   └── usuario.py           # Modelo ORM da tabela de usuários
│   ├── routes/
│   │   ├── auth.py              # Endpoints de autenticação (login/registro)
│   │   └── descarte.py          # Endpoints de descarte e confirmação
│   ├── schemas/
│   │   └── descarte.py          # Schemas Pydantic para validação de entrada/saída
│   ├── services/
│   │   ├── localizacao_service.py   # Validação de proximidade geográfica
│   │   ├── pontuacao_service.py     # Cálculo de pontos por kg confirmado
│   │   └── validacao_service.py     # Validação de quantidade e tipo de resíduo
│   ├── database.py              # Configuração da engine e sessão do SQLAlchemy
│   └── main.py                  # Ponto de entrada da aplicação FastAPI
├── alembic.ini                  # Configuração do Alembic
├── docker-compose.yml           # Postgres local para desenvolvimento
├── requirements.txt
├── .env                         # Variáveis de ambiente (não versionar)
└── README.md
```

---

## Branch de Desenvolvimento

Esta entrega está na branch `feature/logica-descarte-pontuacao`, contendo toda a lógica de:

- Registro de descartes com validações de negócio
- Confirmação de descartes pela cooperativa
- Cálculo proporcional de pontuação (10 pts/kg)
- Serviços auxiliares de validação e geolocalização


## Atualizações Backend
Esta entrega está na branch `feature/validacao-descarte-kaue`, contendo toda a lógica de:
### Validação de descarte
- Validação de quantidade mínima e máxima;
- Validação de tipos de resíduos aceitos;
- Bloqueio de descartes inválidos.

### Transferência de resíduos
- Criação da lógica inicial de transferência;
- Integração da transferência no fluxo de descarte.
