"""
加密货币数据提供器
使用 yfinance（主要）和 CoinGecko（备用）获取加密货币数据
"""

try:
    from .crypto_provider import CryptoProvider, CRYPTO_SYMBOL_MAPPING
    CRYPTO_PROVIDER_AVAILABLE = True
except ImportError:
    CryptoProvider = None
    CRYPTO_SYMBOL_MAPPING = None
    CRYPTO_PROVIDER_AVAILABLE = False

__all__ = [
    'CryptoProvider',
    'CRYPTO_SYMBOL_MAPPING',
    'CRYPTO_PROVIDER_AVAILABLE',
]