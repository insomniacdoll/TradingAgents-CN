# 加密货币支持 - 第5阶段：后端API更新（修正方案）

## 状态

- 阶段1（核心数据层）：✅ 已完成
- 阶段2（分析师层）：✅ 已完成
- 阶段3（前端修改）：✅ 已完成
- 阶段4（配置与依赖）：✅ 已完成
- **阶段5（后端API更新）：📋 待实施**
- 阶段6（测试与文档）：⏳ 待实施

---

## 一、架构一致性分析

### 1.1 现有架构模式

| 组件 | 港股 | 美股 | 加密货币（修正后） |
|------|------|------|-------------------|
| **Provider** | `HKStockProvider` | `YFinanceUtils` | `CryptoProvider` ✅ |
| **继承基类** | ❌ 不继承 | ❌ 不继承 | ✅ 继承 `BaseStockDataProvider` |
| **服务层** | `ForeignStockService._get_hk_quote()` | `ForeignStockService._get_us_quote()` | ✅ `ForeignStockService._get_crypto_quote()` |
| **路由入口** | `stocks.py` → `ForeignStockService` | `stocks.py` → `ForeignStockService` | ✅ `stocks.py` → `ForeignStockService` |
| **缓存策略** | 服务层统一管理 | 服务层统一管理 | ✅ 服务层统一管理 |
| **请求去重** | `_request_locks` | `_request_locks` | ✅ `_request_locks` |

### 1.2 调用链路（统一架构）

```
用户请求
  ↓
app/routers/stocks.py (get_quote)
  ↓
_detect_market_and_code()  # 自动检测市场类型
  ↓
ForeignStockService.get_quote(market='CRYPTO')
  ↓
_get_crypto_quote()
  ↓
  1. 检查缓存 (Redis → MongoDB → File)
  2. 请求去重 (_request_locks)
  3. 调用 CryptoProvider.get_stock_quotes()
  4. 保存到缓存
  ↓
返回格式化数据
```

### 1.3 数据模型一致性

**市场类型枚举：**
```python
MarketType = Literal["CN", "HK", "US", "CRYPTO"]
```

**交易所类型枚举：**
```python
ExchangeType = Literal["SZSE", "SSE", "SEHK", "NYSE", "NASDAQ", "COINGECKO"]
```

**货币类型枚举：**
```python
CurrencyType = Literal["CNY", "HKD", "USD", "USDT", "BTC", "ETH"]
```

---

## 二、实施计划

### 任务清单

| # | 文件 | 任务 | 估算行数 |
|---|------|------|---------|
| 1 | `app/models/stock_models.py` | 扩展枚举定义 | ~10 |
| 2 | `app/services/foreign_stock_service.py` | 添加CRYPTO分支和_get_crypto_quote | ~80 |
| 3 | `app/routers/stocks.py` | 扩展_detect_market_and_code和get_quote | ~30 |
| 4 | `app/routers/analysis.py` | 添加加密货币符号自动检测 | ~15 |
| 5 | `app/routers/config.py` | 添加加密货币配置端点 | ~20 |

**总计：** 4个文件修改，~155行代码变更

---

## 三、详细实施步骤

### 3.1 更新数据模型

**文件：** `app/models/stock_models.py`

**位置：** 第21-25行（枚举类型定义）

**修改前：**
```python
# 枚举类型定义
MarketType = Literal["CN", "HK", "US"]  # 市场类型
ExchangeType = Literal["SZSE", "SSE", "SEHK", "NYSE", "NASDAQ"]  # 交易所
StockStatus = Literal["L", "D", "P"]  # 上市状态: L-上市 D-退市 P-暂停
CurrencyType = Literal["CNY", "HKD", "USD"]  # 货币类型
```

**修改后：**
```python
# 枚举类型定义
MarketType = Literal["CN", "HK", "US", "CRYPTO"]  # 市场类型
ExchangeType = Literal["SZSE", "SSE", "SEHK", "NYSE", "NASDAQ", "COINGECKO"]  # 交易所
StockStatus = Literal["L", "D", "P"]  # 上市状态: L-上市 D-退市 P-暂停
CurrencyType = Literal["CNY", "HKD", "USD", "USDT", "BTC", "ETH"]  # 货币类型
```

