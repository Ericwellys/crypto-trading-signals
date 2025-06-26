import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import os
from datetime import datetime, timedelta
from trading_logic import TradingAnalyzer
from telegram_notifier import TelegramNotifier
from data_fetcher import DataFetcher

# Configure Streamlit page
st.set_page_config(
    page_title="Crypto Trading Signals",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'signals_history' not in st.session_state:
    st.session_state.signals_history = []
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True

# Initialize components
@st.cache_resource
def get_components():
    data_fetcher = DataFetcher()
    telegram_notifier = TelegramNotifier()
    trading_analyzer = TradingAnalyzer()
    return data_fetcher, telegram_notifier, trading_analyzer

data_fetcher, telegram_notifier, trading_analyzer = get_components()

def create_price_chart(df):
    """Create interactive price chart with technical indicators"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=('Bitcoin Price & EMAs', 'RSI', 'MACD'),
        row_width=[0.2, 0.2, 0.2]
    )
    
    # Price and EMAs
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df['close'],
            mode='lines',
            name='BTC Price',
            line=dict(color='#ffd700', width=2)
        ),
        row=1, col=1
    )
    
    if 'EMA9' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['EMA9'],
                mode='lines',
                name='EMA 9',
                line=dict(color='#00ff88', width=1)
            ),
            row=1, col=1
        )
    
    if 'EMA21' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['EMA21'],
                mode='lines',
                name='EMA 21',
                line=dict(color='#ff6b6b', width=1)
            ),
            row=1, col=1
        )
    
    # RSI
    if 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='#8884d8', width=2)
            ),
            row=2, col=1
        )
        
        # RSI overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # MACD
    if 'MACD_12_26_9' in df.columns and 'MACDs_12_26_9' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['MACD_12_26_9'],
                mode='lines',
                name='MACD',
                line=dict(color='#82ca9d', width=2)
            ),
            row=3, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['MACDs_12_26_9'],
                mode='lines',
                name='Signal',
                line=dict(color='#ffc658', width=2)
            ),
            row=3, col=1
        )
        
        # MACD histogram
        if 'MACDh_12_26_9' in df.columns:
            fig.add_trace(
                go.Bar(
                    x=df.index, y=df['MACDh_12_26_9'],
                    name='MACD Histogram',
                    marker_color='rgba(128, 132, 216, 0.6)'
                ),
                row=3, col=1
            )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        title_text="Bitcoin Technical Analysis",
        title_x=0.5
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.2)')
    
    return fig

def display_signal_card(signal_data):
    """Display trading signal in a card format"""
    signal_type = signal_data['signal']
    
    if 'COMPRA' in signal_type:
        color = "green"
        icon = "🟢"
    elif 'VENDA' in signal_type:
        color = "red"
        icon = "🔴"
    else:
        color = "orange"
        icon = "🟡"
    
    with st.container():
        st.markdown(f"""
        <div style="padding: 1rem; border-radius: 0.5rem; border-left: 4px solid {color}; background-color: rgba(128, 128, 128, 0.1);">
            <h3>{icon} {signal_data['signal']}</h3>
            <p><strong>Preço:</strong> ${signal_data['price']:.2f}</p>
            <p><strong>RSI:</strong> {signal_data['rsi']:.2f}</p>
            <p><strong>MACD:</strong> {signal_data['macd']:.4f}</p>
            <p><strong>Timestamp:</strong> {signal_data['timestamp']}</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    st.title("📈 Crypto Trading Signals Dashboard")
    st.markdown("---")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configurações")
        
        auto_refresh = st.checkbox("Auto Refresh", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
        
        refresh_interval = st.selectbox(
            "Intervalo de Atualização (minutos)",
            [1, 5, 10, 15, 30],
            index=1
        )
        
        telegram_enabled = st.checkbox("Notificações Telegram", value=True)
        
        if telegram_enabled:
            st.info("📱 Notificações enviadas apenas para sinais de COMPRA e VENDA")
        
        st.markdown("---")
        
        if st.button("🔄 Atualizar Agora"):
            st.rerun()
        
        st.markdown("---")
        
        # Display connection status
        st.subheader("📡 Status da Conexão")
        
        # Test CoinGecko API
        try:
            test_data = data_fetcher.obter_dados_btc(limite=1)
            if test_data is not None:
                st.success("✅ CoinGecko API")
            else:
                st.error("❌ CoinGecko API")
        except:
            st.error("❌ CoinGecko API")
        
        # Test Telegram API
        if telegram_enabled:
            try:
                telegram_notifier.test_connection()
                st.success("✅ Telegram Bot")
            except:
                st.error("❌ Telegram Bot")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Análise Técnica do Bitcoin")
        
        # Fetch and display data
        with st.spinner("Carregando dados do mercado..."):
            df = data_fetcher.obter_dados_btc(limite=100)
            
            if df is not None and not df.empty:
                # Calculate technical indicators
                df_with_indicators = trading_analyzer.calculate_indicators(df)
                
                # Generate trading signal
                signal_data = trading_analyzer.generate_signal(df_with_indicators)
                
                if signal_data:
                    # Update signals history
                    signal_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Add to history if it's a new signal or significant change
                    if not st.session_state.signals_history or \
                       st.session_state.signals_history[-1]['signal'] != signal_data['signal']:
                        st.session_state.signals_history.append(signal_data)
                        
                        # Keep only last 50 signals
                        if len(st.session_state.signals_history) > 50:
                            st.session_state.signals_history = st.session_state.signals_history[-50:]
                        
                        # Send Telegram notification only for BUY/SELL signals (not HOLD)
                        if telegram_enabled and ('COMPRA' in signal_data['signal'] or 'VENDA' in signal_data['signal']):
                            try:
                                message = trading_analyzer.format_signal_message(signal_data)
                                telegram_notifier.enviar_mensagem(message)
                                st.success(f"📱 Notificação enviada: {signal_data['signal']}")
                            except Exception as e:
                                st.warning(f"Erro ao enviar notificação: {e}")
                    
                    # Display current signal
                    with col2:
                        st.subheader("🎯 Sinal Atual")
                        display_signal_card(signal_data)
                        
                        # Current market data
                        st.subheader("💹 Dados do Mercado")
                        
                        metrics_col1, metrics_col2 = st.columns(2)
                        
                        with metrics_col1:
                            st.metric(
                                "Preço BTC",
                                f"${signal_data['price']:.2f}",
                                delta=f"{((signal_data['price'] - df_with_indicators['close'].iloc[-2]) / df_with_indicators['close'].iloc[-2] * 100):.2f}%" if len(df_with_indicators) > 1 else None
                            )
                            
                            st.metric(
                                "RSI (14)",
                                f"{signal_data['rsi']:.2f}",
                                delta="Sobrecomprado" if signal_data['rsi'] > 70 else "Sobrevendido" if signal_data['rsi'] < 30 else "Neutro"
                            )
                        
                        with metrics_col2:
                            st.metric(
                                "MACD",
                                f"{signal_data['macd']:.4f}",
                                delta="Bullish" if signal_data['macd'] > signal_data['macd_signal'] else "Bearish"
                            )
                            
                            st.metric(
                                "EMA 9/21",
                                f"{signal_data['ema9']:.2f}",
                                delta="Trend Up" if signal_data['ema9'] > signal_data['ema21'] else "Trend Down"
                            )
                    
                    # Display chart
                    chart = create_price_chart(df_with_indicators)
                    st.plotly_chart(chart, use_container_width=True)
                    
                    st.session_state.last_update = datetime.now()
                
            else:
                st.error("❌ Não foi possível obter dados do mercado. Verifique sua conexão com a internet.")
    
    # Historical signals section
    st.markdown("---")
    st.subheader("📜 Histórico de Sinais")
    
    if st.session_state.signals_history:
        # Create DataFrame for history
        history_df = pd.DataFrame(st.session_state.signals_history)
        history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
        
        # Display recent signals
        st.dataframe(
            history_df[['timestamp', 'signal', 'price', 'rsi', 'macd']].tail(10),
            use_container_width=True
        )
        
        # Signal distribution chart
        signal_counts = history_df['signal'].value_counts()
        fig_pie = px.pie(
            values=signal_counts.values,
            names=signal_counts.index,
            title="Distribuição de Sinais",
            color_discrete_map={
                'SINAL DE COMPRA': 'green',
                'SINAL DE VENDA': 'red',
                'AGUARDAR': 'orange'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    else:
        st.info("Nenhum sinal gerado ainda. Os sinais aparecerão aqui conforme forem gerados.")
    
    # Footer with last update info
    if st.session_state.last_update:
        st.markdown("---")
        st.caption(f"Última atualização: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Auto refresh
    if auto_refresh:
        time.sleep(refresh_interval * 60)
        st.rerun()

if __name__ == "__main__":
    main()
