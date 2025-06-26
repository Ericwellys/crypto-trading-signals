import requests
import os

class TelegramNotifier:
    """Handles Telegram bot notifications"""
    
    def __init__(self):
        # Get Telegram credentials from environment variables
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Fallback to hardcoded values only for development
        if not self.token:
            self.token = '7474571490:AAFEE8efexplZ7t0QyA2UiTbn4j3PYae8jw'
        if not self.chat_id:
            self.chat_id = '5803697819'
            
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def enviar_mensagem(self, mensagem):
        """Send message to Telegram chat"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id, 
                'text': mensagem,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=payload, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                print(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Erro ao enviar mensagem para o Telegram: {e}")
            return False
    
    def test_connection(self):
        """Test Telegram bot connection"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    return True
            
            return False
            
        except Exception as e:
            print(f"Erro ao testar conexão Telegram: {e}")
            return False
    
    def send_formatted_signal(self, signal_data):
        """Send formatted trading signal to Telegram"""
        try:
            signal = signal_data["signal"]
            preco = signal_data["price"]
            rsi = signal_data["rsi"]
            
            # Create formatted message with emojis
            if "COMPRA" in signal:
                emoji = "🚀"
                action = "BUY SIGNAL"
            elif "VENDA" in signal:
                emoji = "📉"
                action = "SELL SIGNAL"
            else:
                emoji = "⏸️"
                action = "HOLD"
            
            message = f"""
{emoji} <b>{action}</b> {emoji}

📊 <b>Bitcoin Trading Signal</b>
💰 Price: <b>${preco:.2f}</b>
📈 RSI: <b>{rsi:.2f}</b>
📉 MACD: <b>{signal_data['macd']:.4f}</b>

⚡ <i>Automated Trading Signal</i>
🕐 {signal_data.get('timestamp', 'Now')}
            """
            
            return self.enviar_mensagem(message)
            
        except Exception as e:
            print(f"Erro ao enviar sinal formatado: {e}")
            return False
    
    def send_alert(self, alert_type, message):
        """Send different types of alerts"""
        try:
            alerts = {
                'error': '🚨',
                'warning': '⚠️',
                'info': 'ℹ️',
                'success': '✅'
            }
            
            emoji = alerts.get(alert_type, 'ℹ️')
            formatted_message = f"{emoji} <b>{alert_type.upper()}</b>\n\n{message}"
            
            return self.enviar_mensagem(formatted_message)
            
        except Exception as e:
            print(f"Erro ao enviar alerta: {e}")
            return False
