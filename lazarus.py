import requests

import time

import json

from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURAÇÕES DO SNIPER (MODO ELITE V1.0) ---

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")



# Regras de Ouro

QUEDA_MINIMA = 0.40       # Queda de 40% nas últimas 24h

RECUPERACAO_MINIMA = 0.10 # Subiu 10% do fundo (Sinal de vida)

RECUPERACAO_MAXIMA = 1.00 # Máximo 100% (Não pegar se já dobrou)

VOLUME_MINIMO = 500000    # Volume > $500k (Liquidez)

COOLDOWN_HORAS = 4        # Avisar da mesma moeda de novo após 4 horas



print("🦅 PROJETO LAZARUS: SISTEMA 100% OPERACIONAL")

print(f"   -> Filtros: Queda > 40% | Rec: 10%-100% | Vol > $500k")

print(f"   -> Re-aviso a cada {COOLDOWN_HORAS} horas para oportunidades persistentes.")

print("-" * 50)



# Dicionário para controlar o tempo dos alertas: {'SYMBOL': timestamp}

alertas_enviados = {}



def enviar_telegram(mensagem):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}

    try:

        requests.post(url, data=data, timeout=10)

    except Exception as e:

        print(f"Erro no Telegram: {e}")



def buscar_oportunidades():

    url = "https://api.mexc.com/api/v3/ticker/24hr"

    try:

        response = requests.get(url, timeout=10)

        dados = response.json()

        

        agora = time.time()

        

        # Limpeza de memória (Remove moedas do cooldown que já expiraram)

        chaves_para_remover = [k for k, v in alertas_enviados.items() if agora - v > (COOLDOWN_HORAS * 3600)]

        for k in chaves_para_remover:

            del alertas_enviados[k]



        for moeda in dados:

            symbol = moeda['symbol']

            if not symbol.endswith("USDT"): continue

                

            try:

                preco_atual = float(moeda['lastPrice'])

                high_24h = float(moeda['highPrice'])

                low_24h = float(moeda['lowPrice'])

                volume_usdt = float(moeda['quoteVolume'])

            except: continue



            if high_24h == 0 or low_24h == 0: continue



            queda_do_topo = (high_24h - preco_atual) / high_24h

            recuperacao = (preco_atual - low_24h) / low_24h



            # --- FILTROS ---

            if (queda_do_topo >= QUEDA_MINIMA and 

                recuperacao >= RECUPERACAO_MINIMA and 

                recuperacao <= RECUPERACAO_MAXIMA and 

                volume_usdt > VOLUME_MINIMO):

                

                # Verifica se está no Cooldown

                if symbol in alertas_enviados:

                    ultimo_aviso = alertas_enviados[symbol]

                    # Se não passou 4 horas, ignora

                    if agora - ultimo_aviso < (COOLDOWN_HORAS * 3600):

                        continue



                hora_formatada = datetime.now().strftime("%H:%M")

                icone = "🔥" if volume_usdt > 1000000 else "⚡"

                

                msg = (

                    f"{icone} **OPORTUNIDADE DETECTADA!**\n\n"

                    f"💎 **Moeda:** `{symbol}`\n"

                    f"📉 **Queda:** -{queda_do_topo*100:.1f}%\n"

                    f"🚀 **Recuperação:** +{recuperacao*100:.1f}%\n"

                    f"📊 **Vol:** ${volume_usdt:,.0f}\n"

                    f"💰 **Preço:** {preco_atual}\n\n"

                    f"⏰ {hora_formatada} | [Ver na MEXC](https://www.mexc.com/exchange/{symbol.replace('USDT','_USDT')})"

                )

                

                print(f"✅ ALERTA ENVIADO: {symbol} | Rec: +{recuperacao*100:.0f}%")

                enviar_telegram(msg)

                

                # Registra o horário do aviso

                alertas_enviados[symbol] = agora



    except Exception as e:

        print(f"Erro na conexão ou processamento: {e}")



# Loop Infinito

while True:

    buscar_oportunidades()

    time.sleep(60)