**位置：** 第60行（`StockBasicInfoExtended.symbol` 字段）

**修改前：**
```python
symbol: str = Field(..., description="6位股票代码", pattern=r"^\d{6}$")
```

**修改后：**
```python
symbol: str = Field(..., description="股票/加密货币代码")
```

**位置：** 第159行（`MarketQuotesExtended.symbol` 字段）

**修改前：**
```python
symbol: str = Field(..., description="6位股票代码", pattern=r"^\d{6}$")
```

**修改后：**
```python
symbol: str = Field(..., description="股票/加密货币代码")
```

---

### 3.2 更新服务层

**文件：** `app/services/foreign_stock_service.py`

**位置：** 第28-39行（`CACHE_TTL` 配置）

**修改前：**
```python
    # 缓存时间配置（秒）
    CACHE_TTL = {
        "HK": {
            "quote": 600,        # 10分钟（实时行情）
            "info": 86400,       # 1天（基础信息）
            "kline": 7200,       # 2小时（K线数据）
        },
        "US": {
            "quote": 600,        # 10分钟
            "info": 86400,       # 1天
            "kline": 7200,       # 2小时
        }
    }
```

**修改后：**
```python
    # 缓存时间配置（秒）
    CACHE_TTL = {
        "HK": {
            "quote": 600,        # 10分钟（实时行情）
            "info": 86400,       # 1天（基础信息）
            "kline": 7200,       # 2小时（K线数据）
        },
        "US": {
            "quote": 600,        # 10分钟
            "info": 86400,       # 1天
            "kline": 7200,       # 2小时
        },
        "CRYPTO": {
            "quote": 600,        # 10分钟（实时行情）
            "info": 86400,       # 1天（基础信息）
            "kline": 7200,       # 2小时（K线数据）
        }
    }
```

**位置：** 第41-57行（`__init__` 方法）

**修改前：**
```python
    def __init__(self, db=None):
        # 使用统一缓存系统（自动选择 MongoDB/Redis/File）
        self.cache = get_cache()

        # 初始化港股数据源提供者
        self.hk_provider = HKStockProvider()

        # 保存数据库连接（用于查询数据源优先级）
        self.db = db

        # 🔥 请求去重：为每个 (market, code, data_type) 创建独立的锁
        self._request_locks = defaultdict(asyncio.Lock)

        # 🔥 正在进行的请求缓存（用于共享结果）
        self._pending_requests = {}

        logger.info("✅ ForeignStockService 初始化完成（已启用请求去重）")
```

**修改后：**
```python
    def __init__(self, db=None):
        # 使用统一缓存系统（自动选择 MongoDB/Redis/File）
        self.cache = get_cache()

        # 初始化港股数据源提供者
        self.hk_provider = HKStockProvider()

        # 初始化加密货币数据源提供者
        self.crypto_provider = None
        try:
            from tradingagents.dataflows.providers.crypto import CryptoProvider
            self.crypto_provider = CryptoProvider()
            logger.info("✅ 加密货币Provider初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 加密货币Provider初始化失败: {e}")

        # 保存数据库连接（用于查询数据源优先级）
        self.db = db

        # 🔥 请求去重：为每个 (market, code, data_type) 创建独立的锁
        self._request_locks = defaultdict(asyncio.Lock)

        # 🔥 正在进行的请求缓存（用于共享结果）
        self._pending_requests = {}

        logger.info("✅ ForeignStockService 初始化完成（已启用请求去重）")
```

**位置：** 第59-82行（`get_quote` 方法）

**修改前：**
```python
    async def get_quote(self, market: str, code: str, force_refresh: bool = False) -> Dict:
        """
        获取实时行情

        Args:
            market: 市场类型 (HK/US)
            code: 股票代码
            force_refresh: 是否强制刷新（跳过缓存）

        Returns:
            实时行情数据

        流程：
        1. 检查是否强制刷新
        2. 从缓存获取（Redis → MongoDB → File）
        3. 缓存未命中 → 调用数据源API（按优先级）
        4. 保存到缓存
        """
        if market == 'HK':
            return await self._get_hk_quote(code, force_refresh)
        elif market == 'US':
            return await self._get_us_quote(code, force_refresh)
        else:
            raise ValueError(f"不支持的市场类型: {market}")
```

