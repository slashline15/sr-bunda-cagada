export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    try {
      // Roteamento
      if (path === "/" || path === "/health") return ok("LexKing Tracker up 👑");

      if (path.startsWith("/gen/")) {
        const name = decodeURIComponent(path.split("/").pop() || "");
        if (!name || name.length > 50) return bad(400, "Nome inválido");
        const code = shortCode();
        // nada a gravar aqui; o log só existe quando /t/<code> é acessado
        const base = `${url.protocol}//${url.host}`;
        const link = `${base}/t/${code}`;
        const mapa = `${base}/map/${code}`;
        return json({ name, code, link, mapa });
      }

      if (path.startsWith("/t/")) {
        const code = (path.split("/").pop() || "").trim();
        if (!code || code.length > 16) return bad(400, "Link inválido");

        // IP real atrás da Cloudflare
        const ip =
          request.headers.get("cf-connecting-ip") ||
          request.headers.get("x-real-ip") ||
          (request.headers.get("x-forwarded-for") || "").split(",")[0].trim() ||
          "0.0.0.0";

        const ua = request.headers.get("user-agent") || "Unknown";
        const cf = request.cf || {}; // geo rico do edge

        // Guarda (sem travar a resposta)
        const data = {
          code,
          name: url.searchParams.get("n")?.slice(0, 50) || null, // opcional: /t/<code>?n=amigo
          ip,
          ua,
          city: cf.city || null,
          region: cf.region || cf.regionCode || null,
          country: cf.country || null,
          lat: safeNum(cf.latitude),
          lon: safeNum(cf.longitude),
          isp: cf.asOrganization || null,
          asn: safeNum(cf.asn),
          ts: new Date().toISOString(),
        };

        await env.DB
          .prepare(
            `INSERT INTO logs (code, name, ip, ua, city, region, country, lat, lon, isp, asn, ts)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)`
          )
          .bind(
            data.code,
            data.name,
            data.ip,
            data.ua,
            data.city,
            data.region,
            data.country,
            data.lat,
            data.lon,
            data.isp,
            data.asn,
            data.ts
          )
          .run();

        // a) PNG 1x1 (melhor para previews, não “vaza” redirect)
        // b) Se quiser redirecionar, use ?img=https://... (WhatsApp pode não seguir)
        const img = url.searchParams.get("img");
        if (img) return Response.redirect(img, 302);
        return tinyPNG(); // 1x1 transparente
      }

      if (path.startsWith("/api/logs/")) {
        const code = (path.split("/").pop() || "").trim();
        if (!code) return bad(400, "Código obrigatório");
        const { results } = await env.DB.prepare(
          `SELECT id, code, name, ip, ua, city, region, country, lat, lon, isp, asn, ts
           FROM logs WHERE code=?1 ORDER BY id DESC LIMIT 1000`
        ).bind(code).all();
        return json({ code, total: results.length, logs: results });
      }

      if (path.startsWith("/map/")) {
        const code = (path.split("/").pop() || "").trim();
        if (!code) return bad(400, "Código inválido");

        const { results } = await env.DB.prepare(
          `SELECT id, code, name, ip, ua, city, region, country, lat, lon, isp, asn, ts
           FROM logs WHERE code=?1 ORDER BY id DESC LIMIT 2000`
        ).bind(code).all();

        return html(leafletPage({ code, logs: results }));
      }

      return notFound();
    } catch (err) {
      console.error(err);
      return bad(500, "Deu ruim no Worker");
    }
  },
};

