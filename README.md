# OptionPilot - AI Options Strategy Analyzer

An MVP desktop application for options trading analysis, designed for individual investors who want to quantify and validate strategy risks and returns before trading.

## Quick Start

### Prerequisites
- Python 3.11+
- uv package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd OptionPilot

# Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your actual API keys
```

### Running the Application
```bash
# CLI interface (Milestone 1)
uv run python cli.py

# Web interface (Milestone 2)
uv run streamlit run app.py

# Run tests
uv run python -m pytest tests/ -v
```

## Project Structure
```
OptionPilot/
├── models.py              # Core data structures
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # API configuration template
└── tests/                # Test suite
```

---

# 产品需求文档 (PRD): AI期权策略分析器 MVP

* **产品名称:** AI期权策略分析器
* **版本:** 1.0 (MVP)
* **目标用户:** 熟悉期权基础，希望在交易前量化和验证策略风险与回报的个人投资者。

---

## 1. 产品目标

* **核心目标:** 让用户能够快速构建一个期权价差策略，并直观地理解其潜在的风险、回报和关键参数。
* **辅助目标:** 利用 AI 提供策略的定性分析和风险提示，并通过交易日志追踪纸上交易的表现。

---

## 2. 核心功能需求

### F1: 数据源与连接

* **1.1. 股票报价:**
    * **描述:** 程序需能通过 **Alpha Vantage API** 获取预设股票列表（如 NVDA, TSLA, HOOD, CRCL）的最新报价。
    * **接收标准:** 成功返回指定股票的当前市场价格。
* **1.2. 期权链数据:**
    * **描述:** 用户选择股票和到期日后，程序需通过 **Alpha Vantage API** 获取完整的期权链。
    * **接收标准:** 成功返回包含所有行权价 (Strikes)、看涨/看跌 (Type)、买价 (Bid)、卖价 (Ask) 的数据列表。
* **1.3. 技术栈:**
    * **描述:** 项目后端逻辑使用 **Python** 开发，并采用 **uv** 进行包和虚拟环境管理。

### F2: 策略构建与计算器

* **2.1. 策略输入:**
    * **描述:** 用户界面需允许用户构建一个双边期权策略 (two-leg spread)。
    * **接收标准:** 用户可为每一边选择 `买/卖 (Action)`, `看涨/看跌 (Type)`, 和 `行权价 (Strike)`。
* **2.2. 核心指标计算:**
    * **描述:** 在用户完成策略构建后，系统必须**立即**根据期权链的买卖价差，自动计算并清晰展示以下核心指标：
        * **净权利金 (Net Premium):** 明确标明是收入(Credit)还是支出(Debit)。
        * **最大利润 (Max Profit):** 策略可实现的最大理论收益。
        * **最大亏损 (Max Loss):** 策略的最大理论风险。
        * **盈亏平衡点 (Breakeven Point):** 股价在到期日达到该点时，策略不赚不亏。
        * **保证金/成本 (Margin/Cost):** 对于信用价差，保证金等于最大亏损；对于借方价差，成本等于净权利金支出。
        * **保证金回报率 (Return on Margin):** `最大利润 / 保证金`。
* **2.3. 收益可视化:**
    * **描述:** 系统必须生成并展示该策略的**盈亏平衡图 (Payoff Diagram)**。
    * **接收标准:** 该图需能直观地展示在不同到期日股价下，策略的盈亏情况。

### F3: AI 策略分析

* **3.1. AI 调用:**
    * **描述:** 在策略构建面板旁，提供一个 **"AI 分析"** 按钮。
    * **接收标准:** 用户点击后，程序将策略详情（股票代码、当前股价、策略构成）作为请求，调用 **OpenRouter** 平台上的大语言模型 API (首选 **Claude 4 Sonnet**)。
* **3.2. AI 分析内容:**
    * **描述:** AI 的返回结果必须聚焦于以下三点，并以精炼的语言展示给用户：
        * **策略解读:** 用一句话解释用户构建的是什么策略 (例如: "这是一个牛市看跌期权信用价差策略")。
        * **市场观点:** 指出该策略所隐含的市场预期 (例如: "此策略在股价温和上涨或保持在 [某价格] 之上时盈利")。
        * **核心风险提示:** 明确告知策略的主要风险 (例如: "若股价跌破 [某价格]，将发生最大亏损")。

### F4: 纸上交易日志

* **4.1. 记录交易:**
    * **描述:** 用户可以将其构建的策略一键保存到“交易日志”中。
    * **接收标准:** 日志中成功创建一条包含所有策略参数和计算指标的新条目。
* **4.2. 日志展示:**
    * **描述:** 交易日志以列表形式展示所有已保存的纸上交易。
    * **接收标准:** 列表需至少包含以下列：`股票代码`, `策略类型`, `入场日期`, `到期日`, `净权利金`, `状态 (持仓中/已平仓)`, `最终盈亏`。
* **4.3. 平仓操作:**
    * **描述:** MVP 阶段，平仓为手动操作。用户可选择一条持仓中的交易，手动输入平仓价格或最终结果，系统据此计算最终盈亏并更新状态。

---

## 3. MVP 范围之外 (Out of Scope)

* 任何与真实券商账户的对接或实盘交易功能。
* 复杂的多边（超过2边）期权策略。
* 用户账户系统、云端数据同步。
* 基于历史数据的回测功能。
* 高级统计指标（如隐含波动率 IV, 希腊字母 Greeks, 获利概率 POP）。