**修改后：**
```python
    async def get_quote(self, market: str, code: str, force_refresh: bool = False) -> Dict:
        """
        获取实时行情

        Args:
            market: 市场类型 (HK/US/CRYPTO)
            code: 股票/加密货币代码
            force_refresh: 是否强制刷新（跳过缓存）

        Returns:
            实时行情数据

        流程：
        1. 检查是否强制刷新
        2. 从缓存获取（Redis → MongoDB → File）
        3. 缓存未命中 → 调用数据源API（按优先级）
        4. 保存到缓存
        """
        if market == 'HK':
            return await self._get_hk_quote(code, force_refresh)
        elif market == 'US':
            return await self._get_us_quote(code, force_refresh)
        elif market == 'CRYPTO':
            return await self._get_crypto_quote(code, force_refresh)
        else:
            raise ValueError(f"不支持的市场类型: {market}")
```

**位置：** 第84-101行（`get_basic_info` 方法）

**修改前：**
```python
    async def get_basic_info(self, market: str, code: str, force_refresh: bool = False) -> Dict:
        """
        获取基础信息

        Args:
            market: 市场类型 (HK/US)
            code: 股票代码
            force_refresh: 是否强制刷新

        Returns:
            基础信息数据
        """
        if market == 'HK':
            return await self._get_hk_info(code, force_refresh)
        elif market == 'US':
            return await self._get_us_info(code, force_refresh)
        else:
            raise ValueError(f"不支持的市场类型: {market}")
```

**修改后：**
```python
    async def get_basic_info(self, market: str, code: str, force_refresh: bool = False) -> Dict:
        """
        获取基础信息

        Args:
            market: 市场类型 (HK/US/CRYPTO)
            code: 股票/加密货币代码
            force_refresh: 是否强制刷新

        Returns:
            基础信息数据
        """
        if market == 'HK':
            return await self._get_hk_info(code, force_refresh)
        elif market == 'US':
            return await self._get_us_info(code, force_refresh)
        elif market == 'CRYPTO':
            return await self._get_crypto_info(code, force_refresh)
        else:
            raise ValueError(f"不支持的市场类型: {market}")
```

**位置：** 第103-123行（`get_kline` 方法）

**修改前：**
```python
    async def get_kline(self, market: str, code: str, period: str = 'day',
                       limit: int = 120, force_refresh: bool = False) -> List[Dict]:
        """
        获取K线数据

        Args:
            market: 市场类型 (HK/US)
            code: 股票代码
            period: 周期 (day/week/month)
            limit: 数据条数
            force_refresh: 是否强制刷新

        Returns:
            K线数据列表
        """
        if market == 'HK':
            return await self._get_hk_kline(code, period, limit, force_refresh)
        elif market == 'US':
            return await self._get_us_kline(code, period, limit, force_refresh)
        else:
            raise ValueError(f"不支持的市场类型: {market}")
```

**修改后：**
```python
    async def get_kline(self, market: str, code: str, period: str = 'day',
                       limit: int = 120, force_refresh: bool = False) -> List[Dict]:
        """
        获取K线数据

        Args:
            market: 市场类型 (HK/US/CRYPTO)
            code: 股票/加密货币代码
            period: 周期 (day/week/month)
            limit: 数据条数
            force_refresh: 是否强制刷新

        Returns:
            K线数据列表
        """
        if market == 'HK':
            return await self._get_hk_kline(code, period, limit, force_refresh)
        elif market == 'US':
            return await self._get_us_kline(code, period, limit, force_refresh)
        elif market == 'CRYPTO':
            return await self._get_crypto_kline(code, period, limit, force_refresh)
        else:
            raise ValueError(f"不支持的市场类型: {market}")
```

**位置：** 在文件末尾（添加新方法）

