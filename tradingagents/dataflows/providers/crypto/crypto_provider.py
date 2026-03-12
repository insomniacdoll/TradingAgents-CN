"""
加密货币数据提供器
支持 yfinance（主要）和 CoinGecko（备用）双数据源
继承自 BaseStockDataProvider
"""

from typing import Optional, Dict, Any, Union
from datetime import datetime, date
import logging
import pandas as pd
import os

from tradingagents.dataflows.providers.base_provider import BaseStockDataProvider
from tradingagents.utils.logging_manager import get_logger

logger = get_logger("providers.crypto")

# yfinance支持的主要加密货币符号映射
CRYPTO_SYMBOL_MAPPING = {
    'BTC': 'BTC-USD', 'ETH': 'ETH-USD', 'ADA': 'ADA-USD', 'SOL': 'SOL-USD',
    'DOT': 'DOT-USD', 'AVAX': 'AVAX-USD', 'MATIC': 'MATIC-USD', 'LINK': 'LINK-USD',
    'UNI': 'UNI-USD', 'AAVE': 'AAVE-USD', 'XRP': 'XRP-USD', 'LTC': 'LTC-USD',
    'BCH': 'BCH-USD', 'DOGE': 'DOGE-USD', 'SHIB': 'SHIB-USD', 'PEPE': 'PEPE-USD',
    'FLOKI': 'FLOKI-USD', 'BNB': 'BNB-USD', 'USDT': 'USDT-USD', 'USDC': 'USDC-USD',
    'TON': 'TON-USD', 'ICP': 'ICP-USD', 'HBAR': 'HBAR-USD', 'THETA': 'THETA-USD',
    'FIL': 'FIL-USD', 'ETC': 'ETC-USD', 'MKR': 'MKR-USD', 'APT': 'APT-USD',
    'LDO': 'LDO-USD', 'OP': 'OP-USD', 'VET': 'VET-USD', 'ALGO': 'ALGO-USD',
    'ATOM': 'ATOM-USD', 'NEAR': 'NEAR-USD', 'FTM': 'FTM-USD', 'CRO': 'CRO-USD',
    'SAND': 'SAND-USD', 'MANA': 'MANA-USD', 'AXS': 'AXS-USD', 'GALA': 'GALA-USD',
    'ENJ': 'ENJ-USD', 'CHZ': 'CHZ-USD', 'BAT': 'BAT-USD', 'ZEC': 'ZEC-USD',
    'DASH': 'DASH-USD', 'XMR': 'XMR-USD',
}

# 加密货币中文名称映射
CRYPTO_NAMES = {
    'BTC': '比特币', 'ETH': '以太坊', 'ADA': '卡尔达诺', 'SOL': '索拉纳',
    'DOT': '波卡', 'AVAX': '雪崩', 'MATIC': 'Polygon', 'LINK': 'Chainlink',
    'UNI': 'Uniswap', 'AAVE': 'Aave', 'XRP': '瑞波币', 'LTC': '莱特币',
    'BCH': '比特币现金', 'DOGE': '狗狗币', 'SHIB': '柴犬币', 'PEPE': 'Pepe',
    'FLOKI': 'FLOKI', 'BNB': '币安币', 'USDT': '泰达币', 'USDC': 'USD Coin',
}


