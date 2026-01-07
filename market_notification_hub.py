import os
from core.loader import Loader
from core.indicator import Indicator
from core.backtester import Backtester
from core.strategies import Strategies
from core.notifier import Notifier
from dotenv import load_dotenv
load_dotenv()
os.chdir(os.path.dirname(os.path.abspath(__file__)))

  
def main(channel):
    # import strategies from strategies.csv
    strategies = Strategies().import_strategies(channel["strategies"])
    tickers    = list(strategies.keys())
    
    # import standard indicators for signal confirmation
    confirmations = loader.load_confirmations()

    # initialize lists
    alerts = []
    report = []
        
    # run for each ticker
    for ticker in tickers:
        print(f"Processing {ticker}")
        
        # strategy
        ind_t     = strategies[ticker]["Indicator"]
        ind_p     = strategies[ticker]["Parameters"]
        params    = ind_p.split("_")
        indicator = {"ind_t": ind_t, "ind_p": [int(p) for p in params]}
        
        # download and backtest
        df = loader.download_data(ticker)
        confir = []
        for confirmation in confirmations:
            df_c = df.copy()
            df_c = Indicator(confirmation).setup_indicator(df_c)
            df_c = Backtester(df_c).run_strategy(confirmation)
            confir.append(df_c["Signal"].iloc[-1])
        df = Indicator(indicator).setup_indicator(df)
        df = Backtester(df).run_strategy(indicator)

        # obtain last values: closing price, signal, signal length, volume strength, entry price
        last_clo = df["Close"].iloc[-1]
        last_sig = df["Signal"].iloc[-1]
        last_str = df["Signal_Length"].iloc[-1]
        last_vol = df["Volume_Strength"].iloc[-1]
        last_ent = df["Entry_Price"].iloc[-1]
        last_con = confir.count(1)

        # store report
        alerts.append({
            "Ticker": ticker,
            "Indicator": ind_t,
            "Parameters": params,
            "Close": float(last_clo),
            "Signal": int(last_sig),
            "Signal_Length": int(last_str),
            "Signal Confirmation": last_con,
            "Volume_Strength": float(last_vol),
            "Entry_Price": float(last_ent)
        })
    
    messages = {}
    for a in alerts:
        # define signal
        if a["Signal"] != 0:       
            verb = "⬆️ BUY" if a["Signal"] == 1 else "⬇️ SELL"
        else:
            verb = "⏸️ NEUTRAL"
        
        # trading message
        msg = (f"#{a['Ticker']} | {verb} ({a['Indicator']}{'/'.join(a['Parameters'])}) Duration {a['Signal_Length']:d} | Price U$ {a['Close']:.2f}\n"
               f"Volume Strength: {a['Volume_Strength']:.2f}\n"
               f"Signal Confirmation: {a['Signal Confirmation']}/{len(confir)} BUY, {len(confir)-a['Signal Confirmation']}/{len(confir)} SELL\n"
               f"Entry Price: U$ {a['Entry_Price']:.2f}")
        report.append(msg)

        # notifies via Telegram
        token    = os.getenv(channel["token"])
        chat_id  = os.getenv(channel["chat_id"])
        notifier = Notifier(token=token, chat_id=chat_id)
        try:
            payload = {"chat_id": notifier.CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True}
            msg_id  = notifier.send_telegram(payload)
            messages[a["Ticker"]] = msg_id
        except Exception as err:
            print("Telegram error:", err)
    
    # summary in Telegram
    try:
        summary = []
        for ticker, msg_id in messages.items():
            link = f"https://t.me/{notifier.CHAT_ID.lstrip('@')}/{msg_id}"
            summary.append(f'<a href="{link}">{ticker}</a>')
        msg   =  " ○ ".join(summary)
        payload = {"chat_id": notifier.CHAT_ID, "text": f"<b>Summary:</b>\n{msg}", "parse_mode": "HTML", "disable_web_page_preview": True}
        notifier.send_telegram(payload)
    
    except Exception as err:
        print("Telegram error:", err)


if __name__ == "__main__":
    loader = Loader("config/channels.json")
    
    for channel in loader.channels:
        max_attempt = 3
        
        for attempt in range(max_attempt):
            try:
                print(f"Channel: {channel['name']}.")
                main(channel)
                break
            except Exception as err:
                print(f"Error on attempt {attempt}: {err}.")