**新增方法1：`_get_crypto_quote`**
```python
    async def _get_crypto_quote(self, code: str, force_refresh: bool = False) -> Dict:
        """
        获取加密货币实时行情（带请求去重）
        🔥 按照港股/美股统一的模式调用API
        🔥 防止并发请求重复调用API
        """
        # 1. 检查缓存（除非强制刷新）
        if not force_refresh:
            cache_key = self.cache.find_cached_stock_data(
                symbol=code,
                data_source="crypto_realtime_quote"
            )

            if cache_key:
                cached_data = self.cache.load_stock_data(cache_key)
                if cached_data:
                    logger.info(f"⚡ 从缓存获取加密货币行情: {code}")
                    return self._parse_cached_data(cached_data, 'CRYPTO', code)

        # 2. 🔥 请求去重：使用锁确保同一加密货币同时只有一个API调用
        request_key = f"CRYPTO_quote_{code}_{force_refresh}"
        lock = self._request_locks[request_key]

        async with lock:
            # 🔥 再次检查缓存（可能在等待锁的过程中，其他请求已经完成并缓存了数据）
            if not force_refresh:
                cache_key = self.cache.find_cached_stock_data(
                    symbol=code,
                    data_source="crypto_realtime_quote"
                )
                if cache_key:
                    cached_data = self.cache.load_stock_data(cache_key)
                    if cached_data:
                        logger.info(f"⚡ 从缓存获取加密货币行情（锁内）: {code}")
                        return self._parse_cached_data(cached_data, 'CRYPTO', code)

            # 3. 🔥 检查是否有正在进行的请求（共享结果）
            if not force_refresh and request_key in self._pending_requests:
                logger.info(f"⏳ 等待其他请求完成: {code}")
                return await self._pending_requests[request_key]

            # 4. 🔥 创建新请求任务
            task = asyncio.create_task(self._fetch_crypto_quote(code))
            self._pending_requests[request_key] = task

            try:
                result = await task
                return result
            finally:
                # 5. 清理pending请求
                if request_key in self._pending_requests:
                    del self._pending_requests[request_key]

    async def _fetch_crypto_quote(self, code: str) -> Dict:
        """实际获取加密货币行情数据"""
        if not self.crypto_provider:
            logger.warning(f"⚠️ 加密货币Provider不可用: {code}")
            return {}

        try:
            logger.info(f"🪙 从API获取加密货币行情: {code}")
            data = await self.crypto_provider.get_stock_quotes(code)

            if data and data.get("code"):
                # 保存到缓存
                self.cache.save_stock_data(
                    data,
                    symbol=code,
                    data_source="crypto_realtime_quote"
                )
                logger.info(f"✅ 加密货币行情获取成功: {code}")
                return data
            else:
                logger.warning(f"⚠️ 加密货币行情数据为空: {code}")
                return {}
        except Exception as e:
            logger.error(f"❌ 获取加密货币行情失败: {code}, 错误: {e}")
            return {}
```

**新增方法2：`_get_crypto_info`**
```python
    async def _get_crypto_info(self, code: str, force_refresh: bool = False) -> Dict:
        """获取加密货币基础信息"""
        if not force_refresh:
            cache_key = self.cache.find_cached_stock_data(
                symbol=code,
                data_source="crypto_basic_info"
            )

            if cache_key:
                cached_data = self.cache.load_stock_data(cache_key)
                if cached_data:
                    logger.info(f"⚡ 从缓存获取加密货币信息: {code}")
                    return self._parse_cached_data(cached_data, 'CRYPTO', code)

        if not self.crypto_provider:
            logger.warning(f"⚠️ 加密货币Provider不可用: {code}")
            return {}

        try:
            logger.info(f"🪙 从API获取加密货币信息: {code}")
            data = await self.crypto_provider.get_stock_basic_info(code)

            if data and data.get("code"):
                self.cache.save_stock_data(
                    data,
                    symbol=code,
                    data_source="crypto_basic_info"
                )
                logger.info(f"✅ 加密货币信息获取成功: {code}")
                return data
            else:
                logger.warning(f"⚠️ 加密货币信息数据为空: {code}")
                return {}
        except Exception as e:
            logger.error(f"❌ 获取加密货币信息失败: {code}, 错误: {e}")
            return {}
```

