"""
工具实现 - 银行业务工具集
每个函数都返回一个 ToolResult
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import random
import json
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Account, BankCard, Transaction, Product, Portfolio, Subscription, AutoRule, Contact, AuditLog
from app.core.risk_levels import RiskLevel, get_tool_risk_level
from app.tools.tool_registry import ToolResult
from app.core.context import uid


# ===== 工具实现函数 =====

async def get_balance(session: AsyncSession) -> ToolResult:
    """查询余额"""
    result = await session.execute(select(Account).where(Account.user_id == uid()))
    account = result.scalar_one_or_none()
    if not account:
        return ToolResult(success=False, error="账户不存在", risk_level=RiskLevel.GREEN)
    
    if account.is_locked:
        return ToolResult(
            success=False,
            error=f"账户已被锁定，原因：{account.lock_reason}",
            risk_level=RiskLevel.RED
        )
    
    return ToolResult(
        success=True,
        data={
            "balance": account.balance,
            "daily_transfer_remaining": max(0, 1000 - account.daily_transfer_total),
            "message": f"当前账户余额为 ¥{account.balance:,.2f}"
        },
        risk_level=RiskLevel.GREEN
    )


async def get_transaction_history(session: AsyncSession, days: int = 30, limit: int = 20) -> ToolResult:
    """查询交易记录"""
    since = datetime.now() - timedelta(days=days)
    result = await session.execute(
        select(Transaction)
        .where(Transaction.user_id == uid())
        .where(Transaction.timestamp >= since)
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
    )
    transactions = result.scalars().all()
    
    data = [
        {
            "id": t.id,
            "type": t.transaction_type,
            "amount": t.amount,
            "counterparty": t.counterparty,
            "memo": t.memo,
            "category": t.category,
            "is_suspicious": t.is_suspicious,
            "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M")
        }
        for t in transactions
    ]
    
    return ToolResult(
        success=True,
        data={"transactions": data, "count": len(data)},
        risk_level=RiskLevel.GREEN
    )


async def get_statement(session: AsyncSession, month: str = None) -> ToolResult:
    """获取账单分析"""
    if not month:
        month = datetime.now().strftime("%Y-%m")
    
    result = await session.execute(
        select(Transaction).where(Transaction.user_id == uid())
    )
    month_tx = [t for t in result.scalars().all() if t.timestamp.strftime("%Y-%m") == month]

    spending_by_category = {}
    income = 0.0
    for t in month_tx:
        if t.transaction_type == "转出":
            cat = t.category or "其他"
            spending_by_category[cat] = round(spending_by_category.get(cat, 0) + t.amount, 2)
        elif t.transaction_type == "转入":
            income += t.amount

    total = sum(spending_by_category.values())
    if not spending_by_category:
        return ToolResult(success=True, data={
            "month": month, "total_spending": 0, "total_income": round(income, 2),
            "by_category": {}, "top_category": None, "savings_rate": None, "insights": ["该月暂无消费记录"],
        }, risk_level=RiskLevel.GREEN)
    savings_rate = round((income - total) / income * 100, 1) if income > 0 else None
    top = max(spending_by_category, key=spending_by_category.get)
    suspicious_n = len([t for t in month_tx if t.is_suspicious])
    insights = [f"{top}支出最高，占比 {spending_by_category[top] / total * 100:.0f}%"]
    insights.append(f"发现 {suspicious_n} 笔夜间可疑交易，建议核查" if suspicious_n else "未发现异常交易")
    if savings_rate is not None:
        insights.append(f"本月储蓄率 {savings_rate}%")
    
    return ToolResult(
        success=True,
        data={
            "month": month,
            "total_spending": round(total, 2),
            "total_income": round(income, 2),
            "by_category": spending_by_category,
            "top_category": top,
            "savings_rate": savings_rate,
            "insights": insights,
        },
        risk_level=RiskLevel.GREEN
    )


async def get_products(session: AsyncSession, risk_level: int = None) -> ToolResult:
    """获取理财产品列表"""
    query = select(Product)
    if risk_level:
        query = query.where(Product.risk_level == risk_level)
    
    result = await session.execute(query)
    products = result.scalars().all()
    
    data = [
        {
            "name": p.name,
            "tag": p.tag,
            "description": p.description,
            "annual_rate": p.annual_rate,
            "risk_level": p.risk_level,
            "min_amount": p.min_amount
        }
        for p in products
    ]
    
    return ToolResult(
        success=True,
        data={"products": data},
        risk_level=RiskLevel.GREEN
    )


async def get_portfolio(session: AsyncSession) -> ToolResult:
    """获取持仓"""
    result = await session.execute(
        select(Portfolio, Product)
        .join(Product)
        .where(Portfolio.user_id == uid())
    )
    holdings = result.all()
    
    data = []
    total = 0
    for portfolio, product in holdings:
        profit_loss_pct = (portfolio.profit_loss / portfolio.amount) * 100
        data.append({
            "name": product.name,
            "amount": portfolio.amount,
            "current_value": portfolio.current_value,
            "profit_loss": portfolio.profit_loss,
            "profit_loss_pct": round(profit_loss_pct, 2),
            "annual_rate": product.annual_rate
        })
        total += portfolio.current_value
    
    return ToolResult(
        success=True,
        data={"holdings": data, "total_value": round(total, 2)},
        risk_level=RiskLevel.GREEN
    )


async def get_cards(session: AsyncSession) -> ToolResult:
    """获取银行卡列表"""
    result = await session.execute(
        select(BankCard).where(BankCard.user_id == uid())
    )
    cards = result.scalars().all()
    
    data = [
        {
            "name": c.card_name,
            "number": c.card_number,
            "type": c.card_type,
            "balance_or_limit": c.balance_or_limit,
            "status": c.status
        }
        for c in cards
    ]
    
    return ToolResult(
        success=True,
        data={"cards": data},
        risk_level=RiskLevel.GREEN
    )


async def get_subscriptions(session: AsyncSession) -> ToolResult:
    """获取订阅列表"""
    result = await session.execute(
        select(Subscription).where(Subscription.user_id == uid())
    )
    subs = result.scalars().all()
    
    data = [
        {
            "name": s.name,
            "logo": s.logo,
            "cycle": s.cycle,
            "amount": s.amount,
            "next_date": s.next_date,
            "is_active": s.is_active
        }
        for s in subs
    ]
    
    total_monthly = sum(s.amount for s in subs if s.cycle == "月付")
    total_yearly = sum(s.amount for s in subs if s.cycle == "年付") / 12
    upcoming = len([s for s in subs if s.is_active])
    
    return ToolResult(
        success=True,
        data={
            "subscriptions": data,
            "total_monthly": round(total_monthly + total_yearly, 2),
            "upcoming_count": upcoming
        },
        risk_level=RiskLevel.GREEN
    )


async def get_rules(session: AsyncSession) -> ToolResult:
    """获取联动规则"""
    result = await session.execute(
        select(AutoRule).where(AutoRule.user_id == uid())
    )
    rules = result.scalars().all()
    
    data = [
        {
            "id": r.id,
            "trigger": r.trigger,
            "action": r.action,
            "is_active": r.is_active
        }
        for r in rules
    ]
    
    return ToolResult(
        success=True,
        data={"rules": data},
        risk_level=RiskLevel.GREEN
    )


async def analyze_spending(session: AsyncSession, period: str = "month") -> ToolResult:
    """分析消费习惯"""
    days = {"week": 7, "month": 30, "year": 365}.get(period, 30)
    since = datetime.now() - timedelta(days=days)
    
    result = await session.execute(
        select(Transaction)
        .where(Transaction.user_id == uid())
        .where(Transaction.timestamp >= since)
    )
    transactions = result.scalars().all()
    expense_tx = [t for t in transactions if t.transaction_type == "转出"]
    
    # 统计
    total = sum(t.amount for t in expense_tx)
    by_category = {}
    suspicious = []
    
    for t in expense_tx:
        cat = t.category or "其他"
        by_category[cat] = by_category.get(cat, 0) + t.amount
        if t.is_suspicious:
            suspicious.append({
                "amount": t.amount,
                "counterparty": t.counterparty,
                "time": t.timestamp.strftime("%Y-%m-%d %H:%M"),
                "reason": "夜间异常交易"
            })
    
    avg_daily = total / days if days > 0 else 0
    
    return ToolResult(
        success=True,
        data={
            "period": period,
            "total_spending": round(total, 2),
            "daily_average": round(avg_daily, 2),
            "by_category": {k: round(v, 2) for k, v in by_category.items()},
            "transaction_count": len(expense_tx),
            "suspicious_transactions": suspicious,
            "recommendations": [
                "餐饮支出占比较高，建议适当控制" if by_category.get("餐饮", 0) > 1500 else "餐饮支出控制良好",
                "发现{}笔可疑交易，建议核查".format(len(suspicious)) if suspicious else "未发现异常交易"
            ]
        },
        risk_level=RiskLevel.GREEN
    )


async def recommend_products(session: AsyncSession, risk_tolerance: int = 3, amount: float = None) -> ToolResult:
    """推荐理财产品"""
    result = await session.execute(select(Product))
    products = result.scalars().all()
    
    # 根据风险偏好筛选
    if risk_tolerance <= 2:
        filtered = [p for p in products if p.risk_level <= 2]
    elif risk_tolerance == 3:
        filtered = [p for p in products if p.risk_level <= 3]
    else:
        filtered = products
    
    recommendations = []
    for p in filtered:
        recommendations.append({
            "name": p.name,
            "tag": p.tag,
            "annual_rate": p.annual_rate,
            "risk_level": p.risk_level,
            "reason": _get_recommendation_reason(p, risk_tolerance)
        })
    
    # 按风险等级排序
    recommendations.sort(key=lambda x: x["risk_level"])
    
    return ToolResult(
        success=True,
        data={
            "risk_tolerance": risk_tolerance,
            "recommendations": recommendations[:4],
            "allocation_suggestion": _get_allocation_suggestion(risk_tolerance)
        },
        risk_level=RiskLevel.GREEN
    )


def _get_recommendation_reason(product: Product, risk_tolerance: int) -> str:
    """生成推荐理由"""
    reasons = {
        1: "低风险，适合保守型投资者，流动性好",
        2: "中低风险，收益稳定，适合稳健型",
        3: "中等风险，股债平衡，适合平衡型",
        4: "中高风险，收益潜力大，适合进取型",
        5: "高风险，波动较大，适合激进型"
    }
    return reasons.get(product.risk_level, "")


def _get_allocation_suggestion(risk_tolerance: int) -> Dict[str, Any]:
    """资产配置建议"""
    suggestions = {
        1: {"货币基金": "50%", "债券": "40%", "混合": "10%", "股票": "0%"},
        2: {"货币基金": "30%", "债券": "45%", "混合": "20%", "股票": "5%"},
        3: {"货币基金": "20%", "债券": "35%", "混合": "30%", "股票": "15%"},
        4: {"货币基金": "10%", "债券": "20%", "混合": "35%", "股票": "35%"},
        5: {"货币基金": "5%", "债券": "10%", "混合": "30%", "股票": "55%"}
    }
    return suggestions.get(risk_tolerance, suggestions[3])


# ===== 操作类工具 =====

async def transfer(session: AsyncSession, to: str, amount: float, memo: str = "") -> ToolResult:
    """执行转账"""
    # 检查账户状态
    result = await session.execute(select(Account).where(Account.user_id == uid()))
    account = result.scalar_one_or_none()
    
    if not account:
        return ToolResult(success=False, error="账户不存在", risk_level=RiskLevel.GREEN)
    
    if account.is_locked:
        return ToolResult(success=False, error="账户已被锁定", risk_level=RiskLevel.RED)
    
    if amount <= 0:
        return ToolResult(success=False, error="转账金额必须大于0", risk_level=RiskLevel.GREEN)

    # 检查余额
    if account.balance < amount:
        return ToolResult(success=False, error=f"余额不足，当前余额 ¥{account.balance:,.2f}", risk_level=RiskLevel.GREEN)
    
    # 检查日累计限额
    today = datetime.now().strftime("%Y-%m-%d")
    if account.last_transfer_date != today:
        account.daily_transfer_total = 0
        account.last_transfer_date = today

    # 权限(确认/MFA)由上层 guarded_execute 统一把关，这里只负责执行
    risk_level = get_tool_risk_level("transfer", amount)

    # 执行转账
    account.balance -= amount
    account.daily_transfer_total += amount
    
    # 记录交易
    tx = Transaction(
        user_id=uid(),
        transaction_type="转出",
        amount=amount,
        counterparty=to,
        memo=memo or "转账",
        category="转账",
        timestamp=datetime.now()
    )
    session.add(tx)
    await session.commit()
    
    return ToolResult(
        success=True,
        data={
            "balance": account.balance,
            "amount": amount,
            "to": to,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        risk_level=risk_level,
        message=f"转账成功 ¥{amount:,.2f} 给 {to}"
    )


async def buy_product(session: AsyncSession, product_name: str, amount: float) -> ToolResult:
    """申购理财"""
    # 查找产品
    result = await session.execute(select(Product).where(Product.name == product_name))
    product = result.scalar_one_or_none()
    
    if not product:
        return ToolResult(success=False, error=f"未找到产品：{product_name}", risk_level=RiskLevel.RED)
    
    # 检查余额
    result = await session.execute(select(Account).where(Account.user_id == uid()))
    account = result.scalar_one_or_none()

    if not account:
        return ToolResult(success=False, error="账户不存在", risk_level=RiskLevel.RED)
    if amount <= 0:
        return ToolResult(success=False, error="申购金额必须大于0", risk_level=RiskLevel.RED)
    if amount < (product.min_amount or 0):
        return ToolResult(success=False, error=f"低于起投金额 ¥{product.min_amount:,.0f}", risk_level=RiskLevel.RED)
    if account.balance < amount:
        return ToolResult(success=False, error="余额不足", risk_level=RiskLevel.RED)
    
    # 创建持仓
    portfolio = Portfolio(
        user_id=uid(),
        product_id=product.id,
        amount=amount,
        current_value=amount,
        profit_loss=0
    )
    session.add(portfolio)
    
    # 更新余额
    account.balance -= amount
    
    await session.commit()
    
    return ToolResult(
        success=True,
        data={
            "product_name": product_name,
            "amount": amount,
            "annual_rate": product.annual_rate
        },
        risk_level=RiskLevel.RED,
        requires_mfa=True,
        message=f"申购成功 ¥{amount:,.2f} {product_name}"
    )


async def redeem_product(session: AsyncSession, product_name: str, amount: float = None) -> ToolResult:
    """赎回理财"""
    result = await session.execute(
        select(Portfolio, Product)
        .join(Product)
        .where(Portfolio.user_id == uid())
        .where(Product.name == product_name)
    )
    holding = result.first()
    
    if not holding:
        return ToolResult(success=False, error=f"未找到持仓：{product_name}", risk_level=RiskLevel.YELLOW)
    
    portfolio, product = holding
    
    if amount is None or amount >= portfolio.current_value:
        # 全额赎回
        redeem_amount = portfolio.current_value
        await session.delete(portfolio)
        message = f"全额赎回 {product_name} ¥{redeem_amount:,.2f}"
    else:
        # 部分赎回
        portfolio.current_value -= amount
        portfolio.amount = portfolio.current_value
        redeem_amount = amount
        message = f"部分赎回 {product_name} ¥{redeem_amount:,.2f}"
    
    # 更新余额
    result = await session.execute(select(Account).where(Account.user_id == uid()))
    account = result.scalar_one()
    account.balance += redeem_amount
    
    await session.commit()
    
    return ToolResult(
        success=True,
        data={"product_name": product_name, "redeem_amount": redeem_amount, "remaining": portfolio.current_value if holding else 0},
        risk_level=RiskLevel.YELLOW,
        message=message
    )


async def freeze_card(session: AsyncSession, card_number: str) -> ToolResult:
    """冻结卡片"""
    result = await session.execute(
        select(BankCard)
        .where(BankCard.user_id == uid())
        .where(BankCard.card_number.contains(card_number))
    )
    card = result.scalar_one_or_none()
    
    if not card:
        return ToolResult(success=False, error="未找到银行卡", risk_level=RiskLevel.YELLOW)
    
    card.status = "已冻结"
    await session.commit()
    
    return ToolResult(
        success=True,
        data={"card_name": card.card_name, "status": "已冻结"},
        risk_level=RiskLevel.YELLOW,
        message=f"{card.card_name} 已冻结"
    )


async def unfreeze_card(session: AsyncSession, card_number: str) -> ToolResult:
    """解冻卡片"""
    result = await session.execute(
        select(BankCard)
        .where(BankCard.user_id == uid())
        .where(BankCard.card_number.contains(card_number))
    )
    card = result.scalar_one_or_none()
    
    if not card:
        return ToolResult(success=False, error="未找到银行卡", risk_level=RiskLevel.YELLOW)
    
    card.status = "正常"
    await session.commit()
    
    return ToolResult(
        success=True,
        data={"card_name": card.card_name, "status": "正常"},
        risk_level=RiskLevel.YELLOW,
        message=f"{card.card_name} 已解冻"
    )


async def report_loss(session: AsyncSession, card_number: str) -> ToolResult:
    """挂失卡片"""
    result = await session.execute(
        select(BankCard)
        .where(BankCard.user_id == uid())
        .where(BankCard.card_number.contains(card_number))
    )
    card = result.scalar_one_or_none()
    
    if not card:
        return ToolResult(success=False, error="未找到银行卡", risk_level=RiskLevel.RED)
    
    card.status = "已挂失"
    await session.commit()
    
    return ToolResult(
        success=True,
        data={"card_name": card.card_name, "status": "已挂失"},
        risk_level=RiskLevel.RED,
        requires_mfa=True,
        message=f"{card.card_name} 已挂失，请尽快到柜台补办"
    )


async def cancel_subscription(session: AsyncSession, name: str) -> ToolResult:
    """取消订阅"""
    result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == uid())
        .where(Subscription.name == name)
    )
    sub = result.scalar_one_or_none()
    
    if not sub:
        return ToolResult(success=False, error=f"未找到订阅：{name}", risk_level=RiskLevel.YELLOW)
    
    sub.is_active = False
    await session.commit()
    
    return ToolResult(
        success=True,
        data={"name": name, "is_active": False},
        risk_level=RiskLevel.YELLOW,
        message=f"已取消 {name} 自动续费"
    )


async def create_rule(session: AsyncSession, trigger: str, action: str, amount: float = None, days_before: int = None) -> ToolResult:
    """创建联动规则"""
    rule = AutoRule(
        user_id=uid(),
        trigger=trigger,
        action=action,
        amount=amount,
        days_before=days_before,
        is_active=True
    )
    session.add(rule)
    await session.commit()
    
    return ToolResult(
        success=True,
        data={"trigger": trigger, "action": action},
        risk_level=RiskLevel.YELLOW,
        message=f"规则创建成功：{trigger}"
    )


# ===== 理财推荐工具 =====
async def get_risk_assessment(session: AsyncSession) -> ToolResult:
    """获取风险评估问卷"""
    from app.services.wealth_recommendation import wealth_service
    
    questions = wealth_service.generate_risk_assessment_questions()
    
    return ToolResult(
        success=True,
        data={"questions": questions},
        risk_level=RiskLevel.GREEN,
        message="请回答5个问题评估您的风险等级"
    )


async def assess_risk_profile(session: AsyncSession, q1: int = None, q2: int = None, q3: int = None, q4: int = None, q5: int = None) -> ToolResult:
    """评估风险等级"""
    from app.services.wealth_recommendation import wealth_service
    
    answers = {
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "q4": q4,
        "q5": q5
    }
    
    # 过滤掉 None 值
    answers = {k: v for k, v in answers.items() if v is not None}
    
    result = wealth_service.assess_risk_profile(answers)
    
    return ToolResult(
        success=True,
        data=result,
        risk_level=RiskLevel.GREEN,
        message=result["message"]
    )


async def get_wealth_recommendation(session: AsyncSession, risk_code: str) -> ToolResult:
    """获取理财推荐"""
    from app.services.wealth_recommendation import wealth_service
    
    result = wealth_service.get_product_recommendation(risk_code)
    
    return ToolResult(
        success=True,
        data=result,
        risk_level=RiskLevel.GREEN,
        message=result["message"]
    )


async def get_asset_pyramid(session: AsyncSession) -> ToolResult:
    """获取资产配置金字塔"""
    from app.services.wealth_recommendation import wealth_service
    
    result = wealth_service.get_asset_pyramid()
    
    return ToolResult(
        success=True,
        data=result,
        risk_level=RiskLevel.GREEN,
        message="资产配置金字塔信息"
    )


async def compare_products(session: AsyncSession, products: list = None) -> ToolResult:
    """对比产品"""
    from app.services.wealth_recommendation import wealth_service
    
    if not products:
        return ToolResult(success=False, error="未指定产品", risk_level=RiskLevel.GREEN)
    
    result = wealth_service.compare_products(products)
    
    return ToolResult(
        success=True,
        data=result,
        risk_level=RiskLevel.GREEN,
        message=result["message"]
    )


async def get_wealth_faq(session: AsyncSession, keyword: str = None) -> ToolResult:
    """获取理财FAQ"""
    from app.services.wealth_recommendation import wealth_service
    
    if keyword:
        result = wealth_service.get_faq(keyword)
        if not result:
            result = wealth_service.get_all_faqs()
    else:
        result = wealth_service.get_all_faqs()
    
    return ToolResult(
        success=True,
        data=result,
        risk_level=RiskLevel.GREEN,
        message="理财常见问题"
    )


async def analyze_finance(session: AsyncSession, monthly_income: float, monthly_expense: float, current_savings: float) -> ToolResult:
    """分析财务状况"""
    from app.services.wealth_recommendation import wealth_service
    
    result = wealth_service.analyze_financial_situation(
        monthly_income=monthly_income,
        monthly_expense=monthly_expense,
        current_savings=current_savings
    )
    
    return ToolResult(
        success=True,
        data=result,
        risk_level=RiskLevel.GREEN,
        message="财务分析完成"
    )


async def get_summary(session: AsyncSession) -> ToolResult:
    """账户概览: 余额、本月收支、储蓄率、持仓总额"""
    acc = (await session.execute(select(Account).where(Account.user_id == uid()))).scalar_one_or_none()
    if not acc:
        return ToolResult(success=False, error="账户不存在", risk_level=RiskLevel.GREEN)
    month = datetime.now().strftime("%Y-%m")
    txs = (await session.execute(select(Transaction).where(Transaction.user_id == uid()))).scalars().all()
    expense = sum(t.amount for t in txs if t.transaction_type == "转出" and t.timestamp.strftime("%Y-%m") == month)
    income = sum(t.amount for t in txs if t.transaction_type == "转入" and t.timestamp.strftime("%Y-%m") == month)
    holdings = (await session.execute(select(Portfolio).where(Portfolio.user_id == uid()))).scalars().all()
    return ToolResult(success=True, data={
        "name": acc.name, "balance": round(acc.balance, 2),
        "month_expense": round(expense, 2), "month_income": round(income, 2),
        "savings_rate": round((income - expense) / income * 100, 1) if income > 0 else None,
        "portfolio_value": round(sum(h.current_value for h in holdings), 2),
    }, risk_level=RiskLevel.GREEN)


async def get_contacts(session: AsyncSession) -> ToolResult:
    """常用收款人"""
    rows = (await session.execute(select(Contact).where(Contact.user_id == uid()))).scalars().all()
    return ToolResult(success=True, data={"contacts": [
        {"name": c.name, "phone": c.phone, "memo": c.memo} for c in rows
    ]}, risk_level=RiskLevel.GREEN)


async def get_wealth_analysis(session: AsyncSession, risk_code: str = "balanced",
                              amount: float = None) -> ToolResult:
    """专业理财分析：按『财产盘点→安全评估→收益考量→横向对比→买哪只』五步路径，
    结合业绩比较基准、费后收益、夏普/回撤、期限分层、核心-卫星与合规匹配，生成专业分析报告。"""
    from app.services.wealth_profiles import build_wealth_analysis

    # 可投资金额：默认用账户余额作为近似口径
    investable = None
    if amount is not None:
        try:
            investable = float(amount)
        except (TypeError, ValueError):
            investable = None
    if investable is None:
        acc = (await session.execute(select(Account).where(Account.user_id == uid()))).scalar_one_or_none()
        investable = acc.balance if acc else 0.0

    result = await session.execute(select(Product))
    products = [{"name": p.name, "tag": p.tag, "description": p.description,
                 "annual_rate": p.annual_rate, "risk_level": p.risk_level,
                 "min_amount": p.min_amount, "category": p.category} for p in result.scalars().all()]

    report = build_wealth_analysis(risk_code, products, investable)
    return ToolResult(
        success=True,
        data=report,
        risk_level=RiskLevel.GREEN,
        message=f"已按 {report['investor']['name']} 投资者生成专业理财分析报告"
    )


# ===== 工具映射表 =====
TOOL_IMPLEMENTATIONS = {
    "get_summary": get_summary,
    "get_contacts": get_contacts,
    "get_balance": get_balance,
    "get_transaction_history": get_transaction_history,
    "get_statement": get_statement,
    "get_products": get_products,
    "get_portfolio": get_portfolio,
    "get_cards": get_cards,
    "get_subscriptions": get_subscriptions,
    "get_rules": get_rules,
    "analyze_spending": analyze_spending,
    "recommend_products": recommend_products,
    "transfer": transfer,
    "buy_product": buy_product,
    "redeem_product": redeem_product,
    "freeze_card": freeze_card,
    "unfreeze_card": unfreeze_card,
    "report_loss": report_loss,
    "cancel_subscription": cancel_subscription,
    "create_rule": create_rule,
    "get_risk_assessment": get_risk_assessment,
    "assess_risk_profile": assess_risk_profile,
    "get_wealth_recommendation": get_wealth_recommendation,
    "get_asset_pyramid": get_asset_pyramid,
    "compare_products": compare_products,
    "get_wealth_faq": get_wealth_faq,
    "analyze_finance": analyze_finance,
    "get_wealth_analysis": get_wealth_analysis,
}
