#!/usr/bin/env python3
# run_all.py
"""
Script para executar o Bot do Telegram e o Servidor Flask simultaneamente
"""
import subprocess
import sys
import os
import signal
import time
from typing import List

# Lista de processos
processos: List[subprocess.Popen] = []


def signal_handler(sig, frame):
    """Handler para capturar Ctrl+C e encerrar processos."""
    print("\n\n🛑 Encerrando serviços...")
    for processo in processos:
        processo.terminate()
    print("✅ Serviços encerrados com sucesso!")
    sys.exit(0)


def verificar_env():
    """Verifica se o arquivo .env existe."""
    if not os.path.exists('.env'):
        print("⚠️  AVISO: Arquivo .env não encontrado!")
        print("📝 Copie o arquivo .env.example para .env e configure as variáveis.")
        print("\nComando: cp .env.example .env\n")
        resposta = input("Deseja continuar mesmo assim? (s/n): ")
        if resposta.lower() != 's':
            sys.exit(1)


def main():
    """Executa o bot e o servidor Flask simultaneamente."""
    # Registrar handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Verificar arquivo .env
    verificar_env()

    print("=" * 60)
    print("🚀 SISTEMA DE LOCALIZAÇÃO DE IPs")
    print("=" * 60)
    print()

    try:
        # Iniciar servidor Flask
        print("🌐 Iniciando servidor Flask...")
        processo_flask = subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        processos.append(processo_flask)
        time.sleep(2)  # Aguardar inicialização

        # Iniciar bot do Telegram
        print("🤖 Iniciando bot do Telegram...")
        processo_bot = subprocess.Popen(
            [sys.executable, "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        processos.append(processo_bot)

        print()
        print("✅ Serviços iniciados com sucesso!")
        print()
        print("=" * 60)
        print("📋 SERVIÇOS ATIVOS:")
        print("=" * 60)
        print("🌐 Flask Server: http://localhost:5000")
        print("🤖 Telegram Bot: Ativo e aguardando comandos")
        print()
        print("💡 Pressione Ctrl+C para encerrar todos os serviços")
        print("=" * 60)
        print()

        # Monitorar processos
        while True:
            time.sleep(1)

            # Verificar se algum processo morreu
            for i, processo in enumerate(processos):
                if processo.poll() is not None:
                    nome = "Flask" if i == 0 else "Bot"
                    print(f"\n❌ {nome} encerrado inesperadamente!")

                    # Mostrar saída do processo
                    if processo.stdout:
                        output = processo.stdout.read()
                        if output:
                            print(f"\nSaída do {nome}:")
                            print(output)

                    # Encerrar todos os processos
                    signal_handler(None, None)

    except Exception as e:
        print(f"\n❌ Erro ao iniciar serviços: {e}")
        for processo in processos:
            processo.terminate()
        sys.exit(1)


if __name__ == "__main__":
    main()