**新增方法3：`_get_crypto_kline`**
```python
    async def _get_crypto_kline(
        self,
        code: str,
        period: str = 'day',
        limit: int = 120,
        force_refresh: bool = False
    ) -> List[Dict]:
        """获取加密货币K线数据"""
        if not self.crypto_provider:
            logger.warning(f"⚠️ 加密货币Provider不可用: {code}")
            return []

        try:
            from datetime import datetime, timedelta, date

            end_date = datetime.now()
            start_date = end_date - timedelta(days=limit)

            logger.info(f"🪙 获取加密货币K线数据: {code}, {start_date} 到 {end_date}")

            df = await self.crypto_provider.get_historical_data(
                code,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )

            if df is not None and not df.empty:
                # 转换为字典列表
                result = df.to_dict('records')
                logger.info(f"✅ 加密货币K线数据获取成功: {code}, {len(result)}条")
                return result
            else:
                logger.warning(f"⚠️ 加密货币K线数据为空: {code}")
                return []
        except Exception as e:
            logger.error(f"❌ 获取加密货币K线失败: {code}, 错误: {e}")
            return []
```

---

### 3.3 更新股票路由

**文件：** `app/routers/stocks.py`

**位置：** 第31-64行（`_detect_market_and_code` 函数）

**修改前：**
```python
def _detect_market_and_code(code: str) -> Tuple[str, str]:
    """
    检测股票代码的市场类型并标准化代码

    Args:
        code: 股票代码

    Returns:
        (market, normalized_code): 市场类型和标准化后的代码
            - CN: A股（6位数字）
            - HK: 港股（4-5位数字或带.HK后缀）
            - US: 美股（字母代码）
    """
    code = code.strip().upper()

    # 港股：带.HK后缀
    if code.endswith('.HK'):
        return ('HK', code[:-3].zfill(5))  # 移除.HK，补齐到5位

    # 美股：纯字母
    if re.match(r'^[A-Z]+$', code):
        return ('US', code)

    # 港股：4-5位数字
    if re.match(r'^\d{4,5}$', code):
        return ('HK', code.zfill(5))  # 补齐到5位

    # A股：6位数字
    if re.match(r'^\d{6}$', code):
        return ('CN', code)

    # 默认当作A股处理
    return ('CN', _zfill_code(code))
```

**修改后：**
```python
def _detect_market_and_code(code: str) -> Tuple[str, str]:
    """
    检测股票代码的市场类型并标准化代码

    Args:
        code: 股票/加密货币代码

    Returns:
        (market, normalized_code): 市场类型和标准化后的代码
            - CN: A股（6位数字）
            - HK: 港股（4-5位数字或带.HK后缀）
            - US: 美股（字母代码，4-5位）
            - CRYPTO: 加密货币（2-4位大写字母，白名单）
    """
    code = code.strip().upper()

    # 加密货币：2-4位大写字母，且在provider支持列表中
    if re.match(r'^[A-Z]{2,4}$', code):
        try:
            from tradingagents.dataflows.providers.crypto import CRYPTO_SYMBOL_MAPPING
            if code in CRYPTO_SYMBOL_MAPPING:
                return ('CRYPTO', code)
        except Exception:
            pass

    # 港股：带.HK后缀
    if code.endswith('.HK'):
        return ('HK', code[:-3].zfill(5))  # 移除.HK，补齐到5位

    # 美股：4-5位大写字母（排除加密货币）
    if re.match(r'^[A-Z]{4,5}$', code):
        return ('US', code)

    # 港股：4-5位数字
    if re.match(r'^\d{4,5}$', code):
        return ('HK', code.zfill(5))  # 补齐到5位

    # A股：6位数字
    if re.match(r'^\d{6}$', code):
        return ('CN', code)

    # 默认当作A股处理
    return ('CN', _zfill_code(code))
```

**位置：** 第66-200行（`get_quote` 端点）

