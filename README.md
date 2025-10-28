# Sistema de Localização de IPs

Sistema completo para rastreamento e geolocalização de endereços IP com interface de bot do Telegram e servidor web Flask.

## Características

- **Bot do Telegram** com interface inline e comandos interativos
- **Servidor Flask** para captura de acessos e geolocalização
- **Notificações em tempo real** via Telegram (opcional)
- **Armazenamento dual** em formato TXT e JSON
- **Estatísticas detalhadas** de acessos
- **API REST** para consulta de dados

## Arquitetura

```
localizador/
├── app.py              # Servidor Flask para captura de IPs
├── bot.py              # Bot do Telegram
├── log_manager.py      # Módulo compartilhado de gerenciamento de logs
├── main.py             # Gerador de mapas com Folium
├── log.txt             # Arquivo de log (formato texto)
├── log.json            # Arquivo de log (formato JSON)
└── .env                # Variáveis de ambiente
```

## Instalação

### 1. Clone o repositório

```bash
git clone <seu-repositorio>
cd localizador
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install python-telegram-bot flask requests python-dotenv folium geopy
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` e preencha as variáveis obrigatórias:

```env
TOKEN_API_TELEGRAM=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
ENABLE_TELEGRAM_NOTIFICATIONS=true
```

## Uso

### Iniciar o Bot do Telegram

```bash
python bot.py
```

### Iniciar o Servidor Flask

```bash
python app.py
```

O servidor estará disponível em `http://localhost:5000`

### Comandos do Bot

- `/start` - Menu principal com botões inline
- `/stats` - Ver estatísticas do sistema
- `/buscar_ip <ip>` - Buscar registros por IP
- `/buscar_cidade <cidade>` - Buscar registros por cidade
- `/ultimos [n]` - Ver últimos N registros (padrão: 5, máx: 10)
- `/hello` - Saudação

### Endpoints da API

#### GET `/`
Página inicial com estatísticas

#### GET `/health`
Health check do sistema

**Resposta:**
```json
{
  "status": "ok",
  "timestamp": "2025-01-27T10:30:00",
  "notifications_enabled": true
}
```

#### GET `/api/stats`
Estatísticas em formato JSON

**Resposta:**
```json
{
  "total": 150,
  "ips_unicos": 45,
  "cidades_unicas": 20,
  "paises_unicos": 8,
  "primeiro_registro": "2025-01-20T08:00:00",
  "ultimo_registro": "2025-01-27T10:25:00"
}
```

#### GET `/path/<qualquer_path>`
Endpoint de captura (tracking pixel)

Retorna `204 No Content` e registra:
- IP do cliente
- User-Agent
- Referer
- Localização geográfica
- Provedor (ISP)

## Log Manager

O módulo `log_manager.py` fornece uma interface unificada para gerenciamento de logs:

```python
from log_manager import log_manager

# Adicionar registro
log_manager.adicionar_registro(data)

# Ler todos os registros
registros = log_manager.ler_registros()

# Buscar por IP
encontrados = log_manager.buscar_por_ip("192.168.1.1")

# Buscar por cidade
encontrados = log_manager.buscar_por_cidade("São Paulo")

# Obter últimos registros
ultimos = log_manager.obter_ultimos(5)

# Obter estatísticas
stats = log_manager.obter_estatisticas()
```

## Notificações do Telegram

Quando habilitadas (`ENABLE_TELEGRAM_NOTIFICATIONS=true`), o sistema envia notificações em tempo real para o chat configurado sempre que um novo acesso é detectado.

**Formato da notificação:**
```
🔔 Novo Acesso Detectado

🌐 IP: 192.168.1.1
📍 Localização: São Paulo, Brazil
🏢 Provedor: ISP Name
🕒 Data/Hora: 27/01/2025 10:30:00
💻 User-Agent: Mozilla/5.0...
```

## Gerador de Mapas

O arquivo `main.py` permite gerar mapas interativos usando coordenadas ou endereços:

```bash
python main.py
```

Digite um endereço ou coordenadas (lat,lon) e um mapa HTML será gerado automaticamente.

## Segurança

- O sistema utiliza variáveis de ambiente para dados sensíveis
- IPs são processados considerando proxies (X-Forwarded-For)
- Logging configurado para rastreabilidade
- Endpoints de API sem autenticação (adicione se necessário)

## Tecnologias Utilizadas

- **Python 3.8+**
- **python-telegram-bot** - Interface com Telegram
- **Flask** - Servidor web
- **Requests** - Cliente HTTP
- **Folium** - Geração de mapas
- **GeoPy** - Geocodificação
- **python-dotenv** - Gerenciamento de variáveis de ambiente

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto é fornecido "como está" para fins educacionais.
## Avisos Legais

Este sistema deve ser usado apenas para fins legítimos e autorizados. O rastreamento de IPs deve estar em conformidade com leis locais de privacidade (LGPD, GDPR, etc.).
---

> "Quando o a neve cair e os ventos brancos soprarem, o lobo solitário morre. A alcateia sobrevive. O inverno está chegando.

