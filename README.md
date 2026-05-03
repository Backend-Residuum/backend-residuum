# Residium — Módulo de Inteligência e Logística de Descarte

## Visão Geral

Este repositório contém o **módulo de inteligência e logística** da plataforma **Residium** — sistema responsável pelo registro, validação e confirmação de descartes de resíduos recicláveis, bem como pela geração automática de pontuação para os usuários. A API foi desenvolvida com foco em regras de negócio claras: validação de localização, verificação do tipo de resíduo aceito e cálculo proporcional de pontos com base no peso real confirmado pela cooperativa.

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
cd residium
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
CREATE DATABASE residum;
```

### 2. Restaurar o script SQL (se fornecido)

```bash
psql -U postgres -d residum -f script_residum.sql
```

### 3. Aplicar as colunas necessárias na tabela de descarte

Caso o banco já exista de uma versão anterior, adicione as colunas manualmente:

```sql
ALTER TABLE descarte ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pendente';
ALTER TABLE descarte ADD COLUMN IF NOT EXISTS usuario_id INTEGER;
ALTER TABLE descarte ADD COLUMN IF NOT EXISTS quantidade_confirmada FLOAT;
```

> **Nota:** As migrações são aplicadas automaticamente ao iniciar a API (`Base.metadata.create_all`), mas em bancos pré-existentes os `ALTER TABLE` acima garantem a compatibilidade.

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```env
DATABASE_URL=postgresql://postgres:<sua_senha>@localhost:5432/residum
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
residium/
├── app/
│   ├── core/
│   │   └── security.py          # Geração e validação de tokens JWT
│   ├── dependencies/
│   │   └── auth.py              # Injeção de dependência do usuário autenticado
│   ├── models/
│   │   ├── descarte.py          # Modelo ORM da tabela de descartes
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