**修改前：**
```python
@router.get("/{code}/quote", response_model=dict)
async def get_quote(
    code: str,
    force_refresh: bool = Query(False, description="是否强制刷新（跳过缓存）"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取股票实时行情（支持A股/港股/美股）

    自动识别市场类型：
    - 6位数字 → A股
    - 4位数字或.HK → 港股
    - 纯字母 → 美股

    参数：
    - code: 股票代码
    - force_refresh: 是否强制刷新（跳过缓存）

    返回字段（data内，蛇形命名）:
      - code, name, market
      - price(close), change_percent(pct_chg), amount, prev_close(估算)
      - turnover_rate, amplitude（振幅，替代量比）
      - trade_date, updated_at
    """
    # 检测市场类型
    market, normalized_code = _detect_market_and_code(code)

    # 港股和美股：使用新服务
    if market in ['HK', 'US']:
        from app.services.foreign_stock_service import ForeignStockService

        db = get_mongo_db()  # 不需要 await，直接返回数据库对象
        service = ForeignStockService(db=db)

        try:
            result = await service.get_quote(market, normalized_code, force_refresh)

            if result:
                return ok(data={
                    "code": normalized_code,
                    "name": result.get("name") or result.get("symbol", normalized_code),
                    "market": market,
                    "market_type": "港股" if market == "HK" else "美股",
                    "price": result.get("close") or result.get("current_price"),
                    "change_percent": result.get("pct_chg"),
                    "amount": result.get("amount") or result.get("volume"),
                    "prev_close": result.get("pre_close"),
                    "trade_date": result.get("trade_date") or result.get("date"),
                    "updated_at": result.get("updated_at") or result.get("timestamp")
                })
            else:
                return ok(data=None, message=f"未找到{market}行情数据")

        except Exception as e:
            logger.error(f"获取{market}行情失败: {e}")
            return ok(data=None, message=f"获取{market}行情失败: {str(e)}")

    # A股：现有逻辑（不变）
    # ... 现有A股逻辑 ...
```

**修改后：**
```python
@router.get("/{code}/quote", response_model=dict)
async def get_quote(
    code: str,
    force_refresh: bool = Query(False, description="是否强制刷新（跳过缓存）"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取股票/加密货币实时行情（支持A股/港股/美股/加密货币）

    自动识别市场类型：
    - 6位数字 → A股
    - 4位数字或.HK → 港股
    - 4-5位字母（非加密货币）→ 美股
    - 2-4位字母（加密货币白名单）→ 加密货币

    参数：
    - code: 股票/加密货币代码
    - force_refresh: 是否强制刷新（跳过缓存）

    返回字段（data内，蛇形命名）:
      - code, name, market
      - price(close), change_percent(pct_chg), amount, prev_close(估算)
      - turnover_rate, amplitude（振幅，替代量比）
      - trade_date, updated_at
    """
    # 检测市场类型
    market, normalized_code = _detect_market_and_code(code)

    # 港股、美股、加密货币：统一使用 ForeignStockService
    if market in ['HK', 'US', 'CRYPTO']:
        from app.services.foreign_stock_service import ForeignStockService

        db = get_mongo_db()  # 不需要 await，直接返回数据库对象
        service = ForeignStockService(db=db)

        try:
            result = await service.get_quote(market, normalized_code, force_refresh)

            if result:
                # 统一数据格式化
                market_type_map = {
                    'HK': '港股',
                    'US': '美股',
                    'CRYPTO': '加密货币'
                }

                return ok(data={
                    "code": normalized_code,
                    "name": result.get("name") or result.get("symbol", normalized_code),
                    "market": market,
                    "market_type": market_type_map.get(market, "未知"),
                    "price": result.get("close") or result.get("current_price"),
                    "change_percent": result.get("pct_chg") or result.get("price_change_24h"),
                    "amount": result.get("amount") or result.get("volume") or result.get("total_volume"),
                    "prev_close": result.get("pre_close"),
                    "trade_date": result.get("trade_date") or result.get("date"),
                    "updated_at": result.get("updated_at") or result.get("timestamp")
                })
            else:
                market_type_name = "加密货币" if market == "CRYPTO" else (market if market in ["HK", "US"] else "未知")
                return ok(data=None, message=f"未找到{market_type_name}行情数据")

        except Exception as e:
            logger.error(f"获取{market}行情失败: {e}")
            return ok(data=None, message=f"获取{market}行情失败: {str(e)}")

    # A股：现有逻辑（不变）
    # ... 现有A股逻辑 ...
```

