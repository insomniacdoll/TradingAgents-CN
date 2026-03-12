# 加密货币支持合并方案

## 一、项目差异分析

### Crypto项目核心改动
1. **新增 `coingecko_utils.py`** - CoinGecko API数据获取工具
2. **修改 `interface.py`** - 导入CoinGecko工具函数
3. **修改三个分析师文件**：
   - `fundamentals_analyst.py` - 添加加密货币基本面分析（英文prompt）
   - `market_analyst.py` - 添加加密货币技术分析（英文prompt）
   - `news_analyst.py` - 添加加密货币新闻分析（英文prompt）
4. **添加 `_is_crypto_symbol()` 函数** - 智能检测交易标类型
5. **依赖添加** - `requests` (已存在)

### 当前项目特点
- 更完善的中文市场支持（港股、A股）
- 复杂的数据源管理架构（`data_source_manager.py`, `providers/`）
- 使用 `pyproject.toml` 管理依赖
- Web界面、FastAPI后端等更完整的功能
- 前端使用Vue 3 + TypeScript，支持A股/美股/港股

---

## 二、合并方案

### 阶段1：核心数据层

**1.1 新增CoinGecko数据提供者**
- 创建 `tradingagents/dataflows/providers/crypto/coingecko_provider.py`
- 实现统一的provider接口（参考现有US/HK provider）
- 封装CoinGecko API调用，支持缓存和错误处理
- 支持中英文数据格式

**1.2 更新interface.py**
- 导入CoinGecko工具函数
- 添加符号类型检测函数 `is_crypto_symbol(symbol: str) -> bool`
- 添加crypto符号白名单（BTC、ETH等）
- 保持向后兼容，不影响现有股票/港股功能

### 阶段2：分析师层（中文Prompt）

**2.1 修改分析师文件**
- 在每个分析师中添加crypto检测逻辑
- 根据符号类型选择不同的工具集
- **将crypto相关的prompt全部改为中文**
- 保持现有股票/港股功能不变

**具体改动：**

**fundamentals_analyst.py**
- 添加crypto基本面工具
- **中文prompt内容：**
  - 加密货币基本面分析师
  - 分析市值、供应量、代币经济学、网络指标、采用指标等
  - 生成中文报告

**market_analyst.py**
- 添加crypto技术分析工具
- **中文prompt内容：**
  - 加密货币技术分析师
  - 分析价格走势、成交量、支撑阻力位、波动性等
  - 生成中文报告

**news_analyst.py**
- 添加crypto新闻工具
- **中文prompt内容：**
  - 加密货币新闻研究员
  - 分析加密货币市场相关新闻、监管动态、机构采用等
  - 生成中文报告

### 阶段3：前端修改

**3.1 类型定义更新**
- 修改 `frontend/src/types/analysis.ts`
- 将 `market_type` 类型扩展为：
  ```typescript
  market_type: 'A股' | '美股' | '港股' | '加密货币'
  ```

**3.2 代码验证工具更新**
- 修改 `frontend/src/utils/stockValidator.ts`
- 新增 `validateCrypto()` 函数
- 更新 `validateStockCode()` 函数，支持加密货币检测

```typescript
/**
 * 加密货币代码格式验证
 * 格式：2-4个大写字母
 * 示例：BTC、ETH、ADA、SOL、DOT
 */
export function validateCrypto(code: string): StockValidationResult {
  const cleanCode = code.trim().toUpperCase()

  // 基本格式：2-4个大写字母
  if (!/^[A-Z]{2,4}$/.test(cleanCode)) {
    return {
      valid: false,
      message: '加密货币代码格式不正确（2-4个字母，如：BTC、ETH）'
    }
  }

  // 常见加密货币白名单
  const commonCryptos = ['BTC', 'ETH', 'ADA', 'SOL', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'AAVE',
                         'XRP', 'LTC', 'BCH', 'EOS', 'TRX', 'XLM', 'VET', 'ALGO', 'ATOM', 'LUNA',
                         'NEAR', 'FTM', 'CRO', 'SAND', 'MANA', 'AXS', 'GALA', 'ENJ', 'CHZ', 'BAT',
                         'ZEC', 'DASH', 'XMR', 'DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BNB', 'USDT', 'USDC']

  if (!commonCryptos.includes(cleanCode)) {
    return {
      valid: false,
      message: '暂不支持该加密货币，请使用常见加密货币（如：BTC、ETH、ADA等）'
    }
  }

  return {
    valid: true,
    market: '加密货币',
    normalizedCode: cleanCode
  }
}
```

