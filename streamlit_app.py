import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Stocks & Options Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Password Gate ────────────────────────────────────────────────────────────
def check_password():
    """Returns True if the user has entered the correct password."""
    correct_password = st.secrets.get("APP_PASSWORD", "")
    if not correct_password:
        return True  # No password configured, allow access

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("📈 Stocks & Options Dashboard")
    st.markdown("This dashboard is password-protected.")
    password = st.text_input("Enter password", type="password")
    if st.button("Login", type="primary"):
        if password == correct_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


if not check_password():
    st.stop()

# ── Styling ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #16213e;
    }
    .green { color: #00c853; }
    .red { color: #ff1744; }
    div[data-testid="stMetric"] {
        background-color: #0e1117;
        border: 1px solid #1e2a3a;
        border-radius: 8px;
        padding: 12px 16px;
    }
</style>
""", unsafe_allow_html=True)


# ── Tradier API Helper ───────────────────────────────────────────────────────
class TradierAPI:
    def __init__(self, api_key: str, use_sandbox: bool = True):
        self.api_key = api_key
        self.base_url = (
            "https://sandbox.tradier.com/v1"
            if use_sandbox
            else "https://api.tradier.com/v1"
        )
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }

    def _get(self, endpoint: str, params: dict = None) -> dict | None:
        try:
            r = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params or {},
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            st.error(f"API error: {e}")
            return None

    # ── Quotes ───────────────────────────────────────────────────────────
    def get_quote(self, symbol: str) -> dict | None:
        data = self._get("/markets/quotes", {"symbols": symbol, "greeks": "false"})
        if data and "quotes" in data and "quote" in data["quotes"]:
            return data["quotes"]["quote"]
        return None

    # ── Historical prices ────────────────────────────────────────────────
    def get_history(
        self, symbol: str, interval: str = "daily", start: str = None, end: str = None
    ) -> pd.DataFrame | None:
        if not start:
            start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not end:
            end = datetime.now().strftime("%Y-%m-%d")
        data = self._get(
            "/markets/history",
            {
                "symbol": symbol,
                "interval": interval,
                "start": start,
                "end": end,
            },
        )
        if data and "history" in data and data["history"] and "day" in data["history"]:
            days = data["history"]["day"]
            if isinstance(days, dict):
                days = [days]
            df = pd.DataFrame(days)
            df["date"] = pd.to_datetime(df["date"])
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            return df
        return None

    # ── Option expirations ───────────────────────────────────────────────
    def get_option_expirations(self, symbol: str) -> list | None:
        data = self._get("/markets/options/expirations", {"symbol": symbol})
        if data and "expirations" in data and data["expirations"]:
            exp = data["expirations"].get("date", [])
            if isinstance(exp, str):
                return [exp]
            return exp
        return None

    # ── Option chain ─────────────────────────────────────────────────────
    def get_option_chain(
        self, symbol: str, expiration: str, option_type: str = "all"
    ) -> pd.DataFrame | None:
        data = self._get(
            "/markets/options/chains",
            {
                "symbol": symbol,
                "expiration": expiration,
                "greeks": "true",
            },
        )
        if data and "options" in data and data["options"] and "option" in data["options"]:
            options = data["options"]["option"]
            if isinstance(options, dict):
                options = [options]
            df = pd.DataFrame(options)
            if option_type != "all":
                df = df[df["option_type"] == option_type]
            return df
        return None

    # ── Time & sales (intraday) ──────────────────────────────────────────
    def get_timesales(
        self, symbol: str, interval: str = "5min", start: str = None, end: str = None
    ) -> pd.DataFrame | None:
        params = {"symbol": symbol, "interval": interval}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        data = self._get("/markets/timesales", params)
        if data and "series" in data and data["series"] and "data" in data["series"]:
            records = data["series"]["data"]
            if isinstance(records, dict):
                records = [records]
            df = pd.DataFrame(records)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            for col in ["open", "high", "low", "close", "volume", "price"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            return df
        return None

    # ── Clock (market status) ────────────────────────────────────────────
    def get_clock(self) -> dict | None:
        data = self._get("/markets/clock")
        if data and "clock" in data:
            return data["clock"]
        return None


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    # Load API key from Streamlit Secrets, with optional manual override
    default_key = st.secrets.get("TRADIER_API_KEY", "")
    if default_key:
        api_key = default_key
        st.success("API key loaded from secrets")
    else:
        api_key = st.text_input(
            "Tradier API Key",
            type="password",
            help="Enter your Tradier API token",
        )
    use_sandbox = st.toggle("Use Sandbox (Paper Trading)", value=False)

    st.divider()

    st.header("🔍 Lookup")
    symbol = st.text_input("Ticker Symbol", value="AAPL").upper().strip()

    st.divider()

    st.header("📊 Chart Settings")
    chart_period = st.selectbox(
        "History Period",
        ["1M", "3M", "6M", "1Y", "2Y"],
        index=3,
    )
    chart_interval = st.selectbox(
        "Interval",
        ["daily", "weekly", "monthly"],
        index=0,
    )
    chart_type = st.selectbox("Chart Type", ["Candlestick", "Line", "OHLC"], index=0)

    st.divider()

    st.header("📉 Overlays (on price)")
    overlay_indicators = st.multiselect(
        "Select overlays",
        ["Bollinger Bands", "EMA 9", "EMA 21", "SMA 50", "Keltner Channels", "VWAP"],
        default=["Bollinger Bands", "SMA 50"],
    )

    st.header("📊 Sub-Indicators")
    sub_indicators = st.multiselect(
        "Select indicators",
        ["RSI", "MACD", "Momentum", "Stochastic", "CCI", "ADX", "ATR", "OBV"],
        default=["RSI", "MACD"],
    )

# ── Period mapping ───────────────────────────────────────────────────────────
PERIOD_DAYS = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365, "2Y": 730}

# ── Main ─────────────────────────────────────────────────────────────────────
st.title("📈 Stocks & Options Dashboard")

if not api_key:
    st.info(
        "Enter your **Tradier API key** in the sidebar to get started. "
        "You can get a free sandbox key at [developer.tradier.com](https://developer.tradier.com/)."
    )
    st.stop()

api = TradierAPI(api_key, use_sandbox)

# ── Market Status ────────────────────────────────────────────────────────────
clock = api.get_clock()
if clock:
    state = clock.get("state", "unknown")
    color = "🟢" if state == "open" else "🔴"
    st.caption(f"{color} Market: **{state.upper()}** | {clock.get('description', '')} | {clock.get('date', '')}")

# ── Quote ────────────────────────────────────────────────────────────────────
quote = api.get_quote(symbol)

if not quote:
    st.error(f"Could not fetch data for **{symbol}**. Check the symbol and API key.")
    st.stop()

# ── Header metrics ───────────────────────────────────────────────────────────
last_price = quote.get("last", quote.get("close", 0))
change = quote.get("change", 0) or 0
change_pct = quote.get("change_percentage", 0) or 0
prev_close = quote.get("prevclose", 0)

st.subheader(f"{quote.get('description', symbol)} ({symbol})")

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Last Price", f"${last_price:,.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
col2.metric("Open", f"${quote.get('open', 0) or 0:,.2f}")
col3.metric("High", f"${quote.get('high', 0) or 0:,.2f}")
col4.metric("Low", f"${quote.get('low', 0) or 0:,.2f}")
col5.metric("Volume", f"{quote.get('volume', 0) or 0:,.0f}")
col6.metric("Avg Volume", f"{quote.get('average_volume', 0) or 0:,.0f}")

# ── Extended details ─────────────────────────────────────────────────────────
with st.expander("📋 Full Quote Details", expanded=False):
    detail_cols = st.columns(4)
    details = {
        "Previous Close": f"${prev_close or 0:,.2f}",
        "52-Week High": f"${quote.get('week_52_high', 0) or 0:,.2f}",
        "52-Week Low": f"${quote.get('week_52_low', 0) or 0:,.2f}",
        "Bid": f"${quote.get('bid', 0) or 0:,.2f} x {quote.get('bidsize', 0) or 0}",
        "Ask": f"${quote.get('ask', 0) or 0:,.2f} x {quote.get('asksize', 0) or 0}",
        "Last Volume": f"{quote.get('last_volume', 0) or 0:,}",
        "Trade Date": str(quote.get("trade_date", "N/A")),
        "Exchange": quote.get("exch", "N/A"),
        "Type": quote.get("type", "N/A"),
    }
    for i, (label, value) in enumerate(details.items()):
        detail_cols[i % 4].markdown(f"**{label}:** {value}")

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_chart, tab_intraday, tab_options, tab_greeks = st.tabs(
    ["📈 Price Chart", "⏱️ Intraday", "🔗 Options Chain", "🇬🇷 Greeks & Analysis"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Historical Price Chart
# ══════════════════════════════════════════════════════════════════════════════
with tab_chart:
    days = PERIOD_DAYS[chart_period]
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    hist = api.get_history(symbol, interval=chart_interval, start=start_date)

    if hist is not None and not hist.empty:
        # ── Calculate ALL indicators ─────────────────────────────────

        # Bollinger Bands (20-period, 2 std dev)
        hist["BB_MID"] = hist["close"].rolling(20).mean()
        hist["BB_STD"] = hist["close"].rolling(20).std()
        hist["BB_UPPER"] = hist["BB_MID"] + 2 * hist["BB_STD"]
        hist["BB_LOWER"] = hist["BB_MID"] - 2 * hist["BB_STD"]

        # EMAs
        hist["EMA9"] = hist["close"].ewm(span=9, adjust=False).mean()
        hist["EMA21"] = hist["close"].ewm(span=21, adjust=False).mean()
        hist["SMA50"] = hist["close"].rolling(50).mean()

        # Keltner Channels (20-period EMA, 1.5x ATR)
        hist["KC_MID"] = hist["close"].ewm(span=20, adjust=False).mean()
        tr = pd.concat([
            hist["high"] - hist["low"],
            (hist["high"] - hist["close"].shift()).abs(),
            (hist["low"] - hist["close"].shift()).abs(),
        ], axis=1).max(axis=1)
        hist["ATR14"] = tr.rolling(14).mean()
        hist["KC_UPPER"] = hist["KC_MID"] + 1.5 * hist["ATR14"]
        hist["KC_LOWER"] = hist["KC_MID"] - 1.5 * hist["ATR14"]

        # RSI (14-period)
        delta_c = hist["close"].diff()
        gain = delta_c.where(delta_c > 0, 0.0).rolling(14).mean()
        loss = (-delta_c.where(delta_c < 0, 0.0)).rolling(14).mean()
        rs = gain / loss.replace(0, float("nan"))
        hist["RSI"] = 100 - (100 / (1 + rs))

        # MACD (12, 26, 9)
        ema12 = hist["close"].ewm(span=12, adjust=False).mean()
        ema26 = hist["close"].ewm(span=26, adjust=False).mean()
        hist["MACD"] = ema12 - ema26
        hist["MACD_SIGNAL"] = hist["MACD"].ewm(span=9, adjust=False).mean()
        hist["MACD_HIST"] = hist["MACD"] - hist["MACD_SIGNAL"]

        # Momentum (10-period rate of change)
        hist["MOM"] = hist["close"].pct_change(10) * 100

        # Stochastic Oscillator (14-period)
        low14 = hist["low"].rolling(14).min()
        high14 = hist["high"].rolling(14).max()
        hist["STOCH_K"] = ((hist["close"] - low14) / (high14 - low14)) * 100
        hist["STOCH_D"] = hist["STOCH_K"].rolling(3).mean()

        # CCI (20-period)
        tp = (hist["high"] + hist["low"] + hist["close"]) / 3
        tp_sma = tp.rolling(20).mean()
        import numpy as np
        tp_mad = tp.rolling(20).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
        hist["CCI"] = (tp - tp_sma) / (0.015 * tp_mad)

        # ADX (14-period)
        plus_dm = hist["high"].diff()
        minus_dm = -hist["low"].diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)
        atr14_smooth = tr.ewm(span=14, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(span=14, adjust=False).mean() / atr14_smooth)
        minus_di = 100 * (minus_dm.ewm(span=14, adjust=False).mean() / atr14_smooth)
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, float("nan")))
        hist["ADX"] = dx.ewm(span=14, adjust=False).mean()
        hist["PLUS_DI"] = plus_di
        hist["MINUS_DI"] = minus_di

        # OBV (On-Balance Volume)
        obv_sign = hist["close"].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        hist["OBV"] = (obv_sign * hist["volume"]).cumsum()

        # VWAP (cumulative)
        hist["VWAP"] = (((hist["high"] + hist["low"] + hist["close"]) / 3) * hist["volume"]).cumsum() / hist["volume"].cumsum()

        # ── Build dynamic subplot layout ─────────────────────────────
        n_subs = len(sub_indicators)
        total_rows = 2 + n_subs  # price + volume + each sub-indicator

        price_height = 0.40
        vol_height = 0.10
        remaining = 1.0 - price_height - vol_height
        sub_height = remaining / max(n_subs, 1)

        row_heights = [price_height, vol_height] + [sub_height] * n_subs
        subplot_titles = ["", "Volume"] + sub_indicators

        fig = make_subplots(
            rows=total_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.025,
            row_heights=row_heights,
            subplot_titles=subplot_titles,
        )

        # ── Row 1: Price chart ───────────────────────────────────────
        if chart_type == "Candlestick":
            fig.add_trace(
                go.Candlestick(
                    x=hist["date"], open=hist["open"], high=hist["high"],
                    low=hist["low"], close=hist["close"], name="Price",
                ), row=1, col=1,
            )
        elif chart_type == "Line":
            fig.add_trace(
                go.Scatter(
                    x=hist["date"], y=hist["close"], mode="lines",
                    name="Close", line=dict(color="#00b4d8", width=2),
                ), row=1, col=1,
            )
        else:
            fig.add_trace(
                go.Ohlc(
                    x=hist["date"], open=hist["open"], high=hist["high"],
                    low=hist["low"], close=hist["close"], name="Price",
                ), row=1, col=1,
            )

        # ── Overlay indicators on price ──────────────────────────────
        if "Bollinger Bands" in overlay_indicators:
            fig.add_trace(go.Scatter(x=hist["date"], y=hist["BB_UPPER"], mode="lines", name="BB Upper", line=dict(color="#636efa", width=1, dash="dash")), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist["date"], y=hist["BB_MID"], mode="lines", name="BB Mid", line=dict(color="#ffd60a", width=1, dash="dot")), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist["date"], y=hist["BB_LOWER"], mode="lines", name="BB Lower", line=dict(color="#636efa", width=1, dash="dash"), fill="tonexty", fillcolor="rgba(99,110,250,0.08)"), row=1, col=1)

        if "EMA 9" in overlay_indicators:
            fig.add_trace(go.Scatter(x=hist["date"], y=hist["EMA9"], mode="lines", name="EMA 9", line=dict(color="#00e5ff", width=1)), row=1, col=1)

        if "EMA 21" in overlay_indicators:
            fig.add_trace(go.Scatter(x=hist["date"], y=hist["EMA21"], mode="lines", name="EMA 21", line=dict(color="#76ff03", width=1)), row=1, col=1)

        if "SMA 50" in overlay_indicators:
            fig.add_trace(go.Scatter(x=hist["date"], y=hist["SMA50"], mode="lines", name="SMA 50", line=dict(color="#ff6b6b", width=1, dash="dot")), row=1, col=1)

        if "Keltner Channels" in overlay_indicators:
            fig.add_trace(go.Scatter(x=hist["date"], y=hist["KC_UPPER"], mode="lines", name="KC Upper", line=dict(color="#ff9800", width=1, dash="dash")), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist["date"], y=hist["KC_MID"], mode="lines", name="KC Mid", line=dict(color="#ff9800", width=1, dash="dot")), row=1, col=1)
            fig.add_trace(go.Scatter(x=hist["date"], y=hist["KC_LOWER"], mode="lines", name="KC Lower", line=dict(color="#ff9800", width=1, dash="dash"), fill="tonexty", fillcolor="rgba(255,152,0,0.06)"), row=1, col=1)

        if "VWAP" in overlay_indicators:
            fig.add_trace(go.Scatter(x=hist["date"], y=hist["VWAP"], mode="lines", name="VWAP", line=dict(color="#ffeb3b", width=1.5)), row=1, col=1)

        # ── Row 2: Volume ────────────────────────────────────────────
        vol_colors = ["#00c853" if row.close >= row.open else "#ff1744" for _, row in hist.iterrows()]
        fig.add_trace(go.Bar(x=hist["date"], y=hist["volume"], marker_color=vol_colors, name="Volume", opacity=0.5), row=2, col=1)

        # ── Sub-indicator rows ───────────────────────────────────────
        for i, ind in enumerate(sub_indicators):
            row_num = 3 + i

            if ind == "RSI":
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["RSI"], mode="lines", name="RSI", line=dict(color="#e040fb", width=1.5)), row=row_num, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=0.8, row=row_num, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=0.8, row=row_num, col=1)
                fig.update_yaxes(title_text="RSI", range=[0, 100], row=row_num, col=1)

            elif ind == "MACD":
                macd_colors = ["#00c853" if v >= 0 else "#ff1744" for v in hist["MACD_HIST"].fillna(0)]
                fig.add_trace(go.Bar(x=hist["date"], y=hist["MACD_HIST"], marker_color=macd_colors, name="MACD Hist", opacity=0.5), row=row_num, col=1)
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["MACD"], mode="lines", name="MACD", line=dict(color="#00b4d8", width=1.5)), row=row_num, col=1)
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["MACD_SIGNAL"], mode="lines", name="Signal", line=dict(color="#ff6b6b", width=1)), row=row_num, col=1)
                fig.add_hline(y=0, line_color="white", line_width=0.5, row=row_num, col=1)
                fig.update_yaxes(title_text="MACD", row=row_num, col=1)

            elif ind == "Momentum":
                mom_colors = ["#00c853" if v >= 0 else "#ff1744" for v in hist["MOM"].fillna(0)]
                fig.add_trace(go.Bar(x=hist["date"], y=hist["MOM"], marker_color=mom_colors, name="Momentum %", opacity=0.7), row=row_num, col=1)
                fig.add_hline(y=0, line_color="white", line_width=0.5, row=row_num, col=1)
                fig.update_yaxes(title_text="Mom %", row=row_num, col=1)

            elif ind == "Stochastic":
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["STOCH_K"], mode="lines", name="%K", line=dict(color="#00b4d8", width=1.5)), row=row_num, col=1)
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["STOCH_D"], mode="lines", name="%D", line=dict(color="#ff6b6b", width=1)), row=row_num, col=1)
                fig.add_hline(y=80, line_dash="dash", line_color="red", line_width=0.8, row=row_num, col=1)
                fig.add_hline(y=20, line_dash="dash", line_color="green", line_width=0.8, row=row_num, col=1)
                fig.update_yaxes(title_text="Stoch", range=[0, 100], row=row_num, col=1)

            elif ind == "CCI":
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["CCI"], mode="lines", name="CCI", line=dict(color="#ab47bc", width=1.5)), row=row_num, col=1)
                fig.add_hline(y=100, line_dash="dash", line_color="red", line_width=0.8, row=row_num, col=1)
                fig.add_hline(y=-100, line_dash="dash", line_color="green", line_width=0.8, row=row_num, col=1)
                fig.add_hline(y=0, line_color="white", line_width=0.5, row=row_num, col=1)
                fig.update_yaxes(title_text="CCI", row=row_num, col=1)

            elif ind == "ADX":
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["ADX"], mode="lines", name="ADX", line=dict(color="#ffeb3b", width=1.5)), row=row_num, col=1)
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["PLUS_DI"], mode="lines", name="+DI", line=dict(color="#00c853", width=1, dash="dot")), row=row_num, col=1)
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["MINUS_DI"], mode="lines", name="-DI", line=dict(color="#ff1744", width=1, dash="dot")), row=row_num, col=1)
                fig.add_hline(y=25, line_dash="dash", line_color="gray", line_width=0.8, row=row_num, col=1)
                fig.update_yaxes(title_text="ADX", row=row_num, col=1)

            elif ind == "ATR":
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["ATR14"], mode="lines", name="ATR (14)", line=dict(color="#ff9800", width=1.5)), row=row_num, col=1)
                fig.update_yaxes(title_text="ATR", row=row_num, col=1)

            elif ind == "OBV":
                fig.add_trace(go.Scatter(x=hist["date"], y=hist["OBV"], mode="lines", name="OBV", line=dict(color="#26c6da", width=1.5), fill="tozeroy", fillcolor="rgba(38,198,218,0.1)"), row=row_num, col=1)
                fig.update_yaxes(title_text="OBV", row=row_num, col=1)

        # ── Layout ───────────────────────────────────────────────────
        chart_height = 500 + (n_subs * 150)
        fig.update_layout(
            template="plotly_dark",
            height=chart_height,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_rangeslider_visible=False,
            showlegend=True,
            legend=dict(orientation="h", y=1.02, x=0),
        )
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Vol", row=2, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # Summary stats
        scol1, scol2, scol3, scol4 = st.columns(4)
        period_return = (
            (hist["close"].iloc[-1] - hist["close"].iloc[0]) / hist["close"].iloc[0] * 100
        )
        scol1.metric("Period Return", f"{period_return:+.2f}%")
        scol2.metric("Period High", f"${hist['high'].max():,.2f}")
        scol3.metric("Period Low", f"${hist['low'].min():,.2f}")
        scol4.metric("Avg Daily Volume", f"{hist['volume'].mean():,.0f}")
    else:
        st.warning("No historical data available.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Intraday
# ══════════════════════════════════════════════════════════════════════════════
with tab_intraday:
    intraday_interval = st.selectbox(
        "Intraday Interval", ["1min", "5min", "15min"], index=1, key="intraday_int"
    )
    ts = api.get_timesales(symbol, interval=intraday_interval)

    if ts is not None and not ts.empty:
        fig_intra = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.75, 0.25],
        )

        fig_intra.add_trace(
            go.Scatter(
                x=ts["timestamp"],
                y=ts["price"] if "price" in ts.columns else ts["close"],
                mode="lines",
                name="Price",
                line=dict(color="#00b4d8", width=1.5),
            ),
            row=1,
            col=1,
        )

        if "volume" in ts.columns:
            fig_intra.add_trace(
                go.Bar(
                    x=ts["timestamp"],
                    y=ts["volume"],
                    name="Volume",
                    marker_color="#5e60ce",
                    opacity=0.5,
                ),
                row=2,
                col=1,
            )

        fig_intra.update_layout(
            template="plotly_dark",
            height=500,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_intra, use_container_width=True)

        # VWAP-like info
        if "price" in ts.columns and "volume" in ts.columns:
            total_vol = ts["volume"].sum()
            if total_vol > 0:
                vwap = (ts["price"] * ts["volume"]).sum() / total_vol
                icol1, icol2, icol3 = st.columns(3)
                icol1.metric("VWAP", f"${vwap:,.2f}")
                icol2.metric("Day Range", f"${ts['price'].min():,.2f} – ${ts['price'].max():,.2f}")
                icol3.metric("Total Volume", f"{total_vol:,.0f}")
    else:
        st.info("No intraday data available (market may be closed).")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Options Chain
# ══════════════════════════════════════════════════════════════════════════════
with tab_options:
    expirations = api.get_option_expirations(symbol)

    if not expirations:
        st.info(f"No option expirations found for **{symbol}**.")
    else:
        ocol1, ocol2 = st.columns([1, 1])
        selected_exp = ocol1.selectbox("Expiration Date", expirations)
        option_view = ocol2.radio(
            "View", ["All", "Calls Only", "Puts Only"], horizontal=True
        )

        opt_type_map = {"All": "all", "Calls Only": "call", "Puts Only": "put"}
        chain = api.get_option_chain(symbol, selected_exp, opt_type_map[option_view])

        if chain is not None and not chain.empty:
            # Days to expiry
            dte = (pd.to_datetime(selected_exp) - pd.Timestamp.now()).days
            st.caption(f"**{selected_exp}** — {dte} days to expiration — {len(chain)} contracts")

            # Display columns
            display_cols = [
                "option_type", "strike", "last", "bid", "ask", "volume",
                "open_interest", "change", "change_percentage",
            ]
            # Add greeks if available
            greek_cols_in_chain = []
            for g in ["greeks"]:
                if g in chain.columns:
                    # Tradier nests greeks; flatten them
                    greeks_df = pd.json_normalize(chain["greeks"].dropna())
                    if not greeks_df.empty:
                        for gc in ["delta", "gamma", "theta", "vega", "rho", "mid_iv"]:
                            if gc in greeks_df.columns:
                                chain.loc[chain["greeks"].notna(), gc] = greeks_df[gc].values
                                greek_cols_in_chain.append(gc)

            show_cols = [c for c in display_cols + greek_cols_in_chain if c in chain.columns]
            display_df = chain[show_cols].copy()

            # Formatting
            for col in ["strike", "last", "bid", "ask", "change"]:
                if col in display_df.columns:
                    display_df[col] = pd.to_numeric(display_df[col], errors="coerce")
            for col in ["volume", "open_interest"]:
                if col in display_df.columns:
                    display_df[col] = pd.to_numeric(display_df[col], errors="coerce").fillna(0).astype(int)

            display_df.columns = [c.replace("_", " ").title() for c in display_df.columns]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=500,
            )

            # Open Interest & Volume chart
            if "strike" in chain.columns:
                chain["strike"] = pd.to_numeric(chain["strike"], errors="coerce")
                chain["open_interest"] = pd.to_numeric(chain.get("open_interest", 0), errors="coerce").fillna(0)
                chain["volume"] = pd.to_numeric(chain.get("volume", 0), errors="coerce").fillna(0)

                st.subheader("Open Interest by Strike")
                oi_fig = go.Figure()

                calls = chain[chain["option_type"] == "call"] if "option_type" in chain.columns else pd.DataFrame()
                puts = chain[chain["option_type"] == "put"] if "option_type" in chain.columns else pd.DataFrame()

                if not calls.empty:
                    oi_fig.add_trace(
                        go.Bar(
                            x=calls["strike"],
                            y=calls["open_interest"],
                            name="Calls OI",
                            marker_color="#00c853",
                            opacity=0.7,
                        )
                    )
                if not puts.empty:
                    oi_fig.add_trace(
                        go.Bar(
                            x=puts["strike"],
                            y=puts["open_interest"],
                            name="Puts OI",
                            marker_color="#ff1744",
                            opacity=0.7,
                        )
                    )

                # Mark current price
                oi_fig.add_vline(
                    x=last_price,
                    line_dash="dash",
                    line_color="yellow",
                    annotation_text=f"${last_price:.2f}",
                )
                oi_fig.update_layout(
                    template="plotly_dark",
                    barmode="group",
                    height=350,
                    margin=dict(l=0, r=0, t=30, b=0),
                )
                st.plotly_chart(oi_fig, use_container_width=True)

                # Put/Call ratio
                total_call_oi = calls["open_interest"].sum() if not calls.empty else 0
                total_put_oi = puts["open_interest"].sum() if not puts.empty else 0
                pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0

                rc1, rc2, rc3 = st.columns(3)
                rc1.metric("Total Call OI", f"{total_call_oi:,.0f}")
                rc2.metric("Total Put OI", f"{total_put_oi:,.0f}")
                rc3.metric("Put/Call Ratio", f"{pcr:.3f}")
        else:
            st.warning("No option chain data returned.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Greeks & Analysis
# ══════════════════════════════════════════════════════════════════════════════
with tab_greeks:
    st.subheader("Options Greeks Visualization")

    expirations_g = api.get_option_expirations(symbol)
    if not expirations_g:
        st.info("No option expirations available for Greeks analysis.")
    else:
        gcol1, gcol2 = st.columns(2)
        sel_exp_g = gcol1.selectbox("Expiration", expirations_g, key="greeks_exp")
        sel_greek = gcol2.selectbox("Greek", ["delta", "gamma", "theta", "vega"], key="greek_sel")

        chain_g = api.get_option_chain(symbol, sel_exp_g)

        if chain_g is not None and not chain_g.empty and "greeks" in chain_g.columns:
            # Flatten greeks
            valid_mask = chain_g["greeks"].notna()
            if valid_mask.any():
                greeks_df = pd.json_normalize(chain_g.loc[valid_mask, "greeks"])
                for gc in ["delta", "gamma", "theta", "vega", "rho", "mid_iv"]:
                    if gc in greeks_df.columns:
                        chain_g.loc[valid_mask, gc] = greeks_df[gc].values

                chain_g["strike"] = pd.to_numeric(chain_g["strike"], errors="coerce")

                if sel_greek in chain_g.columns:
                    chain_g[sel_greek] = pd.to_numeric(chain_g[sel_greek], errors="coerce")

                    calls_g = chain_g[chain_g["option_type"] == "call"].sort_values("strike")
                    puts_g = chain_g[chain_g["option_type"] == "put"].sort_values("strike")

                    greek_fig = go.Figure()
                    if not calls_g.empty:
                        greek_fig.add_trace(
                            go.Scatter(
                                x=calls_g["strike"],
                                y=calls_g[sel_greek],
                                mode="lines+markers",
                                name=f"Call {sel_greek.title()}",
                                line=dict(color="#00c853"),
                                marker=dict(size=4),
                            )
                        )
                    if not puts_g.empty:
                        greek_fig.add_trace(
                            go.Scatter(
                                x=puts_g["strike"],
                                y=puts_g[sel_greek],
                                mode="lines+markers",
                                name=f"Put {sel_greek.title()}",
                                line=dict(color="#ff1744"),
                                marker=dict(size=4),
                            )
                        )

                    greek_fig.add_vline(
                        x=last_price,
                        line_dash="dash",
                        line_color="yellow",
                        annotation_text=f"Spot ${last_price:.2f}",
                    )
                    greek_fig.update_layout(
                        template="plotly_dark",
                        height=450,
                        xaxis_title="Strike Price",
                        yaxis_title=sel_greek.title(),
                        margin=dict(l=0, r=0, t=30, b=0),
                    )
                    st.plotly_chart(greek_fig, use_container_width=True)

                # Implied Volatility Smile
                if "mid_iv" in chain_g.columns:
                    st.subheader("Implied Volatility Smile")
                    chain_g["mid_iv"] = pd.to_numeric(chain_g["mid_iv"], errors="coerce")

                    iv_fig = go.Figure()
                    calls_iv = chain_g[chain_g["option_type"] == "call"].sort_values("strike")
                    puts_iv = chain_g[chain_g["option_type"] == "put"].sort_values("strike")

                    if not calls_iv.empty:
                        iv_fig.add_trace(
                            go.Scatter(
                                x=calls_iv["strike"],
                                y=calls_iv["mid_iv"] * 100,
                                mode="lines+markers",
                                name="Call IV",
                                line=dict(color="#00c853"),
                                marker=dict(size=4),
                            )
                        )
                    if not puts_iv.empty:
                        iv_fig.add_trace(
                            go.Scatter(
                                x=puts_iv["strike"],
                                y=puts_iv["mid_iv"] * 100,
                                mode="lines+markers",
                                name="Put IV",
                                line=dict(color="#ff1744"),
                                marker=dict(size=4),
                            )
                        )

                    iv_fig.add_vline(
                        x=last_price,
                        line_dash="dash",
                        line_color="yellow",
                        annotation_text=f"Spot ${last_price:.2f}",
                    )
                    iv_fig.update_layout(
                        template="plotly_dark",
                        height=400,
                        xaxis_title="Strike Price",
                        yaxis_title="Implied Volatility (%)",
                        margin=dict(l=0, r=0, t=30, b=0),
                    )
                    st.plotly_chart(iv_fig, use_container_width=True)
            else:
                st.warning("No Greeks data available for this expiration.")
        else:
            st.warning("No option chain or Greeks data available.")

# ── Footer ───────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"Data provided by [Tradier](https://tradier.com) | "
    f"{'Sandbox' if use_sandbox else 'Production'} mode | "
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
