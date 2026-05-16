# Residuum — Frontend Web

## Visão Geral

Este repositório contém o frontend web do sistema **Residuum**, uma plataforma voltada para gestão, rastreio e gamificação do descarte correto de resíduos recicláveis.

O frontend foi desenvolvido em **React + Vite** e se comunica com a API backend do Residuum, construída em **FastAPI**. A interface permite que usuários cadastrem resíduos em seu inventário, realizem descartes em pontos de coleta, acompanhem sua pontuação e histórico, enquanto administradores podem gerenciar pontos, confirmar descartes e acompanhar os inventários dos pontos de coleta.

---

## Tecnologias Utilizadas

| Tecnologia | Finalidade |
|---|---|
| React | Construção da interface |
| Vite | Ambiente de desenvolvimento e build |
| Axios | Comunicação com a API backend |
| React Router DOM | Navegação entre telas |
| Leaflet | Mapa interativo |
| React Leaflet | Integração do Leaflet com React |
| OpenStreetMap | Fonte dos mapas |
| Lucide React | Ícones da interface |
| CSS | Estilização do sistema |

---

## Pré-requisitos

Antes de rodar o projeto, é necessário ter instalado:

- Node.js LTS
- npm
- Git

Verifique as instalações com:

```bash
node -v
npm -v
git -v
```

---

## Instalação

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio-frontend>
cd <nome-da-pasta-do-frontend>
```

Exemplo:

```bash
git clone https://github.com/Residuum/frontend-residuum.git
cd frontend-residuum
```

### 2. Instalar as dependências

```bash
npm install
```

---

## Configuração do Ambiente

Crie um arquivo chamado `.env` na raiz do projeto frontend:

```txt
.env
```

Adicione a URL da API backend:

```env
VITE_API_URL=http://localhost:8000
```

Se o backend estiver rodando em outro endereço, altere a URL conforme necessário.

Exemplo:

```env
VITE_API_URL=https://api.residuum.com
```

---

## Como Rodar o Projeto

Com as dependências instaladas e o backend rodando, execute:

```bash
npm run dev
```

O frontend ficará disponível em:

```txt
http://localhost:5173
```

---

## Backend Necessário

Este frontend depende da API backend do Residuum.

Durante o desenvolvimento local, mantenha o backend rodando em:

```txt
http://localhost:8000
```

Comando comum para iniciar o backend:

```bash
python -m uvicorn app.main:app --reload
```

A documentação da API pode ser acessada em:

```txt
http://localhost:8000/docs
```

---

## Funcionalidades Implementadas

### Usuário comum

- Cadastro de usuário
- Login com autenticação JWT
- Exibição do nome do usuário logado
- Visualização da pontuação acumulada
- Perfil completo do usuário
- Cadastro e atualização de endereço
- Inventário pessoal de resíduos
- Cadastro de resíduos no inventário
- Edição e remoção de itens do inventário
- Descarte parcial a partir do inventário
- Validação por localização
- Validação por QR Code
- Histórico de descartes
- Visualização de pontos de coleta
- Mapa interativo com Leaflet e OpenStreetMap
- Filtro de pontos por tipo de resíduo
- Filtro de pontos por distância

### Administrador

- Visualização de todos os pontos de coleta, incluindo pontos inativos
- Cadastro de pontos de coleta
- Edição de pontos de coleta
- Reativação de pontos inativos
- Visualização de descartes pendentes
- Confirmação de descartes
- Atualização do inventário do ponto após confirmação
- Atualização da pontuação do usuário após confirmação
- Geração de QR Code
- Listagem de QR Codes ativos
- Validação de QR Code
- Histórico geral de descartes

---

## Fluxo Principal do Sistema

### Fluxo do usuário

```txt
Login
↓
Cadastro de resíduos no inventário
↓
Escolha de item para descarte
↓
Seleção de ponto de coleta
↓
Validação por GPS ou QR Code
↓
Descarte fica pendente
↓
Admin confirma
↓
Inventário do usuário é atualizado
↓
Pontuação é creditada
```

### Fluxo do administrador

```txt
Login como admin
↓
Gerenciamento de pontos de coleta
↓
Visualização de descartes pendentes
↓
Confirmação da quantidade real coletada
↓
Sistema atualiza pontuação do usuário
↓
Sistema atualiza inventário do ponto de coleta
```

---

## Estrutura do Projeto

```txt
frontend/
├── public/
├── src/
│   ├── assets/
│   ├── components/
│   ├── contexts/
│   ├── pages/
│   ├── services/
│   ├── styles/
│   ├── App.jsx
│   └── main.jsx
├── .env
├── .gitignore
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
└── README.md
```

---

## Scripts Disponíveis

### Rodar em desenvolvimento

```bash
npm run dev
```

### Gerar build de produção

```bash
npm run build
```

### Visualizar build localmente

```bash
npm run preview
```

---

## Variáveis de Ambiente

O projeto utiliza a variável abaixo:

```env
VITE_API_URL=http://localhost:8000
```

Essa variável define a URL base do backend.

O arquivo responsável pela comunicação com a API fica em:

```txt
src/services/api.js
```

---

## Mapa

O sistema utiliza **Leaflet + OpenStreetMap** para exibir os pontos de coleta no mapa.

Essa escolha foi feita porque:

- não exige chave de API;
- não exige billing;
- funciona bem para MVP;
- permite marcadores;
- permite popups;
- permite exibir o raio de operação dos pontos de coleta.

---

## Integração com a API

As principais rotas consumidas pelo frontend são:

```txt
POST /usuarios
POST /login
GET /me
GET /perfil
PUT /me/endereco

POST /me/inventario
GET /me/inventario
PUT /me/inventario/{item_id}
DELETE /me/inventario/{item_id}
POST /me/inventario/{item_id}/descartar

GET /pontos
GET /pontos-coleta
POST /pontos-coleta
GET /pontos-coleta/{ponto_id}
PUT /pontos-coleta/{ponto_id}

POST /descarte/
GET /descarte/historico
GET /descarte/historico/geral
GET /descarte/pendentes
PUT /descarte/{id_descarte}/confirmar

POST /qrcode-tokens
GET /qrcode-tokens/{ponto_id}
POST /qrcode-tokens/validar
```

---

## Observações Importantes

### Não subir `node_modules`

A pasta `node_modules` não deve ser enviada ao GitHub.

Garanta que o arquivo `.gitignore` contenha:

```gitignore
node_modules/
dist/
.env
.DS_Store
```

### Não subir `.env`

O arquivo `.env` não deve ser enviado ao GitHub, pois pode conter URLs ou configurações sensíveis.

Caso necessário, crie um arquivo `.env.example` com:

```env
VITE_API_URL=http://localhost:8000
```

---

## Dependências Principais

As principais dependências estão declaradas no `package.json`.

Caso o projeto seja baixado em outra máquina, basta rodar:

```bash
npm install
```

O npm instalará automaticamente tudo que for necessário.

---

## Status do Projeto

Funcionalidades principais concluídas:

- Autenticação
- Perfil completo
- Inventário do usuário
- Descarte via inventário
- Pontos de coleta
- Filtros por tipo e distância
- Mapa interativo
- Histórico de descartes
- Confirmação de descarte
- Pontuação
- Inventário do ponto de coleta
- Área administrativa
- QR Code