**3.3 市场类型工具更新**
- 修改 `frontend/src/utils/market.ts`
- 更新 `normalizeMarketForAnalysis()` 函数，支持加密货币
- 更新 `getMarketByStockCode()` 函数

```typescript
export const normalizeMarketForAnalysis = (market: any): string => {
  const raw = String(market ?? '').trim()
  const upper = raw.toUpperCase()
  const cn = raw
  const isA = [...]
  const isHK = [...]
  const isUS = [...]
  const isCrypto = ['加密货币', 'CRYPTO', '数字货币'].includes(cn) || ['CRYPTO'].includes(upper)
  if (isA) return 'A股'
  if (isHK) return '港股'
  if (isUS) return '美股'
  if (isCrypto) return '加密货币'
  return 'A股'
}
```

**3.4 分析页面更新**
- 修改 `frontend/src/views/Analysis/SingleAnalysis.vue`
- 市场类型选择器添加"加密货币"选项
- 添加加密货币代码输入验证
- 根据选择的动态调整输入提示

- 修改 `frontend/src/views/Analysis/BatchAnalysis.vue`
- 添加加密货币批量分析支持

- 修改 `frontend/src/views/Analysis/AnalysisHistory.vue`
- 加密货币分析结果展示

**3.5 股票输入组件更新**
- 查找或创建股票代码输入组件
- 添加加密货币代码检测逻辑
- 根据检测结果自动切换市场类型

**3.6 配置页面更新**
- 修改 `frontend/src/views/Settings/` 下的配置页面
- 添加CoinGecko API密钥配置选项（可选）
- 添加加密货币数据源开关配置

### 阶段4：配置与依赖

**4.1 环境配置**
- 在 `.env.example` 添加 `COINGECKO_API_KEY` 配置项（可选）
- 在数据库配置中添加crypto市场类别选项

**4.2 依赖管理**
- `requests` 已存在于 `requirements.txt`，无需额外添加

**4.3 数据源配置**
- 在数据库配置中添加crypto市场类别选项
- 支持用户启用/禁用crypto数据源

### 阶段5：后端API更新

**5.1 API路由更新**
- 添加加密货币符号验证端点
- 支持加密货币分析请求

**5.2 数据库模型更新**
- 支持存储加密货币分析结果
- 更新历史记录查询，支持加密货币过滤

### 阶段6：测试与文档

**6.1 测试**
- 创建 `tests/test_crypto_integration.py`
- 测试符号检测准确性
- 测试各分析师的crypto功能
- 测试前端crypto相关功能

**6.2 文档**
- 更新 README.md 添加crypto支持说明
- 创建 `docs/crypto_support.md` 详细使用指南
- 更新前端用户手册，添加加密货币分析说明

---

## 三、实施步骤

### Step 1: 后端核心功能
1. 创建CoinGecko Provider
2. 更新interface.py
3. 修改分析师（使用中文prompt）

### Step 2: 后端API支持
1. 更新API路由
2. 更新数据库模型
3. 添加配置支持

### Step 3: 前端类型和工具
1. 更新类型定义
2. 更新验证工具
3. 更新市场工具

### Step 4: 前端页面修改
1. 修改分析页面
2. 修改配置页面
3. 更新输入组件

### Step 5: 测试验证
1. 单元测试
2. 集成测试
3. 前后端联调

### Step 6: 文档更新
1. 用户文档
2. API文档
3. 开发文档

---

## 四、关键中文Prompt示例

### 基本面分析师
```
你是一位加密货币基本面分析师，负责分析加密货币的基本面信息。请撰写一份关于该加密货币的全面报告，包括市值排名、供应量机制、代币经济学、网络指标、采用指标和市场定位，为交易员提供完整的加密货币基本面价值观点。

重点关注加密货币特定指标：市值排名、流通供应量与总供应量、交易量模式、网络活动、开发者生态系统、监管环境、社区实力和技术基本面。

请包含尽可能多的细节。不要简单说明趋势混合，请提供详细和精细的分析和见解，以帮助加密货币交易员做出决策。

请在报告末尾附加一个Markdown表格，组织报告中的关键要点，使其易于阅读和理解。
```

