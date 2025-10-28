"""
Módulo compartilhado para gerenciamento de logs entre app.py e bot.py
"""
import ast
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

LOG_FILE = "log.txt"
LOG_FILE_JSON = "log.json"

# Configurar logging
logger = logging.getLogger(__name__)


class LogManager:
    """Gerenciador de logs de localização de IPs."""

    def __init__(self, log_file: str = LOG_FILE):
        self.log_file = log_file

    def adicionar_registro(self, data: Dict) -> bool:
        """
        Adiciona um novo registro ao arquivo de log.

        Args:
            data: Dicionário com os dados do registro

        Returns:
            True se o registro foi adicionado com sucesso
        """
        try:
            # Adiciona timestamp se não existir
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()

            # Salvar em formato texto (compatibilidade)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(str(data) + os.linesep)

            # Também salvar em JSON para melhor estruturação
            self._salvar_json(data)

            logger.info(f"Registro adicionado: {data.get('ip', 'N/A')}")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar registro: {e}")
            return False

    def _salvar_json(self, data: Dict) -> None:
        """Salva registro adicional em formato JSON."""
        try:
            registros = []
            if os.path.exists(LOG_FILE_JSON):
                with open(LOG_FILE_JSON, "r", encoding="utf-8") as f:
                    registros = json.load(f)

            registros.append(data)

            with open(LOG_FILE_JSON, "w", encoding="utf-8") as f:
                json.dump(registros, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Erro ao salvar JSON: {e}")

    def ler_registros(self) -> List[Dict]:
        """
        Lê todos os registros do arquivo de log.

        Returns:
            Lista de dicionários com os registros
        """
        registros = []

        # Tentar ler do JSON primeiro (mais rápido e confiável)
        if os.path.exists(LOG_FILE_JSON):
            try:
                with open(LOG_FILE_JSON, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao ler JSON, tentando TXT: {e}")

        # Fallback para arquivo TXT
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for linha in f:
                    try:
                        registro = ast.literal_eval(linha.strip())
                        registros.append(registro)
                    except Exception as e:
                        logger.error(f"Erro ao parsear linha: {linha[:50]}... - {e}")
        except FileNotFoundError:
            logger.warning(f"Arquivo {self.log_file} não encontrado")

        return registros

    def buscar_por_ip(self, ip: str) -> List[Dict]:
        """Busca registros por endereço IP."""
        registros = self.ler_registros()
        return [r for r in registros if r.get('ip') == ip]

    def buscar_por_cidade(self, cidade: str) -> List[Dict]:
        """Busca registros por nome da cidade."""
        registros = self.ler_registros()
        return [
            r for r in registros
            if r.get('city') and cidade.lower() in r['city'].lower()
        ]

    def buscar_por_pais(self, pais: str) -> List[Dict]:
        """Busca registros por país."""
        registros = self.ler_registros()
        return [
            r for r in registros
            if r.get('country') and pais.lower() in r['country'].lower()
        ]

    def obter_ultimos(self, n: int = 10) -> List[Dict]:
        """Obtém os últimos N registros."""
        registros = self.ler_registros()
        return registros[-n:] if registros else []

    def obter_estatisticas(self) -> Dict:
        """Obtém estatísticas gerais dos logs."""
        registros = self.ler_registros()

        if not registros:
            return {
                "total": 0,
                "ips_unicos": 0,
                "cidades_unicas": 0,
                "paises_unicos": 0
            }

        ips = set(r.get('ip') for r in registros if r.get('ip'))
        cidades = set(r.get('city') for r in registros if r.get('city'))
        paises = set(r.get('country') for r in registros if r.get('country'))

        return {
            "total": len(registros),
            "ips_unicos": len(ips),
            "cidades_unicas": len(cidades),
            "paises_unicos": len(paises),
            "primeiro_registro": registros[0].get('timestamp') if registros else None,
            "ultimo_registro": registros[-1].get('timestamp') if registros else None
        }


# Instância global para uso compartilhado
log_manager = LogManager()
