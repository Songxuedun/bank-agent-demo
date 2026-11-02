"""
银行AI智能体 - 主程序入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.api.endpoints import router
from app.core.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("[START] Bank AI Agent starting...")
    
    # 确保 data 目录存在（必须在 init_db 之前，否则 SQLite 打不开数据库文件）
    os.makedirs("./data", exist_ok=True)
    
    # 初始化数据库
    await init_db()
    
    yield
    
    # 关闭时
    print("[STOP] Bank AI Agent shutting down...")


# 创建 FastAPI 应用
app = FastAPI(
    title="银行AI智能体",
    description="基于DeepSeek的智能银行服务Agent，支持智能转账、账单分析、理财操作等",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
os.makedirs(FRONTEND_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
async def root():
    """根路径 - 返回前端页面(与 API 同源，避免跨域问题)"""
    from fastapi.responses import FileResponse
    html_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "银行AI智能体 API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
