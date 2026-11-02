# 银行 AI 智能体（Bank AI Agent）

基于 **DeepSeek 大模型 + FastAPI + 原生 JS** 的智能银行服务演示项目。支持自然语言对话办理业务，AI 自动调用工具并操作界面，全程可审计。

> 评委可直接查看本仓库，或按下方「快速启动」在本地运行体验。未配置 DeepSeek Key 时，登录 / 转账 / 账单分析 / 理财操作等功能均可正常体验，仅「AI 对话」需要 Key。

## 核心亮点

- **AI Agent 编排**：DeepSeek function calling 驱动工具调用，绿色查询自动执行、黄色操作需确认、红色操作需验证码
- **专业理财分析**：落地《理财产品分析决策专家手册》五步路径——财产盘点 → 安全评估 → 收益考量 → 横向对比 → 买哪只；含业绩比较基准、费后收益、夏普/最大回撤、资金期限分层、核心-卫星配置、风险等级合规匹配（只能买 R≤C 的产品）、风险预算
- **安全分级操作**：单笔 ≤1000 元需确认、>1000 元需短信验证码（演示码 `123456`）
- **全量审计日志**：每笔操作可追溯

## 文件结构

```
bank-agent-demo/   （仓库根目录 = 压缩包内「作品提交」内容）
├── backend/          # FastAPI 后端
│   ├── .env.example  # API 密钥配置模板（真实密钥不入库）
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── core/         # 配置、数据库、安全
│       ├── api/          # REST 端点
│       ├── agent/        # Agent 编排层
│       ├── tools/        # 工具定义与实现
│       └── services/     # 理财知识库 + 专业分析引擎
│           └── wealth_profiles.py   # 五步路径专业分析
├── frontend/        # SPA（无框架，纯 JS）
│   ├── index.html
│   ├── style.css
│   └── app.js
└── bank-agent.html  # 单文件独立演示页
```

## 快速启动

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置 API 密钥（可选）

复制 `backend/.env.example` 为 `backend/.env`，填入你的 DeepSeek API Key：

```env
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 3. 启动服务

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

然后访问 **http://127.0.0.1:8000**（或直接打开 `bank-agent.html`，需后端在运行）。

## 功能概览

| 功能 | 说明 |
|------|------|
| 注册 / 登录 | 首次启动自动创建演示账号（user1/123456） |
| 首页 | 账户概览、本月收支、储蓄率 |
| 智能转账 | AI 引导转账（≤1000 元需确认，>1000 元需验证码） |
| 账单分析 | 消费分类饼图、智能洞察 |
| 理财操作 | 专业理财分析（五步路径）、持仓、申购 / 赎回 |
| AI 对话 | 输入自然语言，AI 自动操作界面并回答 |
| 审计日志 | 全程操作记录，可追溯 |

## 权限分级

- **绿色**：查询类（余额、账单、持仓），自动执行
- **黄色**：≤1000 元转账、取消订阅等，需用户确认
- **红色**：大额转账（>1000 元）、申购理财，需短信验证码（演示验证码：`123456`）

## 演示账号

- `user1` / `123456`（余额 ¥128,430）
- `user2` / `123456`（余额 ¥85,320）
- `user3` / `123456`（余额 ¥200,000）

## 技术栈

- 后端：FastAPI + SQLAlchemy（异步）+ DeepSeek API
- 前端：原生 HTML/CSS/JS，无框架依赖
- 数据库：SQLite（`backend/data/bank_assistant.db`，自动创建）
