# bot.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
import os
import logging
import dotenv
from typing import Dict
from datetime import datetime

from log_manager import log_manager

# Configuração básica de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente do arquivo .env
dotenv.load_dotenv()
TOKEN_API_TELEGRAM = os.getenv("TOKEN_API_TELEGRAM")
if not TOKEN_API_TELEGRAM:
    raise ValueError("TOKEN_API_TELEGRAM não encontrado no arquivo .env")

# ==================== COMANDOS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando inicial com menu inline."""
    if not update.message or not update.effective_user:
        logging.error("Received update without message or user")
        return

    keyboard = [
        [InlineKeyboardButton("📊 Estatísticas", callback_data="menu_stats")],
        [InlineKeyboardButton("🔍 Buscar IP", callback_data="menu_buscar_ip")],
        [InlineKeyboardButton("🏙️ Buscar Cidade", callback_data="menu_buscar_cidade")],
        [InlineKeyboardButton("📝 Últimos Registros", callback_data="menu_ultimos")],
        [InlineKeyboardButton("❓ Ajuda", callback_data="menu_ajuda")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Bem-vindo, {update.effective_user.first_name}!\n\n"
        "🌍 Sistema de Localização de IPs\n"
        "Escolha uma opção abaixo ou use os comandos:\n\n"
        "/stats - Ver estatísticas do sistema\n"
        "/buscar_ip <ip> - Buscar por endereço IP\n"
        "/buscar_cidade <cidade> - Buscar por cidade\n"
        "/ultimos [n] - Ver últimos registros",
        reply_markup=reply_markup
    )

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando de saudação."""
    if not update.message or not update.effective_user:
        logging.error("Received update without message or user")
        return

    await update.message.reply_text(f"Olá, {update.effective_user.first_name}!")



# ==================== FUNÇÕES AUXILIARES ====================

def formatar_registro(registro: Dict) -> str:
    """Formata um registro para exibição."""
    return (
        f"Data: {datetime.fromisoformat(registro['timestamp']).strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"IP: {registro['ip']}\n"
        f"Cidade: {registro['city'] or 'N/A'}\n"
        f"País: {registro['country'] or 'N/A'}\n"
        f"-------------------"
    )

# ==================== COMANDOS DE BUSCA ====================

async def buscar_ip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca registros por endereço IP."""
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "Por favor, forneça um IP para buscar.\n"
            "Exemplo: /buscar_ip 192.168.1.1"
        )
        return

    ip = context.args[0]
    encontrados = log_manager.buscar_por_ip(ip)

    if not encontrados:
        await update.message.reply_text(f"Nenhum registro encontrado para o IP {ip}")
        return

    resposta = f"Encontrados {len(encontrados)} registro(s) para IP {ip}:\n\n"
    for r in encontrados[:5]:  # Limita a 5 resultados
        resposta += formatar_registro(r) + "\n"

    if len(encontrados) > 5:
        resposta += f"\n... e mais {len(encontrados) - 5} registro(s)"

    await update.message.reply_text(resposta)

async def buscar_cidade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca registros por nome da cidade."""
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "Por favor, forneça uma cidade para buscar.\n"
            "Exemplo: /buscar_cidade São Paulo"
        )
        return

    cidade = " ".join(context.args)
    encontrados = log_manager.buscar_por_cidade(cidade)

    if not encontrados:
        await update.message.reply_text(f"Nenhum registro encontrado para a cidade {cidade}")
        return

    resposta = f"Encontrados {len(encontrados)} registro(s) para cidade {cidade}:\n\n"
    for r in encontrados[:5]:  # Limita a 5 resultados
        resposta += formatar_registro(r) + "\n"

    if len(encontrados) > 5:
        resposta += f"\n... e mais {len(encontrados) - 5} registro(s)"

    await update.message.reply_text(resposta)

async def ultimos_registros(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe os últimos N registros do log."""
    if not update.message:
        return

    n = 5  # padrão
    if context.args:
        try:
            n = min(int(context.args[0]), 10)  # máximo 10 registros
        except ValueError:
            await update.message.reply_text(
                "Por favor, forneça um número válido.\n"
                "Exemplo: /ultimos 5"
            )
            return

    registros = log_manager.obter_ultimos(n)
    if not registros:
        await update.message.reply_text("Nenhum registro encontrado no log")
        return

    resposta = f"Últimos {len(registros)} registro(s):\n\n"
    for r in registros:
        resposta += formatar_registro(r) + "\n"

    await update.message.reply_text(resposta)

