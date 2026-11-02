"""API 路由: 注册/登录、数据查询、Agent 对话、确认/MFA"""
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.orchestrator import BankingAgent
from app.core.context import set_uid
from app.core.database import Account, AuditLog
from app.core.init_db import get_session, seed_user
from app.core.security import hash_password, make_token, parse_token, verify_password
from app.tools.implementations import TOOL_IMPLEMENTATIONS

router = APIRouter(prefix="/api")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
# 前端手动操作允许走的工具(同样经过确认/MFA 把关)
UI_ACTIONS = {"transfer", "buy_product", "redeem_product", "cancel_subscription",
              "freeze_card", "unfreeze_card"}
UI_QUERIES = {"get_summary", "get_statement", "get_products", "get_portfolio", "get_cards",
              "get_subscriptions", "get_contacts", "get_transaction_history",
              "get_risk_assessment", "assess_risk_profile", "get_wealth_recommendation",
              "get_asset_pyramid", "get_wealth_analysis"}


class RegisterReq(BaseModel):
    username: str
    password: str = Field(min_length=6, max_length=64)
    name: str = Field(min_length=1, max_length=20)
    phone: str = ""


class LoginReq(BaseModel):
    username: str
    password: str


class ChatReq(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ActionReq(BaseModel):
    tool: str
    params: Dict[str, Any] = {}


class PendingReq(BaseModel):
    pending_id: str
    mfa_code: Optional[str] = ""


async def current_user(authorization: str = Header(default=""),
                       session: AsyncSession = Depends(get_session)) -> str:
    token = authorization.removeprefix("Bearer ").strip()
    user_id = parse_token(token) if token else None
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    acc = (await session.execute(select(Account).where(Account.user_id == user_id))).scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=401, detail="账户不存在")
    set_uid(user_id)
    return user_id


def _profile(acc: Account) -> dict:
    return {"username": acc.username, "name": acc.name, "phone": acc.phone}


@router.post("/register")
async def register(req: RegisterReq, session: AsyncSession = Depends(get_session)):
    username = req.username.strip().lower()
    if not USERNAME_RE.match(username):
        raise HTTPException(400, "用户名需为 3-20 位字母、数字或下划线")
    exists = (await session.execute(select(Account).where(Account.username == username))).scalar_one_or_none()
    if exists:
        raise HTTPException(409, "用户名已被注册")
    user_id = f"u_{username}"
    await seed_user(session, user_id, username, req.password, req.name.strip(),
                    req.phone.strip() or "未填写", 50000.00, 12000)
    await session.commit()
    acc = (await session.execute(select(Account).where(Account.user_id == user_id))).scalar_one()
    return {"token": make_token(user_id), "user": _profile(acc)}


@router.post("/login")
async def login(req: LoginReq, session: AsyncSession = Depends(get_session)):
    acc = (await session.execute(
        select(Account).where(Account.username == req.username.strip().lower()))).scalar_one_or_none()
    if not acc or not verify_password(req.password, acc.password_hash or ""):
        raise HTTPException(401, "用户名或密码错误")
    return {"token": make_token(acc.user_id), "user": _profile(acc)}


@router.get("/me")
async def me(user_id: str = Depends(current_user), session: AsyncSession = Depends(get_session)):
    acc = (await session.execute(select(Account).where(Account.user_id == user_id))).scalar_one()
    return _profile(acc)


@router.get("/query/{tool}")
async def query(tool: str, request: Request, user_id: str = Depends(current_user),
                session: AsyncSession = Depends(get_session)):
    if tool not in UI_QUERIES:
        raise HTTPException(404, "未知查询")
    impl = TOOL_IMPLEMENTATIONS[tool]
    params = dict(request.query_params)
    if params:
        try:
            res = await impl(session, **params)
        except TypeError:
            res = await impl(session)
    else:
        res = await impl(session)
    return {"success": res.success, "error": res.error, "message": res.message, "data": res.data}


@router.post("/action")
async def action(req: ActionReq, user_id: str = Depends(current_user),
                 session: AsyncSession = Depends(get_session)):
    """界面表单发起的操作: 与 Agent 走同一套权限判定，返回 pending 或结果"""
    if req.tool not in UI_ACTIONS:
        raise HTTPException(400, "不支持的操作")
    agent = BankingAgent(session, user_id)
    out = await agent._dispatch(req.tool, req.params, f"用户在界面手动发起 {req.tool}", [], [])
    if out.get("pending"):
        return {**out["pending"], "content": out["content"]}
    return {"type": "result", **out["result"]}


@router.post("/chat")
async def chat(req: ChatReq, user_id: str = Depends(current_user),
               session: AsyncSession = Depends(get_session)):
    return await BankingAgent(session, user_id).chat(req.message)


@router.post("/confirm")
async def confirm(req: PendingReq, user_id: str = Depends(current_user),
                  session: AsyncSession = Depends(get_session)):
    return await BankingAgent(session, user_id).execute_pending(req.pending_id, req.mfa_code or "")


@router.post("/cancel")
async def cancel(req: PendingReq, user_id: str = Depends(current_user),
                 session: AsyncSession = Depends(get_session)):
    await BankingAgent(session, user_id).cancel_pending(req.pending_id)
    return {"success": True}


@router.get("/audit")
async def audit(user_id: str = Depends(current_user), session: AsyncSession = Depends(get_session)):
    rows = (await session.execute(
        select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.id.desc()).limit(30))).scalars().all()
    return {"logs": [{"time": r.timestamp.strftime("%H:%M:%S"), "operation": r.operation, "tool": r.tool_name,
                      "risk": r.risk_level, "mfa": r.mfa_status, "result": r.result} for r in rows]}


@router.get("/health")
async def health():
    return {"status": "ok"}
