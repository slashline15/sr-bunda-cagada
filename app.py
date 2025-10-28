# app.py
from flask import Flask, jsonify, request
import requests
import os
import logging
from datetime import datetime
import dotenv

from log_manager import log_manager

# Configuração básica de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
dotenv.load_dotenv()

app = Flask(__name__)

# Configurações
TELEGRAM_BOT_TOKEN = os.getenv("TOKEN_API_TELEGRAM")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # ID do chat para notificações
ENABLE_NOTIFICATIONS = os.getenv("ENABLE_TELEGRAM_NOTIFICATIONS", "false").lower() == "true"

# ==================== FUNÇÕES AUXILIARES ====================

def obter_geolocalizacao(ip: str) -> dict:
    """Obtém informações de geolocalização para um IP."""
    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip}",
            timeout=5,
            params={"fields": "status,message,country,regionName,city,zip,lat,lon,org,query"}
        )
        geo = response.json()

        if geo.get("status") == "success":
            return geo
        else:
            logger.warning(f"Falha na geolocalização para {ip}: {geo.get('message', 'Unknown')}")
            return {}
    except Exception as e:
        logger.error(f"Erro ao obter geolocalização para {ip}: {e}")
        return {}


def enviar_notificacao_telegram(data: dict) -> bool:
    """Envia notificação para o Telegram sobre novo acesso."""
    if not ENABLE_NOTIFICATIONS or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    try:
        mensagem = (
            f"🔔 *Novo Acesso Detectado*\n\n"
            f"🌐 *IP:* `{data.get('ip', 'N/A')}`\n"
            f"📍 *Localização:* {data.get('city', 'N/A')}, {data.get('country', 'N/A')}\n"
            f"🏢 *Provedor:* {data.get('org', 'N/A')}\n"
            f"🕒 *Data/Hora:* {datetime.fromisoformat(data['timestamp']).strftime('%d/%m/%Y %H:%M:%S')}\n"
            f"💻 *User-Agent:* {data.get('ua', 'N/A')[:50]}..."
        )

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "Markdown"
        }

        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()

        logger.info(f"Notificação enviada para Telegram: {data.get('ip')}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar notificação Telegram: {e}")
        return False


# ==================== ROTAS ====================

@app.route("/")
def index():
    """Página inicial com informações sobre o sistema."""
    stats = log_manager.obter_estatisticas()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sistema de Localização de IPs</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; }}
            .stats {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 20px; }}
            .stat-box {{ background: #f0f0f0; padding: 20px; border-radius: 5px; text-align: center; }}
            .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
            .stat-label {{ color: #666; margin-top: 5px; }}
            .info {{ margin-top: 30px; padding: 15px; background: #e3f2fd; border-left: 4px solid #2196f3; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌍 Sistema de Localização de IPs</h1>
            <p>Sistema ativo e monitorando acessos.</p>

            <h2>Estatísticas</h2>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number">{stats.get('total', 0)}</div>
                    <div class="stat-label">Total de Registros</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{stats.get('ips_unicos', 0)}</div>
                    <div class="stat-label">IPs Únicos</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{stats.get('cidades_unicas', 0)}</div>
                    <div class="stat-label">Cidades Únicas</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{stats.get('paises_unicos', 0)}</div>
                    <div class="stat-label">Países Únicos</div>
                </div>
            </div>

            <div class="info">
                <strong>ℹ️ Informação:</strong> Use o bot do Telegram para consultar os registros.
            </div>
        </div>
    </body>
    </html>
    """
    return html


@app.route("/health")
def health():
    """Endpoint de health check."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "notifications_enabled": ENABLE_NOTIFICATIONS
    })


@app.route("/api/stats")
def api_stats():
    """Retorna estatísticas em formato JSON."""
    return jsonify(log_manager.obter_estatisticas())


@app.route("/path:fake")
@app.route("/path/<path:fake>")
def catch(fake=""):
    """
    Captura requisições e registra informações de geolocalização.
    Retorna 204 No Content (útil para tracking pixel invisível).
    """
    # Obter IP do cliente (considera proxies)
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()

    # Garantir que o IP não seja None
    ip = ip or "unknown"

    ua = request.headers.get("User-Agent", "Unknown")
    referer = request.headers.get("Referer", "Direct")

    # Obter informações de geolocalização
    geo = obter_geolocalizacao(ip)

    # Montar dicionário de dados
    data = {
        "timestamp": datetime.now().isoformat(),
        "ip": ip,
        "ua": ua,
        "referer": referer,
        "path": fake,
        "city": geo.get("city"),
        "region": geo.get("regionName"),
        "country": geo.get("country"),
        "loc": f"{geo.get('lat')},{geo.get('lon')}" if geo.get('lat') and geo.get('lon') else None,
        "org": geo.get("org"),
        "postal": geo.get("zip")
    }

    # Salvar no log usando o gerenciador
    log_manager.adicionar_registro(data)

    # Enviar notificação para Telegram (se habilitado)
    enviar_notificacao_telegram(data)

    logger.info(f"Acesso capturado: {ip} - {data.get('city', 'N/A')}, {data.get('country', 'N/A')}")

    # Retornar 204 No Content (tracking pixel invisível)
    return ("", 204)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