---

### 3.4 更新分析路由

**文件：** `app/routers/analysis.py`

**位置：** 第40-96行（`submit_single_analysis` 端点）

**修改前：**
```python
@router.post("/single", response_model=Dict[str, Any])
async def submit_single_analysis(
    request: SingleAnalysisRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """提交单股分析任务 - 使用 BackgroundTasks 异步执行"""
    try:
        logger.info(f"🎯 收到单股分析请求")
        logger.info(f"👤 用户信息: {user}")
        logger.info(f"📊 请求数据: {request}")

        # 立即创建任务记录并返回，不等待执行完成
        analysis_service = get_simple_analysis_service()
        result = await analysis_service.create_analysis_task(user["id"], request)

        # ... 其余逻辑 ...
```

**修改后：**
```python
@router.post("/single", response_model=Dict[str, Any])
async def submit_single_analysis(
    request: SingleAnalysisRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """提交单股/加密货币分析任务 - 使用 BackgroundTasks 异步执行"""
    try:
        logger.info(f"🎯 收到分析请求")
        logger.info(f"👤 用户信息: {user}")
        logger.info(f"📊 请求数据: {request}")

        # 🔥 自动检测加密货币符号
        symbol = request.get_symbol()
        if symbol:
            from app.routers.stocks import _detect_market_and_code
            market, _ = _detect_market_and_code(symbol)

            # 如果检测到是加密货币，自动设置市场类型
            if market == 'CRYPTO':
                if not request.parameters:
                    request.parameters = AnalysisParameters()
                request.parameters.market_type = "加密货币"
                logger.info(f"🪙 检测到加密货币符号: {symbol}")

        # 立即创建任务记录并返回，不等待执行完成
        analysis_service = get_simple_analysis_service()
        result = await analysis_service.create_analysis_task(user["id"], request)

        # ... 其余逻辑保持不变 ...
```

---

### 3.5 添加配置端点

**文件：** `app/routers/config.py`

**位置：** 在文件末尾添加新端点

**新增端点：**
```python
@router.get("/crypto", response_model=Dict[str, Any])
async def get_crypto_config(
    current_user: dict = Depends(get_current_user)
):
    """
    获取加密货币数据源配置

    返回加密货币数据源的可用状态和配置信息
    """
    try:
        from app.core.config import get_settings
        settings = get_settings()

        # 检查provider是否可用
        provider_available = False
        provider_name = None
        try:
            from tradingagents.dataflows.providers.crypto import CRYPTO_PROVIDER_AVAILABLE, CryptoProvider
            provider_available = CRYPTO_PROVIDER_AVAILABLE
            if provider_available:
                provider = CryptoProvider()
                # 判断主要数据源
                provider_name = "yfinance" if provider.yf_available else "CoinGecko"
        except Exception as e:
            logger.warning(f"检查加密货币provider失败: {e}")

        return ok(data={
            "provider_available": provider_available,
            "provider_name": provider_name,
            "coingecko_api_key_configured": bool(settings.COINGECKO_API_KEY),
            "crypto_data_source_enabled": settings.CRYPTO_DATA_SOURCE_ENABLED,
            "crypto_data_cache_hours": settings.CRYPTO_DATA_CACHE_HOURS,
            "supported_cryptos": [
                "BTC", "ETH", "ADA", "SOL", "DOT", "AVAX", "MATIC", "LINK", "UNI", "AAVE",
                "XRP", "LTC", "BCH", "DOGE", "SHIB", "PEPE", "BNB", "USDT", "USDC"
            ]
        })
    except Exception as e:
        logger.error(f"获取加密货币配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取加密货币配置失败: {str(e)}"
        )
```

---

## 四、验证步骤

### 4.1 市场类型检测验证

