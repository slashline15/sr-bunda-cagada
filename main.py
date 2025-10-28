# main.py
import time
from typing import Tuple, Optional
import folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Função para tentar interpretar a entrada como coordenadas ou endereço
def parse_input(s: str) -> Optional[Tuple[float, float]]:
    s = s.strip()
    if "," in s:
        try:
            lat_str, lon_str = s.split(",", 1)
            return float(lat_str), float(lon_str)
        except ValueError:
            return None
    return None

# Função principal para geocodificação e geocodificação reversa. Email de teste incluído no user_agent.
def geocode_anything(query: str) -> Tuple[Tuple[float, float], str]:
    geolocator = Nominatim(user_agent="engdaniel-localizador/1.0 (contato: daniel.alves66@hotmail.com)")
    # Respeita rate-limit do Nominatim
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)
    # Tenta interpretar como coordenadas primeiro
    coords = parse_input(query)
    if coords:
        lat, lon = coords
        location = reverse((lat, lon), language="pt")
        address = location.address if location else f"{lat}, {lon}"
        return (lat, lon), address
    else:
        location = geocode(query, language="pt")
        if not location:
            raise RuntimeError("Endereço não encontrado. Tenta ser mais específico (bairro, cidade, UF).")
        return (location.latitude, location.longitude), location.address

# Função para construir e salvar o mapa com folium
def build_map(lat: float, lon: float, popup: str, out_file: str = "map.html"):
    m = folium.Map(location=[lat, lon], zoom_start=15, control_scale=True, tiles="OpenStreetMap")
    folium.Marker(
        location=[lat, lon],
        popup=popup,
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

    # camada extra bonita
    folium.TileLayer("CartoDB positron").add_to(m)
    folium.LayerControl().add_to(m)

    # salvar mapa em arquivo HTML e retornar o nome do arquivo
    m.save(out_file)
    return out_file


# Execução principal: solicita entrada do usuário e gera o mapa. Para configurarções adicionais, edite o código.
if __name__ == "__main__":
    try:
        query = input("Digite um endereço ou coordenadas (lat,lon): ").strip()
        (lat, lon), address = geocode_anything(query)
        print(f"Endereço: {address}")
        print(f"Latitude: {lat}, Longitude: {lon}")
        out = build_map(lat, lon, popup=address, out_file="map.html")
        print(f"✔ Mapa gerado em: {out}")
        # abrir arquivo HTML no navegador padrão
        import webbrowser
        webbrowser.open(out)
    except Exception as e:
        print(f"Erro: {e}")