### 技术分析师
```
你是一位加密货币技术分析师，负责分析加密货币市场。你的职责是为加密货币交易提供全面的技术分析。重点关注对数字资产最相关的加密货币特定模式和指标。

需要分析的加密货币关键领域：
- 价格走势和趋势分析
- 成交量模式和市场流动性
- 支撑和阻力水平
- 市场波动性和风险评估
- 动量指标及其在加密货币市场中的可靠性
- 市场情绪和心理水平

请撰写一份非常详细和细致的加密货币市场趋势报告。同时分析短期和长期趋势。不要简单说明趋势混合，请提供详细和精细的分析和见解，以帮助加密货币交易员做出决策。考虑加密货币市场的独特特征，如24/7交易、更高的波动性和情绪驱动的波动。

请在报告末尾附加一个Markdown表格，组织报告中的关键要点，使其易于阅读和理解。
```

### 新闻分析师
```
你是一位加密货币新闻研究员，负责分析过去一周影响加密货币市场的近期新闻和趋势。请撰写一份关于加密货币世界当前状态以及对加密货币交易相关的更广泛宏观经济因素的全面报告。

重点关注加密货币特定新闻，包括：监管发展、机构采用、技术更新、市场情绪、DeFi趋势、NFT市场、区块链发展和主要加密货币交易所新闻。

同时考虑影响加密货币市场的传统宏观经济因素，如通胀、货币政策、全球经济不确定性和传统市场趋势。

不要简单说明趋势混合，请提供详细和精细的分析和见解，以帮助加密货币交易员做出决策。

请在报告末尾附加一个Markdown表格，组织报告中的关键要点，使其易于阅读和理解。
```

---

## 五、支持的加密货币

系统支持以下常见加密货币：

### 主要加密货币
- BTC (Bitcoin) - 比特币
- ETH (Ethereum) - 以太坊
- ADA (Cardano) - 卡尔达诺
- SOL (Solana) - 索拉纳
- DOT (Polkadot) - 波卡

### DeFi代币
- UNI (Uniswap) - Uniswap
- AAVE (Aave) - Aave
- LINK (Chainlink) - 链link
- MATIC (Polygon) - 多边形

### 热门代币
- DOGE (Dogecoin) - 狗狗币
- SHIB (Shiba Inu) - 柴犬币
- PEPE (Pepe) - Pepe
- BNB (Binance Coin) - 币安币

### 稳定币
- USDT (Tether) - 泰达币
- USDC (USD Coin) - USD Coin

---

## 六、API配置

### CoinGecko API（可选）
```bash
# 免费版本已足够使用，设置API密钥可以提高请求限制
export COINGECKO_API_KEY=your_coingecko_api_key
```

### 环境变量配置
在 `.env` 文件中添加：
```bash
# CoinGecko API密钥（可选，免费API无需设置）
COINGECKO_API_KEY=

# 加密货币数据源启用状态
CRYPTO_DATA_SOURCE_ENABLED=true
```

---

## 七、功能特点

### 智能检测
- 自动识别输入符号类型（加密货币 vs 股票）
- 无缝切换数据源和分析方法

### 加密货币专用分析
- **基本面分析**：市值排名、供应量分析、代币经济学
- **技术分析**：价格趋势、技术指标、市场动量
- **新闻分析**：监管新闻、市场趋势、机构动态

### 实时数据
- 24/7加密货币市场数据
- 实时价格和成交量
- 全球市场概览

---

## 八、向后兼容

系统仍然支持原有的股票交易功能：
- 使用股票符号（如AAPL、NVDA）时自动使用股票数据源
- 使用A股代码（如000001）时自动使用A股数据源
- 使用港股代码（如00700）时自动使用港股数据源
- 保持原有的所有股票分析功能

---

## 九、风险与注意事项

1. **向后兼容性**：确保现有股票/港股功能不受影响
2. **API限制**：CoinGecko免费API有速率限制，需要处理
3. **符号检测**：需要确保检测逻辑准确，避免误判
4. **数据一致性**：crypto数据格式与传统股票可能不同，需要适配
5. **中文本地化**：确保所有crypto相关内容都是中文
6. **前端兼容**：确保前端与后端crypto功能完全兼容

---

## 十、建议

- 采用渐进式合并，先实现核心功能，再逐步完善
- 优先保证现有功能稳定，再添加新功能
- 充分测试后再合并到主分支
- 考虑添加配置开关，允许用户启用/禁用crypto功能
- 前后端同步开发，确保接口一致性
- 所有新增功能使用中文，保持项目风格统一

---

## 十一、参考文档

- CoinGecko API文档: https://www.coingecko.com/en/api
- 原crypto项目: `../TradingAgents-crypto`
- 数据源管理架构: `docs/technical/data-source-architecture.md`