# 银行AI智能体 - 部署说明

## 项目结构

```
银行agent/
├── backend/                    # 后端 (Python FastAPI)
│   ├── app/
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 配置管理
│   │   │   ├── database.py    # 数据库模型
│   │   │   ├── init_db.py     # 数据库初始化
│   │   │   └── risk_levels.py # 权限分级
│   │   ├── tools/             # 工具层
│   │   │   ├── tool_registry.py    # 工具定义
│   │   │   └── implementations.py # 工具实现
│   │   ├── agent/             # Agent 编排层
│   │   │   └── orchestrator.py # Agent 核心
│   │   ├── api/               # API 路由
│   │   │   └── endpoints.py   # 接口定义
│   │   └── main.py            # 主程序
│   ├── data/                   # SQLite 数据库
│   ├── requirements.txt        # Python 依赖
│   └── .env                    # 环境配置
├── module/                    # 前端
│   ├── index.html            # 页面
│   ├── style.css             # 样式
│   ├── app.js                # 原版交互
│   └── app_ai.js             # AI 增强版
└── README.md                  # 本文件
```

## 快速启动

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

或者直接运行:

```bash
cd backend
python app/main.py
```

### 3. 打开前端

在浏览器中打开 `module/index.html`

或者使用 Python HTTP 服务器:

```bash
cd module
python -m http.server 8080
# 访问 http://localhost:8080
```

## API 接口

### 对话接口

```
POST /api/chat
{
    "message": "帮我查一下余额"
}
```

响应:
```json
{
    "type": "response|confirmation|mfa",
    "content": "回复内容",
    "risk_level": "green|yellow|red",
    "data": {},
    "tool_name": "get_balance",
    "params": {}
}
```

### 确认操作

```
POST /api/confirm
{
    "tool_name": "transfer",
    "params": {"to": "妈妈", "amount": 500}
}
```

### MFA 验证

```
POST /api/mfa
{
    "tool_name": "transfer",
    "params": {"to": "妈妈", "amount": 5000},
    "mfa_code": "123456"
}
```

### 工具列表

```
GET /api/tools
```

### 健康检查

```
GET /api/health
```

## 权限分级

| 等级 | 颜色 | 操作 | 处理方式 |
|------|------|------|----------|
| 绿色 | ✓ | 查询余额、账单、持仓 | 自动执行 |
| 黄色 | ⚠ | 小额转账(<1000)、取消订阅 | 需用户确认 |
| 红色 | 🔴 | 大额转账(>1000)、挂失、申购理财 | 需 MFA 验证 |

## 测试验证码

MFA 验证使用测试验证码: `123456`

## 注意事项

1. 后端需要连接 DeepSeek API，请确保网络畅通
2. 前端默认连接 `http://localhost:8000`
3. 如果 API 不可用，前端会自动切换到本地模拟模式
4. 所有操作都会记录审计日志

## 常见问题

### Q: 前端显示"AI 离线"
A: 检查后端服务是否启动，端口是否为 8000

### Q: MFA 验证失败
A: 使用测试验证码 `123456`

### Q: 转账失败
A: 检查账户余额是否充足
