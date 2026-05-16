# 🚀 Quick Start - Painel de Testes Residuum

## 1. Iniciar o Servidor

```bash
cd "c:\Users\HERICK LEAL\Desktop\residium-entrega-final"

# Ativar venv (PowerShell)
. .\.venv\Scripts\Activate.ps1

# Rodar o servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

O servidor estará em: **http://localhost:8000**

---

## 2. Acessar o Painel de Testes

Abra no navegador:
```
http://localhost:8000/painel-testes
```

---

## 3. Teste Completo (5 minutos)

### Passo 1: Criar Ponto de Coleta (Uma vez)
Acesse o Swagger: `http://localhost:8000/docs`

1. Vá para `POST /pontos-coleta`
2. Click "Try it out"
3. Cole o JSON:
```json
{
  "nome": "Ponto Centro São Paulo",
  "endereco": "Av. Paulista, 1000, São Paulo",
  "latitude": -23.550520,
  "longitude": -46.633309,
  "raio_operacao": 1000
}
```
4. Execute (response dirá `"id": 1`)

### Passo 2: No Painel de Testes
1. **Seção 1 - Simulador do Usuário:**
   - Preencha: Nome, Email, Senha (qualquer uma)
   - Clique "Registrar/Fazer Login"
   - Deve aparecer: ✅ Autenticado como...

2. **Registrar Descarte:**
   - Peso: 5.5 (padrão ok)
   - Tipo: Garrafa PET
   - ID Ponto: 1
   - Clique "✅ GPS Perto (Válido)"
   - Clique "🚀 Enviar Descarte"
   - Deve aparecer: ✅ Descarte registrado com sucesso

### Passo 3: Confirmar Descarte (Como Admin)
3. **Seção 2 - Simulador da Cooperativa:**
   - Clique "🔄 Atualizar Descartes Pendentes"
   - Deve aparecer um card com o descarte
   - No input, coloque: 5.0 (confirmamos 5kg dos 5.5)
   - Clique "✅ Confirmar"
   - Deve aparecer: ✅ Descarte confirmado! 50 pontos gerados!

### Passo 4: Ver Resultado
4. **Seção 3 - Painel de Auditoria:**
   - Clique "🔄 Atualizar Dados"
   - **Pontuação:** Deve aparecer **50 pts** (5kg × 10 pts/kg)
   - **Estoque:** Deve aparecer `garrafa pet: 5.5`

---

## 4. Testes de Validação

### ❌ Teste GPS Longe (Bloqueado)
1. Clique "❌ GPS Longe (Inválido)"
2. Tente "Enviar Descarte"
3. Resultado: **403 - Muito longe do ponto de coleta**

### 🎫 Teste QR Code (Opcional)
1. Clique "🔄 Gerar QR Code Mock"
2. Limpe o GPS (não necessário com QR)
3. Envie descarte
4. Resultado: ✅ Aceito como validação presencial

---

## 5. Endpoints Principais

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/usuarios` | Criar usuário |
| POST | `/login` | Fazer login (retorna token + usuario_id) |
| GET | `/me` | Dados do usuário logado |
| POST | `/descarte/` | Registrar descarte (com GPS ou QR) |
| GET | `/descarte/pendentes` | Listar pendentes (admin) |
| PUT | `/descarte/{id}/confirmar` | Confirmar e calcular pontos (admin) |
| POST | `/pontos-coleta` | Criar ponto (admin) |
| GET | `/pontos-coleta` | Listar pontos |
| GET | `/pontos-coleta/{id}` | Detalhes do ponto |
| POST | `/qrcode-tokens` | Gerar token (admin) |
| POST | `/qrcode-tokens/validar` | Validar token |

---

## 6. Dados de Teste Pré-Configurados

**Usuário Cliente:**
- Nome: João Silva
- Email: joao@example.com
- Senha: senha123

**Ponto de Coleta:**
- ID: 1
- Nome: Ponto Centro
- Coordenadas: -23.550520, -46.633309 (São Paulo)
- Raio: 1000m

---

## 7. Troubleshooting

| Problema | Solução |
|----------|---------|
| "Autenticação pendente" | Clique "Registrar/Fazer Login" na Seção 1 |
| "Muito longe do ponto" | Use o botão "✅ GPS Perto" |
| Descartes não aparecem | Clique "🔄 Atualizar Descartes Pendentes" |
| Pontuação não atualiza | Clique "🔄 Atualizar Dados" na Seção 3 |
| Token JWT inválido | Clique "❌ Limpar Token" e faça login novamente |

---

## 8. Debugging

**Ver logs do servidor:**
```bash
# Terminal com uvicorn deve mostrar:
# [GET] /painel-testes - 200
# [POST] /descarte/ - 201
# [PUT] /descarte/1/confirmar - 200
```

**Ver logs do navegador (F12 - Console):**
```javascript
// Você verá as requisições fetch sendo executadas
// Erros aparecem em vermelho
```

---

## 9. Resetar Tudo (Se Necessário)

```sql
-- No banco PostgreSQL:
DELETE FROM qrcode_token;
DELETE FROM descarte;
DELETE FROM ponto_coleta;
DELETE FROM usuario WHERE email = 'joao@example.com';
```

Depois:
1. Recrie o ponto de coleta via Swagger
2. Refaça o teste completo

---

**Boa demonstração! 🎉**
