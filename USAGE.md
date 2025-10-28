# Guia de Uso - Sistema de Localização de IPs

## Início Rápido

### 1. Instalação

```bash
# Clone o repositório
git clone <seu-repositorio>
cd localizador

# Crie o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configuração

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas credenciais
nano .env  # ou use seu editor preferido
```

**Variáveis obrigatórias:**
- `TOKEN_API_TELEGRAM` - Token do seu bot (obtenha com @BotFather)
- `TELEGRAM_CHAT_ID` - ID do chat para notificações (obtenha com @userinfobot)

### 3. Executar o Sistema

**Opção 1: Executar tudo de uma vez**
```bash
python run_all.py
```

**Opção 2: Executar separadamente**
```bash
# Terminal 1 - Servidor Flask
python app.py

# Terminal 2 - Bot do Telegram
python bot.py
```

## Exemplos de Uso

### Bot do Telegram

#### 1. Iniciar o bot
Abra o Telegram, procure seu bot e envie:
```
/start
```

Você verá um menu interativo com botões.

#### 2. Ver estatísticas
```
/stats
```

**Resposta esperada:**
```
📊 Estatísticas do Sistema

📝 Total de registros: 150
🌐 IPs únicos: 45
🏙️ Cidades únicas: 20
🌍 Países únicos: 8

⏰ Primeiro registro: 20/01/2025 08:00:00
⏰ Último registro: 27/01/2025 10:25:00
```

#### 3. Buscar por IP
```
/buscar_ip 192.168.1.1
```

**Resposta esperada:**
```
Encontrados 3 registro(s) para IP 192.168.1.1:

Data: 27/01/2025 10:00:00
IP: 192.168.1.1
Cidade: São Paulo
País: Brazil
-------------------
[...]
```

#### 4. Buscar por cidade
```
/buscar_cidade São Paulo
```

**Resposta esperada:**
```
Encontrados 25 registro(s) para cidade São Paulo:

Data: 27/01/2025 10:15:00
IP: 200.150.100.50
País: Brazil
-------------------
[...]
```

#### 5. Ver últimos registros
```
/ultimos 5
```

Mostra os 5 registros mais recentes.

### API REST (Flask)

#### 1. Página inicial
Abra o navegador:
```
http://localhost:5000
```

Você verá uma página com estatísticas do sistema.

#### 2. Health Check
```bash
curl http://localhost:5000/health
```

**Resposta:**
```json
{
  "status": "ok",
  "timestamp": "2025-01-27T10:30:00.123456",
  "notifications_enabled": true
}
```

#### 3. Estatísticas (JSON)
```bash
curl http://localhost:5000/api/stats
```

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

#### 4. Tracking Pixel
Insira em uma página HTML:
```html
<img src="http://seu-servidor:5000/path/imagem.png" width="1" height="1" />
```

Cada acesso será registrado automaticamente.

### Gerador de Mapas

```bash
python main.py
```

**Exemplo de uso:**
```
Digite um endereço ou coordenadas (lat,lon): -23.5505, -46.6333
Endereço: São Paulo, Brasil
Latitude: -23.5505, Longitude: -46.6333
✔ Mapa gerado em: map.html
```

O arquivo `map.html` será aberto automaticamente no navegador.

## Casos de Uso Comuns

### 1. Monitoramento de site
Configure o tracking pixel em suas páginas web para monitorar visitantes:

```html
<img src="http://seu-servidor:5000/path/visit.gif"
     width="1" height="1" style="display:none;" />
```

### 2. Links rastreáveis
Crie links que redirecionam após registrar o acesso:

```html
<a href="http://seu-servidor:5000/path/link-email">Clique aqui</a>
```

### 3. Notificações em tempo real
Ative as notificações no `.env`:
```env
ENABLE_TELEGRAM_NOTIFICATIONS=true
TELEGRAM_CHAT_ID=seu_chat_id
```

Você receberá mensagens no Telegram para cada novo acesso.

### 4. Análise de logs via bot
Use o bot para consultar rapidamente:
- Quais IPs acessaram seu sistema
- De quais cidades vieram os acessos
- Quantos países diferentes acessaram

## Integração com Log Manager

Para usar o `log_manager.py` em seus próprios scripts:

```python
from log_manager import log_manager

# Adicionar um registro manualmente
data = {
    "ip": "192.168.1.1",
    "city": "São Paulo",
    "country": "Brazil",
    "ua": "Mozilla/5.0..."
}
log_manager.adicionar_registro(data)

# Buscar registros
registros = log_manager.buscar_por_ip("192.168.1.1")
for r in registros:
    print(f"{r['timestamp']} - {r['city']}")

# Obter estatísticas
stats = log_manager.obter_estatisticas()
print(f"Total de registros: {stats['total']}")
```

## Solução de Problemas

### Bot não responde
1. Verifique se o TOKEN_API_TELEGRAM está correto
2. Certifique-se de que o bot está rodando (`python bot.py`)
3. Verifique os logs para erros

### Notificações não chegam
1. Confirme que `ENABLE_TELEGRAM_NOTIFICATIONS=true`
2. Verifique se o `TELEGRAM_CHAT_ID` está correto
3. Certifique-se de que iniciou uma conversa com o bot

### Flask retorna erro 500
1. Verifique os logs do Flask
2. Teste a API de geolocalização: `curl http://ip-api.com/json/8.8.8.8`
3. Verifique permissões de escrita nos arquivos log.txt e log.json

### Geolocalização não funciona
A API gratuita do ip-api.com tem limitações:
- Máximo de 45 requisições por minuto
- Não funciona para IPs locais (127.0.0.1, 192.168.x.x)

## Dicas e Truques

### 1. Consultar logs rapidamente
```bash
# Ver últimas 10 linhas do log
tail -10 log.txt

# Filtrar por IP específico
grep "192.168.1.1" log.txt
```

### 2. Limpar logs antigos
```bash
# Backup antes de limpar
cp log.txt log_backup.txt
cp log.json log_backup.json

# Limpar logs
> log.txt
echo "[]" > log.json
```

### 3. Executar em produção
Use um gerenciador de processos como `supervisor` ou `systemd`:

```ini
# /etc/supervisor/conf.d/localizador.conf
[program:localizador-flask]
command=/caminho/venv/bin/python /caminho/app.py
directory=/caminho/localizador
autostart=true
autorestart=true

[program:localizador-bot]
command=/caminho/venv/bin/python /caminho/bot.py
directory=/caminho/localizador
autostart=true
autorestart=true
```

## Próximos Passos

1. Configure um domínio para o servidor Flask
2. Adicione HTTPS com Let's Encrypt
3. Implemente autenticação na API
4. Adicione mais comandos ao bot
5. Crie dashboards de visualização

## Recursos Adicionais

- Documentação do python-telegram-bot: https://docs.python-telegram-bot.org/
- Documentação do Flask: https://flask.palletsprojects.com/
- API de Geolocalização: https://ip-api.com/docs/
