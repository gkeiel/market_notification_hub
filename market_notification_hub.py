import os, argparse, random
from core.loader import Loader
from core.indicator import Indicator
from core.backtester import Backtester
from core.strategies import Strategies
from core.notifier import Notifier
from dotenv import load_dotenv
load_dotenv()
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def main(channel, mode):
    # run for selected mode
    if mode == "signals":
        run_signals(channel)
    elif mode == "alerts":
        run_alerts(channel)
    elif mode == "info":
        run_info(channel)
    else:
        raise ValueError("Invalid mode.")

def run_alerts(channel):
    # import strategies from strategies.csv
    strategies = Strategies().import_strategies(channel["strategies"])
    tickers    = list(strategies.keys())
    notifier   = Notifier()
    price_move  = []
    volume_move = []
    
    for ticker in tickers:
        df = loader.download_data(ticker)
        price_change = (df["Close"].iloc[-1]/df["Close"].iloc[-2] -1)*100
        price_move.append((ticker, price_change))
        volume_ratio = df["Volume"].iloc[-1]/df["Volume"].rolling(20).mean().iloc[-1]
        volume_move.append((ticker, volume_ratio))

    price_move  = sorted(price_move, key=lambda x: abs(x[1]), reverse=True)[:3]
    volume_move = sorted(volume_move, key=lambda x: x[1], reverse=True)[:3]
    
    if price_move or volume_move:
        msg = "<b>Price Movers:<\b>\n"
        for ticker, change in price_move:
            msg += f"#{ticker} {change:+.1f}%\n"
        msg += "\n<b>Volume Leaders:<\b>\n"
        for ticker, vol in volume_move:
            msg += f"#{ticker} {vol:.1f}x\n"
    #else:
        #msg = ("Stay disciplined. The market rewards patience.\n")
    notifier.send_telegram(msg)

def run_info(channel):
    notifier = Notifier()
    
    messages = [
    "Check our other channels:\n"
    "t.me/b3_trading_signals_free\n"
    "t.me/market_forecaster_public",

    "Trading Tip:\n"
    "Strong trends often begin with volume expansion.",

    "Discipline Tip:\n"
    "Consistent traders follow their plan even after a losing trade.",

    "Market Insight:\n"
    "Large price moves with low volume often lack follow-through.",
    
    "Market Insight:\n"
    "Volatility often increases near major support and resistance levels."
    
    "Risk Reminder:\n"
    "Protecting capital is more important than chasing profits."
    ]
    
    msg = random.choice(messages)
    notifier.send_telegram(msg)
    
def run_signals(channel):
    # import strategies from strategies.csv
    strategies = Strategies().import_strategies(channel["strategies"])
    tickers    = list(strategies.keys())
    notifier   = Notifier()

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
        try:
            msg_id = notifier.send_telegram(msg)
            messages[a["Ticker"]] = msg_id
        except Exception as err:
            print("Telegram error:", err)
    
    # summary in Telegram
    try:
        summary = []
        for ticker, msg_id in messages.items():
            link = f"https://t.me/{notifier.CHAT_ID.lstrip('@')}/{msg_id}"
            summary.append(f'<a href="{link}">{ticker}</a>')
        msg = "Summary:\n" +" ○ ".join(summary)
        notifier.send_telegram(msg)
    
    except Exception as err:
        print("Telegram error:", err)
        
    # report in E-mail
    notifier.send_email(subject="Market Notification Hub - Daily Report", body="\n\n".join(report))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="signals")
    args   = parser.parse_args()
    
    loader = Loader("config/channels.json")
    
    for channel in loader.channels:
        max_attempt = 3
        
        for attempt in range(max_attempt):
            try:
                print(f"Channel {channel['name']}")
                main(channel, args.mode)
                break
            except Exception as err:
                print(f"Error on attempt {attempt}: {err}.")