async def estatisticas(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe estatísticas gerais dos logs."""
    if not update.message:
        return

    stats = log_manager.obter_estatisticas()

    if stats['total'] == 0:
        await update.message.reply_text("Nenhum registro encontrado no sistema")
        return

    resposta = (
        "📊 *Estatísticas do Sistema*\n\n"
        f"📝 Total de registros: *{stats['total']}*\n"
        f"🌐 IPs únicos: *{stats['ips_unicos']}*\n"
        f"🏙️ Cidades únicas: *{stats['cidades_unicas']}*\n"
        f"🌍 Países únicos: *{stats['paises_unicos']}*\n\n"
    )

    if stats.get('primeiro_registro'):
        primeiro = datetime.fromisoformat(stats['primeiro_registro']).strftime('%d/%m/%Y %H:%M:%S')
        resposta += f"⏰ Primeiro registro: {primeiro}\n"

    if stats.get('ultimo_registro'):
        ultimo = datetime.fromisoformat(stats['ultimo_registro']).strftime('%d/%m/%Y %H:%M:%S')
        resposta += f"⏰ Último registro: {ultimo}\n"

    await update.message.reply_text(resposta, parse_mode='Markdown')

# ==================== HANDLERS INLINE ====================

async def button_callback(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para botões inline."""
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if query.data == "menu_stats":
        # Exibe estatísticas diretamente
        stats = log_manager.obter_estatisticas()

        if stats['total'] == 0:
            await query.edit_message_text("Nenhum registro encontrado no sistema")
            return

        resposta = (
            "📊 *Estatísticas do Sistema*\n\n"
            f"📝 Total de registros: *{stats['total']}*\n"
            f"🌐 IPs únicos: *{stats['ips_unicos']}*\n"
            f"🏙️ Cidades únicas: *{stats['cidades_unicas']}*\n"
            f"🌍 Países únicos: *{stats['paises_unicos']}*\n\n"
        )

        if stats.get('primeiro_registro'):
            primeiro = datetime.fromisoformat(stats['primeiro_registro']).strftime('%d/%m/%Y %H:%M:%S')
            resposta += f"⏰ Primeiro registro: {primeiro}\n"

        if stats.get('ultimo_registro'):
            ultimo = datetime.fromisoformat(stats['ultimo_registro']).strftime('%d/%m/%Y %H:%M:%S')
            resposta += f"⏰ Último registro: {ultimo}\n"

        # Adiciona botão de voltar
        keyboard = [[InlineKeyboardButton("◀️ Voltar ao Menu", callback_data="menu_voltar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(resposta, parse_mode='Markdown', reply_markup=reply_markup)

    elif query.data == "menu_buscar_ip":
        await query.edit_message_text(
            "Para buscar por IP, use o comando:\n"
            "/buscar_ip <endereço_ip>\n\n"
            "Exemplo: /buscar_ip 192.168.1.1"
        )

    elif query.data == "menu_buscar_cidade":
        await query.edit_message_text(
            "Para buscar por cidade, use o comando:\n"
            "/buscar_cidade <nome_da_cidade>\n\n"
            "Exemplo: /buscar_cidade São Paulo"
        )

    elif query.data == "menu_ultimos":
        # Executa diretamente a busca dos últimos 5 registros
        registros = log_manager.obter_ultimos(5)
        if not registros:
            await query.edit_message_text("Nenhum registro encontrado no log")
            return

        resposta = f"Últimos {len(registros)} registro(s):\n\n"
        for r in registros:
            resposta += formatar_registro(r) + "\n"

        # Adiciona botão de voltar
        keyboard = [[InlineKeyboardButton("◀️ Voltar ao Menu", callback_data="menu_voltar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(resposta, reply_markup=reply_markup)

    elif query.data == "menu_ajuda":
        keyboard = [[InlineKeyboardButton("◀️ Voltar ao Menu", callback_data="menu_voltar")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📖 *Comandos Disponíveis*\n\n"
            "/start - Menu principal\n"
            "/stats - Ver estatísticas do sistema\n"
            "/buscar_ip <ip> - Buscar por endereço IP\n"
            "/buscar_cidade <cidade> - Buscar por cidade\n"
            "/ultimos [n] - Ver últimos N registros (padrão: 5, máx: 10)\n"
            "/hello - Saudação\n\n"
            "💡 Use os botões do menu ou digite os comandos diretamente.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    elif query.data == "menu_voltar":
        # Recria o menu principal
        keyboard = [
            [InlineKeyboardButton("📊 Estatísticas", callback_data="menu_stats")],
            [InlineKeyboardButton("🔍 Buscar IP", callback_data="menu_buscar_ip")],
            [InlineKeyboardButton("🏙️ Buscar Cidade", callback_data="menu_buscar_cidade")],
            [InlineKeyboardButton("📝 Últimos Registros", callback_data="menu_ultimos")],
            [InlineKeyboardButton("❓ Ajuda", callback_data="menu_ajuda")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "🌍 Sistema de Localização de IPs\n"
            "Escolha uma opção abaixo ou use os comandos:\n\n"
            "/stats - Ver estatísticas do sistema\n"
            "/buscar_ip <ip> - Buscar por endereço IP\n"
            "/buscar_cidade <cidade> - Buscar por cidade\n"
            "/ultimos [n] - Ver últimos registros",
            reply_markup=reply_markup
        )

# ==================== CONFIGURAÇÃO DA APLICAÇÃO ====================

def main() -> None:
    """Função principal que inicializa e executa o bot."""
    if not TOKEN_API_TELEGRAM:
        raise ValueError("TOKEN_API_TELEGRAM não está configurado")

    # Criar aplicação
    app = ApplicationBuilder().token(TOKEN_API_TELEGRAM).build()

    # Registrar handlers de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(CommandHandler("stats", estatisticas))
    app.add_handler(CommandHandler("buscar_ip", buscar_ip))
    app.add_handler(CommandHandler("buscar_cidade", buscar_cidade))
    app.add_handler(CommandHandler("ultimos", ultimos_registros))

    # Registrar handler de callbacks inline
    app.add_handler(CallbackQueryHandler(button_callback))

    # Iniciar o bot
    logging.info("Bot iniciado e aguardando comandos...")
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()

