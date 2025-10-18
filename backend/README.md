# Backend Setup - Alpha Insights Chat

## 📋 Pré-requisitos
- Python 3.8+
- pip (gerenciador de pacotes Python)

## ⚡ Setup Rápido

### 1. Navegue para o diretório do backend
```bash
cd backend
```

### 2. Crie um ambiente virtual (recomendado)
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# ou source venv/bin/activate  # Linux/Mac
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
O arquivo `.env` já contém as chaves de API fornecidas. Se precisar alterá-las:
```
DRIVEBOT_API_KEY=sua_chave_aqui
ALPHABOT_API_KEY=sua_chave_aqui
```

### 5. Execute o servidor
```bash
python app.py
```

O backend estará disponível em: http://localhost:5000

## 🧪 Testando a API

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Teste do Chat
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "alphabot", 
    "message": "Olá, como você pode me ajudar?"
  }'
```

## 📁 Estrutura dos Arquivos
```
backend/
├── app.py              # Aplicação Flask principal
├── requirements.txt    # Dependências Python
├── .env               # Variáveis de ambiente (NÃO commitar!)
└── README.md          # Este arquivo
```

## 🔒 Segurança
- O arquivo `.env` contém chaves de API sensíveis
- Certifique-se de que está no `.gitignore`
- Em produção, use variáveis de ambiente do servidor

## 🐛 Troubleshooting
- **Erro de importação**: Verifique se todas as dependências foram instaladas
- **Erro de API**: Verifique se as chaves de API estão corretas no `.env`
- **CORS Error**: O CORS está configurado para aceitar requisições do frontend