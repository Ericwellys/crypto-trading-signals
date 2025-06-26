import pandas as pd
import numpy as np
from datetime import datetime

class TradingAnalyzer:
    """Handles all trading analysis and signal generation logic"""
    
    def __init__(self):
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.ema_short = 9
        self.ema_long = 21
    
    def calculate_indicators(self, df):
        """Calculate technical indicators for the given dataframe"""
        try:
            df = df.copy()
            
            # Ensure close column is numeric
            df["close"] = pd.to_numeric(df["close"])
            
            # Calculate RSI
            df["RSI"] = self._calculate_rsi(df["close"], self.rsi_period)
            
            # Calculate MACD
            macd_line, signal_line, histogram = self._calculate_macd(
                df["close"], self.macd_fast, self.macd_slow, self.macd_signal
            )
            df["MACD_12_26_9"] = macd_line
            df["MACDs_12_26_9"] = signal_line
            df["MACDh_12_26_9"] = histogram
            
            # Calculate EMAs
            df["EMA9"] = self._calculate_ema(df["close"], self.ema_short)
            df["EMA21"] = self._calculate_ema(df["close"], self.ema_long)
            
            # Calculate volume (using price change as proxy since real volume isn't available)
            df["Volume"] = df["close"].diff().abs()
            df["MediaVolume"] = df["Volume"].rolling(20).mean()
            
            return df
            
        except Exception as e:
            print(f"Erro ao calcular indicadores: {e}")
            return df
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_ema(self, prices, period):
        """Calculate Exponential Moving Average"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD indicator"""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def generate_signal(self, df):
        """Generate trading signal based on technical indicators"""
        try:
            if df is None or df.empty or len(df) < 2:
                return None
            
            # Get latest values
            latest = df.iloc[-1]
            
            rsi = latest.get("RSI")
            macd_valor = latest.get("MACD_12_26_9")
            sinal_macd = latest.get("MACDs_12_26_9")
            ema9 = latest.get("EMA9")
            ema21 = latest.get("EMA21")
            preco = latest.get("close")
            volume = latest.get("Volume", 0)
            media_volume = latest.get("MediaVolume", 0)
            
            # Check if all required indicators are available
            if any(pd.isna([rsi, macd_valor, sinal_macd, ema9, ema21, preco])):
                return None
            
            # Trading logic based on indicators
            signal = self._determine_signal(rsi, macd_valor, sinal_macd, ema9, ema21)
            
            return {
                "signal": signal,
                "price": preco,
                "rsi": rsi,
                "macd": macd_valor,
                "macd_signal": sinal_macd,
                "ema9": ema9,
                "ema21": ema21,
                "volume": volume,
                "volume_avg": media_volume
            }
            
        except Exception as e:
            print(f"Erro ao gerar sinal: {e}")
            return None
    
    def _determine_signal(self, rsi, macd_valor, sinal_macd, ema9, ema21):
        """Determine trading signal based on indicator values"""
        # Strong buy signal conditions (more conservative)
        if (rsi > 45 and rsi < 75 and 
            macd_valor > sinal_macd and 
            ema9 > ema21 and 
            (macd_valor - sinal_macd) > 0.001):  # MACD crossover with momentum
            return "🟢 SINAL DE COMPRA"
        
        # Strong sell signal conditions (more conservative)
        elif (rsi < 55 and rsi > 25 and 
              macd_valor < sinal_macd and 
              ema9 < ema21 and 
              (sinal_macd - macd_valor) > 0.001):  # MACD crossover with momentum
            return "🔴 SINAL DE VENDA"
        
        # Wait/Hold signal
        else:
            return "🟡 AGUARDAR"
    
    def format_signal_message(self, signal_data):
        """Format signal data into a message for Telegram"""
        signal = signal_data["signal"]
        preco = signal_data["price"]
        rsi = signal_data["rsi"]
        macd = signal_data["macd"]
        macd_signal = signal_data["macd_signal"]
        ema9 = signal_data["ema9"]
        ema21 = signal_data["ema21"]
        volume = signal_data["volume"]
        volume_avg = signal_data["volume_avg"]
        
        # Only create message for actionable signals (not AGUARDAR)
        if 'AGUARDAR' not in signal:
            if 'COMPRA' in signal:
                emoji = "🚀"
                action = "COMPRA RECOMENDADA"
            else:  # VENDA
                emoji = "📉"
                action = "VENDA RECOMENDADA"
            
            mensagem = f"""{signal}

💰 Bitcoin: ${preco:.2f}
📈 RSI: {rsi:.1f}
📉 MACD: {macd:.4f}
📊 Tendência: {"Alta" if ema9 > ema21 else "Baixa"}

⚡ Sinal Automatizado
⏰ {datetime.now().strftime('%H:%M:%S')}"""
        else:
            mensagem = signal  # Simple message for hold signals
        
        return mensagem
    
    def get_signal_strength(self, signal_data):
        """Calculate signal strength based on indicator convergence"""
        try:
            rsi = signal_data["rsi"]
            macd = signal_data["macd"]
            macd_signal = signal_data["macd_signal"]
            ema9 = signal_data["ema9"]
            ema21 = signal_data["ema21"]
            
            strength = 0
            
            # RSI strength
            if rsi > 70:
                strength += 2  # Strong overbought
            elif rsi > 60:
                strength += 1  # Moderate bullish
            elif rsi < 30:
                strength -= 2  # Strong oversold
            elif rsi < 40:
                strength -= 1  # Moderate bearish
            
            # MACD strength
            macd_diff = abs(macd - macd_signal)
            if macd > macd_signal:
                strength += min(2, macd_diff * 100)  # Bullish MACD
            else:
                strength -= min(2, macd_diff * 100)  # Bearish MACD
            
            # EMA trend strength
            ema_diff = abs(ema9 - ema21) / ema21 * 100
            if ema9 > ema21:
                strength += min(2, ema_diff)  # Uptrend
            else:
                strength -= min(2, ema_diff)  # Downtrend
            
            # Normalize to 0-100 scale
            strength = max(0, min(100, (strength + 10) * 5))
            
            return strength
            
        except Exception as e:
            print(f"Erro ao calcular força do sinal: {e}")
            return 50  # Neutral strength
