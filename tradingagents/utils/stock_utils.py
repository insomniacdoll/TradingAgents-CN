"""
股票工具函数
提供股票代码识别、分类和处理功能
"""

import re
from typing import Dict, Tuple, Optional
from enum import Enum

# 导入统一日志系统
from tradingagents.utils.logging_init import get_logger
logger = get_logger("default")


class StockMarket(Enum):
    """股票市场枚举"""
    CHINA_A = "china_a"      # 中国A股
    HONG_KONG = "hong_kong"  # 港股
    US = "us"                # 美股
    CRYPTO = "crypto"        # 加密货币
    UNKNOWN = "unknown"      # 未知


class StockUtils:
    """股票工具类"""
    
    @staticmethod
    def identify_stock_market(ticker: str) -> StockMarket:
        """
        识别股票代码所属市场

        Args:
            ticker: 股票代码

        Returns:
            StockMarket: 股票市场类型
        """
        if not ticker:
            return StockMarket.UNKNOWN

        ticker = str(ticker).strip().upper()

        # 加密货币：优先检测
        if StockUtils.is_crypto_symbol(ticker):
            return StockMarket.CRYPTO

        # 中国A股：6位数字
        if re.match(r'^\d{6}$', ticker):
            return StockMarket.CHINA_A

        # 港股：4-5位数字.HK 或 纯4-5位数字（支持0700.HK、09988.HK、00700、9988格式）
        if re.match(r'^\d{4,5}\.HK$', ticker) or re.match(r'^\d{4,5}$', ticker):
            return StockMarket.HONG_KONG

        # 美股：1-5位字母（排除已识别的加密货币）
        if re.match(r'^[A-Z]{1,5}$', ticker):
            return StockMarket.US

        return StockMarket.UNKNOWN
    
    @staticmethod
    def is_crypto_symbol(ticker: str) -> bool:
        """
        判断是否为加密货币

        Args:
            ticker: 加密货币代码

        Returns:
            bool: 是否为加密货币
        """
        if not ticker:
            return False

        ticker = str(ticker).strip().upper()

        # 从interface导入crypto符号映射
        try:
            from tradingagents.dataflows.interface import CRYPTO_SYMBOL_MAPPING
            return ticker in CRYPTO_SYMBOL_MAPPING
        except ImportError:
            # 备用白名单
            crypto_symbols = {
                'BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'AAVE',
                'XRP', 'LTC', 'BCH', 'DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BNB', 'USDT', 'USDC',
                'TON', 'ICP', 'HBAR', 'THETA', 'FIL', 'ETC', 'MKR', 'APT', 'LDO', 'OP',
            }
            return ticker in crypto_symbols

    @staticmethod
    def get_crypto_name(ticker: str) -> str:
        """
        获取加密货币中文名称

        Args:
            ticker: 加密货币代码

        Returns:
            str: 加密货币中文名称
        """
        try:
            from tradingagents.dataflows.interface import CRYPTO_NAMES
            return CRYPTO_NAMES.get(ticker.upper(), f"加密货币{ticker}")
        except ImportError:
            return f"加密货币{ticker}"

    @staticmethod
    def is_china_stock(ticker: str) -> bool:
        """
        判断是否为中国A股

        Args:
            ticker: 股票代码

        Returns:
            bool: 是否为中国A股
        """
        return StockUtils.identify_stock_market(ticker) == StockMarket.CHINA_A

    @staticmethod
    def is_hk_stock(ticker: str) -> bool:
        """
        判断是否为港股

        Args:
            ticker: 股票代码

        Returns:
            bool: 是否为港股
        """
        return StockUtils.identify_stock_market(ticker) == StockMarket.HONG_KONG

    @staticmethod
    def is_us_stock(ticker: str) -> bool:
        """
        判断是否为美股

        Args:
            ticker: 股票代码

        Returns:
            bool: 是否为美股
        """
        return StockUtils.identify_stock_market(ticker) == StockMarket.US
    
    @staticmethod
    def get_currency_info(ticker: str) -> Tuple[str, str]:
        """
        根据股票代码获取货币信息
        
        Args:
            ticker: 股票代码
            
        Returns:
            Tuple[str, str]: (货币名称, 货币符号)
        """
        market = StockUtils.identify_stock_market(ticker)
        
        if market == StockMarket.CHINA_A:
            return "人民币", "¥"
        elif market == StockMarket.HONG_KONG:
            return "港币", "HK$"
        elif market == StockMarket.US:
            return "美元", "$"
        else:
            return "未知", "?"
    
    @staticmethod
    def get_data_source(ticker: str) -> str:
        """
        根据股票代码获取推荐的数据源
        
        Args:
            ticker: 股票代码
            
        Returns:
            str: 数据源名称
        """
        market = StockUtils.identify_stock_market(ticker)
        
        if market == StockMarket.CHINA_A:
            return "china_unified"  # 使用统一的中国股票数据源
        elif market == StockMarket.HONG_KONG:
            return "yahoo_finance"  # 港股使用Yahoo Finance
        elif market == StockMarket.US:
            return "yahoo_finance"  # 美股使用Yahoo Finance
        else:
            return "unknown"
    
    @staticmethod
    def normalize_hk_ticker(ticker: str) -> str:
        """
        标准化港股代码格式
        
        Args:
            ticker: 原始港股代码
            
        Returns:
            str: 标准化后的港股代码
        """
        if not ticker:
            return ticker
            
        ticker = str(ticker).strip().upper()
        
        # 如果是纯4-5位数字，添加.HK后缀
        if re.match(r'^\d{4,5}$', ticker):
            return f"{ticker}.HK"

        # 如果已经是正确格式，直接返回
        if re.match(r'^\d{4,5}\.HK$', ticker):
            return ticker
            
        return ticker
    
    @staticmethod
    def get_market_info(ticker: str) -> Dict:
        """
        获取股票市场的详细信息

        Args:
            ticker: 股票代码

        Returns:
            Dict: 市场信息字典
        """
        market = StockUtils.identify_stock_market(ticker)

        market_info_map = {
            StockMarket.CHINA_A: {
                'market_name': 'A股',
                'market_code': 'CN',
                'currency_name': '人民币',
                'currency_symbol': '¥',
                'is_china': True,
                'is_hk': False,
                'is_us': False,
                'is_crypto': False,
            },
            StockMarket.HONG_KONG: {
                'market_name': '港股',
                'market_code': 'HK',
                'currency_name': '港币',
                'currency_symbol': 'HK$',
                'is_china': False,
                'is_hk': True,
                'is_us': False,
                'is_crypto': False,
            },
            StockMarket.US: {
                'market_name': '美股',
                'market_code': 'US',
                'currency_name': '美元',
                'currency_symbol': '$',
                'is_china': False,
                'is_hk': False,
                'is_us': True,
                'is_crypto': False,
            },
            StockMarket.CRYPTO: {
                'market_name': '加密货币',
                'market_code': 'CRYPTO',
                'currency_name': '美元',
                'currency_symbol': '$',
                'is_china': False,
                'is_hk': False,
                'is_us': False,
                'is_crypto': True,
            },
            StockMarket.UNKNOWN: {
                'market_name': '未知',
                'market_code': 'UNKNOWN',
                'currency_name': '未知',
                'currency_symbol': '',
                'is_china': False,
                'is_hk': False,
                'is_us': False,
                'is_crypto': False,
            },
        }

        market_info = market_info_map.get(market, market_info_map[StockMarket.UNKNOWN])
        market_info['ticker'] = ticker
        market_info['market'] = market.value

        return market_info


# 便捷函数，保持向后兼容
def is_china_stock(ticker: str) -> bool:
    """判断是否为中国A股（向后兼容）"""
    return StockUtils.is_china_stock(ticker)


def is_hk_stock(ticker: str) -> bool:
    """判断是否为港股"""
    return StockUtils.is_hk_stock(ticker)


def is_us_stock(ticker: str) -> bool:
    """判断是否为美股"""
    return StockUtils.is_us_stock(ticker)


def get_stock_market_info(ticker: str) -> Dict:
    """获取股票市场信息"""
    return StockUtils.get_market_info(ticker)
