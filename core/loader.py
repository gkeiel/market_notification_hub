import json
import yfinance as yf
from datetime import datetime


# =====================================================
#  Loader
# =====================================================
class Loader:
    def __init__(self, file_config):
        self.file_config = file_config
        self.load_config(file_config)
           
    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            self.start    = config.get("start", "2024-01-01")
            self.end      = config.get("end", datetime.now())
            self.market   = config.get("market", "US")
            self.channels = config.get("channels", [])
            
    def load_tickers(self):
        with open(self.file_tickers, "r", encoding="utf-8") as f:
            data = json.load(f)
        tickers = data.get("tickers", [])
        return tickers
    
    def load_indicators(self):
        indicators = []
        with open(self.file_indicators, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    ind_t = parts[0]                        # indicator title
                    ind_p = [int(x) for x in parts[1:]]     # indicator parameters
                    indicators.append({"ind_t":ind_t, "ind_p":ind_p})
        return indicators

    def load_confirmations(self):
        return [
            {"ind_t": "SMA", "ind_p": [5]},
            {"ind_t": "SMA", "ind_p": [10]},
            {"ind_t": "SMA", "ind_p": [20]},
            {"ind_t": "SMA", "ind_p": [50]},
            {"ind_t": "SMA", "ind_p": [100]},
            {"ind_t": "SMA", "ind_p": [200]},
        ]
    SUFFIXES = {"AU":".AX", "BR":".SA", "CN":".SS", "CA":".TO"}
    
    def load_search_space(self):    
        with open(self.file_config, "r", encoding="utf-8") as f:
            config = json.load(f)
        optimize = config.get("optimize")
        
        space = []
        for opt in optimize:
            space.append({
                "ind_t":  opt["ind_t"],
                "params": opt["params"]
            })
        return space
    
    def format_ticker(self, ticker):
        if self.market == "BR" and not ticker.endswith(".SA"):
            return f"{ticker}.SA"
        return ticker

    def download_data(self, ticker):
        # collect OHLCVDS data from Yahoo Finance
        try:
            df = yf.download(self.format_ticker(ticker), self.start, self.end, auto_adjust=True)
        except Exception as err:
            raise RuntimeError("Unexpected error in download_data.") from err
        
        # format data
        df.columns = df.columns.droplevel(1)    
        df = df[["Close", "Volume"]]
        return df