class CryptoProvider(BaseStockDataProvider):
    """
    加密货币数据提供器
    支持双数据源：yfinance（主要）、CoinGecko（备用）
    """

    def __init__(self, use_yfinance: bool = True, api_key: Optional[str] = None):
        """
        初始化加密货币数据提供器

        Args:
            use_yfinance: 是否使用yfinance作为主要数据源
            api_key: CoinGecko API密钥（可选）
        """
        super().__init__("crypto")
        self.use_yfinance = use_yfinance
        self.api_key = api_key or os.getenv("COINGECKO_API_KEY")

        # 初始化yfinance
        self.yf_available = False
        self.yf = None
        if use_yfinance:
            try:
                import yfinance as yf
                self.yf = yf
                self.yf_available = True
                logger.info("✅ yfinance 加载成功，将作为主要加密货币数据源")
            except ImportError:
                logger.warning("⚠️ yfinance 不可用，将尝试使用CoinGecko")

        # 初始化CoinGecko（备用）
        self.coin_gecko_available = False
        if not self.yf_available:
            self._init_coingecko()

        if not self.yf_available and not self.coin_gecko_available:
            logger.error("❌ 没有可用的加密货币数据源")

    async def connect(self) -> bool:
        """
        连接到数据源

        Returns:
            bool: 连接是否成功
        """
        if self.yf_available:
            self.connected = True
            logger.info("✅ 加密货币数据提供器连接成功（yfinance）")
            return True
        elif self.coin_gecko_available:
            self.connected = True
            logger.info("✅ 加密货币数据提供器连接成功（CoinGecko）")
            return True
        return False

    def _get_yf_symbol(self, symbol: str) -> str:
        """
        将加密货币符号转换为yfinance格式

        Args:
            symbol: 加密货币符号（如BTC）

        Returns:
            str: yfinance格式的符号（如BTC-USD）
        """
        return CRYPTO_SYMBOL_MAPPING.get(symbol.upper(), f"{symbol.upper()}-USD")

    def _init_coingecko(self):
        """初始化CoinGecko API连接"""
        try:
            import requests
            self.base_url = "https://api.coingecko.com/api/v3"
            self.session = requests.Session()
            if self.api_key:
                self.session.headers.update({"X-Cg-Pro-Api-Key": self.api_key})
            self.coin_gecko_available = True
            logger.info("✅ CoinGecko 加载成功")
        except ImportError:
            logger.error("❌ CoinGecko 需要 requests 库")

    async def get_stock_basic_info(self, symbol: str = None) -> Optional[Dict[str, Any]]:
        """
        获取加密货币基础信息

        Args:
            symbol: 加密货币代码，为空则返回所有支持的加密货币列表

        Returns:
            单个加密货币信息字典或加密货币列表
        """
        if not symbol:
            return [
                {
                    "code": s,
                    "symbol": s,
                    "name": CRYPTO_NAMES.get(s, s),
                    "market": "CRYPTO"
                }
                for s in CRYPTO_SYMBOL_MAPPING.keys()
            ]

        # 优先使用yfinance
        if self.yf_available:
            try:
                yf_symbol = self._get_yf_symbol(symbol)
                ticker = self.yf.Ticker(yf_symbol)
                info = ticker.info
                if info:
                    return self._format_yf_info(symbol, info)
            except Exception as e:
                logger.warning(f"⚠️ yfinance获取失败: {e}，尝试CoinGecko")

        # 备用CoinGecko
        if self.coin_gecko_available:
            return await self._get_coingecko_basic_info(symbol)

        return None

    def _format_yf_info(self, symbol: str, info: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化yfinance返回的数据

        Args:
            symbol: 加密货币符号
            info: yfinance返回的原始信息

        Returns:
            格式化后的信息字典
        """
        return {
            "code": symbol.upper(),
            "symbol": symbol.upper(),
            "name": info.get("shortName", CRYPTO_NAMES.get(symbol.upper(), symbol.upper())),
            "market": "CRYPTO",
            "exchange": "CRYPTO",
            "currency": "USD",
            # 加密货币使用 regularMarketPrice 而不是 currentPrice
            "current_price": info.get("regularMarketPrice") or info.get("currentPrice"),
            "market_cap": info.get("marketCap"),
            "total_volume": info.get("volume24Hr") or info.get("regularMarketVolume"),
            "circulating_supply": info.get("circulatingSupply"),
            "ath": info.get("fiftyTwoWeekHigh") or info.get("fiftyTwoWeekHigh"),
            "atl": info.get("fiftyTwoWeekLow") or info.get("fiftyTwoWeekLow"),
            "data_source": "yfinance",
            "updated_at": datetime.utcnow(),
        }

    async def _get_coingecko_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        使用CoinGecko获取加密货币基础信息

        Args:
            symbol: 加密货币符号

        Returns:
            格式化后的信息字典
        """
        coin_id = self._get_coingecko_coin_id(symbol)
        if not coin_id:
            return None

        data = self._make_coingecko_request(f"/coins/{coin_id}")
        if not data:
            return None

        market_data = data.get("market_data", {})
        return {
            "code": symbol.upper(),
            "symbol": symbol.upper(),
            "name": data.get("name", CRYPTO_NAMES.get(symbol.upper(), symbol.upper())),
            "market": "CRYPTO",
            "currency": "USD",
            "current_price": market_data.get("current_price", {}).get("usd"),
            "market_cap": market_data.get("market_cap", {}).get("usd"),
            "total_volume": market_data.get("total_volume", {}).get("usd"),
            "price_change_24h": market_data.get("price_change_percentage_24h"),
            "ath": market_data.get("ath", {}).get("usd"),
            "atl": market_data.get("atl", {}).get("usd"),
            "data_source": "coingecko",
            "updated_at": datetime.utcnow(),
        }

    def _get_coingecko_coin_id(self, symbol: str) -> Optional[str]:
        """
        获取CoinGecko的coin ID

        Args:
            symbol: 加密货币符号

        Returns:
            CoinGecko的coin ID
        """
        major_coin_ids = {
            'btc': 'bitcoin', 'eth': 'ethereum', 'ada': 'cardano', 'sol': 'solana',
            'dot': 'polkadot', 'avax': 'avalanche-2', 'matic': 'matic-network',
            'link': 'chainlink', 'uni': 'uniswap', 'aave': 'aave', 'xrp': 'ripple',
            'ltc': 'litecoin', 'doge': 'dogecoin', 'shib': 'shiba-inu', 'bnb': 'binancecoin',
            'usdt': 'tether', 'usdc': 'usd-coin',
        }
        return major_coin_ids.get(symbol.lower())

    def _make_coingecko_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        发送CoinGecko API请求

        Args:
            endpoint: API端点
            params: 请求参数

        Returns:
            返回的JSON数据
        """
        import asyncio
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 429:
                asyncio.sleep(2)
                response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ CoinGecko请求失败: {e}")
            return None

    async def get_stock_quotes(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取加密货币实时行情

        Args:
            symbol: 加密货币代码

        Returns:
            实时行情数据字典
        """
        info = await self.get_stock_basic_info(symbol)
        if not info:
            return None
        return {
            "code": info["code"],
            "symbol": info["symbol"],
            "market": "CRYPTO",
            "close": info.get("current_price"),
            "current_price": info.get("current_price"),
            "volume": info.get("total_volume"),
            "pct_chg": info.get("price_change_24h"),
            "timestamp": datetime.utcnow(),
            "data_source": info.get("data_source", "unknown"),
        }

    async def get_historical_data(
        self,
        symbol: str,
        start_date: Union[str, date],
        end_date: Union[str, date] = None
    ) -> Optional[pd.DataFrame]:
        """
        获取加密货币历史数据

        Args:
            symbol: 加密货币代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            历史数据DataFrame
        """
        if not end_date:
            end_date = date.today()

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # 优先使用yfinance
        if self.yf_available:
            try:
                yf_symbol = self._get_yf_symbol(symbol)
                ticker = self.yf.Ticker(yf_symbol)
                end_date_plus_one = pd.to_datetime(end_date) + pd.DateOffset(days=1)
                df = ticker.history(
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date_plus_one.strftime("%Y-%m-%d")
                )
                if not df.empty:
                    df['date'] = df.index.strftime('%Y-%m-%d')
                    df.set_index('date', inplace=True)
                    logger.info(f"✅ 使用yfinance获取 {symbol} 历史数据: {len(df)} 条")
                    return df
            except Exception as e:
                logger.warning(f"⚠️ yfinance获取历史数据失败: {e}")

        # 备用CoinGecko
        if self.coin_gecko_available:
            return await self._get_coingecko_historical_data(symbol, start_date, end_date)

        return None

    async def _get_coingecko_historical_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> Optional[pd.DataFrame]:
        """
        使用CoinGecko获取历史数据

        Args:
            symbol: 加密货币代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            历史数据DataFrame
        """
        coin_id = self._get_coingecko_coin_id(symbol)
        if not coin_id:
            return None

        start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        end_ts = int(datetime.combine(end_date, datetime.max.time()).timestamp())

        data = self._make_coingecko_request(
            f"/coins/{coin_id}/market_chart/range",
            {
                "vs_currency": "usd",
                "from": start_ts,
                "to": end_ts
            }
        )

        if not data:
            return None

        prices = data.get("prices", [])
        if not prices:
            return None

        df_data = []
        for i, price_point in enumerate(prices):
            dt = datetime.fromtimestamp(price_point[0] / 1000)
            df_data.append({
                "date": dt.strftime("%Y-%m-%d"),
                "datetime": dt,
                "open": price_point[1],
                "high": price_point[1],
                "low": price_point[1],
                "close": price_point[1],
                "volume": data.get("total_volumes", [])[i][1] if i < len(data.get("total_volumes", [])) else None,
                "Adj Close": price_point[1],
            })

        df = pd.DataFrame(df_data)
        df.set_index("date", inplace=True)
        logger.info(f"✅ 使用CoinGecko获取 {symbol} 历史数据: {len(df)} 条")
        return df