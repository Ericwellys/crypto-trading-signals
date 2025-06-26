import requests
import pandas as pd
import time
from datetime import datetime

class DataFetcher:
    """Handles data fetching from external APIs"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.timeout = 10
        self.max_retries = 5
        self.retry_delay = 10
    
    def obter_dados_btc(self, limite=100, tentativas=None, atraso=None):
        """Fetch Bitcoin price data from CoinGecko API"""
        if tentativas is None:
            tentativas = self.max_retries
        if atraso is None:
            atraso = self.retry_delay
            
        url = f"{self.base_url}/coins/bitcoin/market_chart"
        params = {"vs_currency": "usd", "days": "1"}
        
        for tentativa in range(tentativas):
            try:
                resposta = requests.get(url, params=params, timeout=self.timeout)
                
                if resposta.status_code == 200:
                    dados = resposta.json()["prices"][-limite:]
                    df = pd.DataFrame(dados, columns=["timestamp", "close"])
                    df["close"] = pd.to_numeric(df["close"])
                    
                    # Convert timestamp to datetime for better plotting
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                    df.set_index("timestamp", inplace=True)
                    
                    return df
                    
                elif resposta.status_code == 429:
                    # Rate limit exceeded
                    print(f"Rate limit exceeded. Waiting {atraso * 2} seconds...")
                    time.sleep(atraso * 2)
                    continue
                    
                else:
                    print(f"Erro ao obter dados: {resposta.status_code} - {resposta.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"Erro na requisição (tentativa {tentativa + 1}): {e}")
            except Exception as e:
                print(f"Erro inesperado: {e}")
            
            if tentativa < tentativas - 1:
                print(f"Tentativa {tentativa + 1} falhou. Aguardando {atraso} segundos...")
                time.sleep(atraso)
        
        print("❌ Não foi possível obter dados do CoinGecko após todas as tentativas.")
        return None
    
    def get_multiple_cryptocurrencies(self, coins=['bitcoin', 'ethereum'], vs_currency='usd', days='1'):
        """Fetch data for multiple cryptocurrencies"""
        results = {}
        
        for coin in coins:
            try:
                url = f"{self.base_url}/coins/{coin}/market_chart"
                params = {"vs_currency": vs_currency, "days": days}
                
                response = requests.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()["prices"]
                    df = pd.DataFrame(data, columns=["timestamp", "close"])
                    df["close"] = pd.to_numeric(df["close"])
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                    df.set_index("timestamp", inplace=True)
                    results[coin] = df
                else:
                    print(f"Erro ao obter dados para {coin}: {response.status_code}")
                    results[coin] = None
                    
                # Small delay to avoid rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Erro ao obter dados para {coin}: {e}")
                results[coin] = None
        
        return results
    
    def get_market_summary(self):
        """Get overall market summary"""
        try:
            url = f"{self.base_url}/global"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()['data']
            else:
                print(f"Erro ao obter resumo do mercado: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erro ao obter resumo do mercado: {e}")
            return None
    
    def get_fear_greed_index(self):
        """Get Fear & Greed Index (from alternative.me API)"""
        try:
            url = "https://api.alternative.me/fng/"
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()['data'][0]
                return {
                    'value': int(data['value']),
                    'classification': data['value_classification'],
                    'timestamp': data['timestamp']
                }
            else:
                print(f"Erro ao obter Fear & Greed Index: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erro ao obter Fear & Greed Index: {e}")
            return None
    
    def check_api_status(self):
        """Check if CoinGecko API is accessible"""
        try:
            url = f"{self.base_url}/ping"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Erro ao verificar status da API: {e}")
            return False
    
    def get_historical_data(self, coin='bitcoin', vs_currency='usd', days=30):
        """Get historical data for longer periods"""
        try:
            url = f"{self.base_url}/coins/{coin}/market_chart"
            params = {"vs_currency": vs_currency, "days": str(days)}
            
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract prices, volumes, and market caps
                prices = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
                volumes = pd.DataFrame(data["total_volumes"], columns=["timestamp", "volume"])
                market_caps = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])
                
                # Merge all data
                df = prices.merge(volumes, on="timestamp").merge(market_caps, on="timestamp")
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df.set_index("timestamp", inplace=True)
                
                return df
            else:
                print(f"Erro ao obter dados históricos: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erro ao obter dados históricos: {e}")
            return None