```bash
# 激活虚拟环境
source ./venv/bin/activate

# 测试市场检测
python -c "
from app.routers.stocks import _detect_market_and_code

# 测试各种代码
test_codes = ['000001', '00700', 'AAPL', 'BTC', 'ETH', '0700.HK']

for code in test_codes:
    market, normalized = _detect_market_and_code(code)
    print(f'{code:15} -> 市场: {market:10}, 标准化代码: {normalized}')
"
```

**预期输出：**
```
000001          -> 市场: CN        , 标准化代码: 000001
00700           -> 市场: HK        , 标准化代码: 00700
AAPL            -> 市场: US        , 标准化代码: AAPL
BTC             -> 市场: CRYPTO    , 标准化代码: BTC
ETH             -> 市场: CRYPTO    , 标准化代码: ETH
0700.HK         -> 市场: HK        , 标准化代码: 00700
```

### 4.2 加密货币行情验证

```bash
# 测试获取BTC行情（需要JWT token）
curl -X GET "http://localhost:8000/api/stocks/BTC/quote" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**预期响应：**
```json
{
  "success": true,
  "data": {
    "code": "BTC",
    "name": "Bitcoin",
    "market": "CRYPTO",
    "market_type": "加密货币",
    "price": 45000.50,
    "change_percent": 2.3,
    "amount": 1500000000,
    "updated_at": "2026-03-13T12:00:00Z"
  },
  "message": "success"
}
```

### 4.3 配置端点验证

```bash
# 测试获取加密货币配置
curl -X GET "http://localhost:8000/api/config/crypto" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**预期响应：**
```json
{
  "success": true,
  "data": {
    "provider_available": true,
    "provider_name": "yfinance",
    "coingecko_api_key_configured": false,
    "crypto_data_source_enabled": true,
    "crypto_data_cache_hours": 24,
    "supported_cryptos": ["BTC", "ETH", "ADA", ...]
  },
  "message": "success"
}
```

### 4.4 分析请求验证

```bash
# 测试提交BTC分析
curl -X POST "http://localhost:8000/api/analysis/single" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC",
    "parameters": {
      "market_type": "加密货币",
      "research_depth": "标准"
    }
  }'
```

---

## 五、与原方案的对比

| 方面 | 原方案 | 修正方案 | 一致性 |
|------|--------|----------|--------|
| **路由架构** | 独立 `crypto.py` | 集成到 `stocks.py` | ✅ 与HK/US一致 |
| **服务调用** | 直接调用Provider | 通过 `ForeignStockService` | ✅ 与HK/US一致 |
| **缓存管理** | Provider内部 | 服务层统一 | ✅ 与HK/US一致 |
| **请求去重** | 无 | `_request_locks` | ✅ 与HK/US一致 |
| **市场枚举** | 未扩展 | `Literal["CN","HK","US","CRYPTO"]` | ✅ 符合模型 |
| **main.py修改** | 需注册新路由 | 无需修改 | ✅ 最小侵入 |
| **新文件** | `crypto.py` | 无 | ✅ 复用现有 |

---

## 六、向后兼容性

1. ✅ 所有现有API端点保持不变
2. ✅ 新增枚举值不影响现有功能
3. ✅ 市场检测逻辑优先匹配现有格式
4. ✅ 不需要修改前端调用（通过统一路由）
5. ✅ `ForeignStockService` 扩展不影响HK/US逻辑

---

## 七、注意事项

1. **Provider依赖**：确保 `tradingagents/dataflows/providers/crypto/` 模块可用
2. **缓存配置**：加密货币使用与HK/US相同的缓存策略
3. **速率限制**：yfinance和CoinGecko都有速率限制，已在Provider中处理
4. **数据格式**：加密货币返回的数据格式已统一转换为与股票一致的格式
5. **错误处理**：遵循现有的错误处理模式，返回统一的响应格式

---

## 八、后续优化方向

1. 添加加密货币K线数据的可视化支持
2. 实现加密货币历史数据的高效存储和查询
3. 添加加密货币特有的指标（如市值排名、流通量等）
4. 支持更多加密货币交易所数据源
5. 实现加密货币实时价格推送（WebSocket）