// ---------- helpers ----------
function ok(msg) {
  return new Response(msg, { status: 200, headers: { "content-type": "text/plain; charset=utf-8" } });
}
function bad(status, msg) {
  return new Response(msg, { status, headers: { "content-type": "text/plain; charset=utf-8" } });
}
function notFound() {
  return new Response("Not found", { status: 404, headers: { "content-type": "text/plain; charset=utf-8" } });
}
function json(obj) {
  return new Response(JSON.stringify(obj, null, 2), { status: 200, headers: { "content-type": "application/json; charset=utf-8" } });
}
function html(s) {
  return new Response(s, { status: 200, headers: { "content-type": "text/html; charset=utf-8" } });
}
function safeNum(n) {
  const x = Number(n);
  return Number.isFinite(x) ? x : null;
}
// PNG 1x1 base64 (transparente)
function tinyPNG() {
  const b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAA"
            + "AAC0lEQVR42mP8/x8AAwMBAHk2x4QAAAAASUVORK5CYII=";
  const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  return new Response(bin, { status: 200, headers: { "content-type": "image/png" } });
}
// short code determinístico o bastante p/ link curto
function shortCode() {
  // 8 chars base36 a partir de UUID
  const u = crypto.randomUUID().replace(/-/g, "");
  const n = BigInt("0x" + u.slice(0, 12)); // 48 bits
  return n.toString(36).slice(0, 8);
}

// ---------- UI / Map ----------
function leafletPage({ code, logs }) {
  // centro padrão: Brasil
  let centerLat = -15.78, centerLon = -47.92;
  for (const l of logs) {
    if (l.lat != null && l.lon != null) { centerLat = l.lat; centerLon = l.lon; break; }
  }
  const uniqueIPs = new Set(logs.map(l => l.ip).filter(Boolean)).size;

  const data = JSON.stringify(logs || []);

  return `
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>Mapa - ${escapeHtml(code)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" rel="stylesheet">
<style>
  :root {
    --lex-orange: #ff7a18;
    --ink: #111;
    --paper: #0b0b0b;
    --muted: #999;
  }
  html,body { margin:0; height:100%; background:#0a0a0a; color:#eee; font-family: Inter, system-ui, Arial, sans-serif; }
  #map { height:100%; }
  .panel {
    position: absolute; top: 16px; right: 16px; z-index: 1000;
    background: rgba(15,15,15,.9); border:1px solid #222; border-radius:14px; padding:14px 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,.4);
  }
  .panel h3 { margin:0 0 8px 0; font-size:15px; letter-spacing:.4px; color:#fff }
  .panel .pill { display:inline-block; padding:4px 8px; margin-right:6px; border-radius:999px; background:#161616; border:1px solid #262626; font-size:12px; color:#ddd }
  .panel .code { color: var(--lex-orange); font-weight:700; }
  .leaflet-container { background:#0e0e0e; }
  .leaflet-popup-content-wrapper, .leaflet-popup-tip { background:#101010; color:#eee; border:1px solid #222; }
  .brand {
    position: absolute; left: 16px; bottom: 16px; padding:6px 10px; border-radius:10px;
    background:linear-gradient(135deg, rgba(255,122,24,.15), rgba(255,122,24,.03));
    border:1px solid rgba(255,122,24,.25); color:#ffb37a; font-weight:600; letter-spacing:.4px;
  }
</style>
</head>
<body>
  <div id="map"></div>
  <div class="panel">
    <h3>📍 <span class="code">/t/${escapeHtml(code)}</span></h3>
    <div class="pill">Acessos: ${logs.length}</div>
    <div class="pill">IPs únicos: ${uniqueIPs}</div>
    <div class="pill">API: /api/logs/${escapeHtml(code)}</div>
  </div>
  <div class="brand">LEXKING · tracker</div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const logs = ${data};
    const map = L.map('map').setView([${centerLat}, ${centerLon}], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 19
    }).addTo(map);

    const pts = [];
    logs.forEach(l => {
      if (l.lat != null && l.lon != null) {
        const m = L.marker([l.lat, l.lon]).addTo(map)
          .bindPopup(
            \`<b>\${l.city || 'N/A'}\${l.region ? ', ' + l.region : ''}\${l.country ? ', ' + l.country : ''}</b><br>
               <b>IP:</b> \${l.ip || '-'}<br>
               <b>ISP/ASN:</b> \${l.isp || '-'} \${l.asn ? '(AS' + l.asn + ')' : ''}<br>
               <b>Data:</b> \${new Date(l.ts).toLocaleString('pt-BR')}\`
          );
        pts.push([l.lat, l.lon]);
      }
    });
    if (pts.length > 1) map.fitBounds(pts, { padding: [40,40] });
  </script>
</body>
</html>`;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"'`=\/]/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;","/":"&#x2F;","`":"&#x60;","=":"&#x3D;"
  }[c]));
}
