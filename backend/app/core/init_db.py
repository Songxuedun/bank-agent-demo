"""
数据库初始化与按用户生成演示数据
- 启动时只在表结构缺失/过期时重建，不会清掉已注册的用户
- seed_user() 同时用于注册新用户和创建演示账号
"""
import random
from datetime import datetime, timedelta

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import (
    Account, AutoRule, BankCard, Base, Contact, Portfolio, Product, Subscription, Transaction,
)
from app.core.security import hash_password

engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

CATEGORIES = ["餐饮", "购物", "交通", "居住", "娱乐", "其他"]
MERCHANTS = {
    "餐饮": ["美团外卖", "饿了么", "星巴克"], "购物": ["淘宝", "京东", "拼多多"],
    "交通": ["滴滴出行", "地铁"], "居住": ["房租", "物业水电"],
    "娱乐": ["电影院", "Steam"], "其他": ["药房", "便利店"],
}

PRODUCTS = [
    ("货币市场基金", "低风险", "流动性高，T+0 赎回。", "2.15%", 1, 100, "货币"),
    ("短债稳健基金", "中低风险", "投资高等级短期债券。", "3.42%", 2, 1000, "债券"),
    ("平衡混合基金", "中风险", "股债均衡配置。", "5.80%", 3, 1000, "混合"),
    ("科技成长股票", "中高风险", "聚焦科技板块，波动较大。", "8.60%", 4, 1000, "股票"),
    ("全球配置基金", "高风险", "跨市场资产配置。", "11.20%", 5, 1000, "全球"),
    ("养老目标日期基金", "长期", "按退休日期动态调整仓位。", "4.50%", 3, 1000, "养老"),
]

# 演示账号。密码只在首次建库时写入哈希，真实环境请删除。
DEMO_USERS = [
    ("user1", "123456", "张三", "138****8888", 128430.00, 15000),
    ("user2", "123456", "李四", "139****6666", 85320.75, 12000),
    ("user3", "123456", "王五", "137****2222", 200000.00, 20000),
]


async def _schema_is_current(conn) -> bool:
    def check(sync_conn):
        insp = inspect(sync_conn)
        if "accounts" not in insp.get_table_names():
            return False
        return "username" in {c["name"] for c in insp.get_columns("accounts")}
    return await conn.run_sync(check)


async def seed_user(session: AsyncSession, user_id: str, username: str, password: str,
                    name: str, phone: str, balance: float, monthly_income: float):
    """为一个用户创建账户及全套演示数据"""
    session.add(Account(
        user_id=user_id, username=username, password_hash=hash_password(password),
        name=name, phone=phone, balance=balance, daily_transfer_total=0.0,
        last_transfer_date=datetime.now().strftime("%Y-%m-%d"),
    ))
    await session.flush()  # 外键依赖 accounts

    tail = lambda: f"{random.randint(1000, 9999)}"
    session.add_all([
        BankCard(user_id=user_id, card_number=f"6222 **** **** {tail()}", card_name="招商银行储蓄卡",
                 card_type="储蓄卡", balance_or_limit=round(balance * 0.3, 2), status="正常"),
        BankCard(user_id=user_id, card_number=f"4895 **** **** {tail()}", card_name="中信信用卡",
                 card_type="信用卡", balance_or_limit=80000.00, status="正常"),
        BankCard(user_id=user_id, card_number=f"6217 **** **** {tail()}", card_name="建设银行借记卡",
                 card_type="储蓄卡", balance_or_limit=18200.00, status="已冻结"),
    ])

    # 持仓: 按余额比例，每个用户略有差异
    result = await session.execute(select(Product).order_by(Product.id))
    prods = result.scalars().all()
    for p, ratio, pnl in zip(prods[:4], (0.12, 0.2, 0.1, 0.05), (0.019, 0.022, 0.031, -0.006)):
        amt = round(balance * ratio * random.uniform(0.85, 1.15), 2)
        session.add(Portfolio(user_id=user_id, product_id=p.id, amount=amt,
                              current_value=round(amt * (1 + pnl), 2), profit_loss=round(amt * pnl, 2)))

    now = datetime.now()
    # 每月 1 日工资，覆盖最近 6 个月
    for m in range(6):
        first = (now.replace(day=1) - timedelta(days=30 * m)).replace(day=1, hour=9, minute=0, second=0, microsecond=0)
        if first <= now:
            session.add(Transaction(user_id=user_id, transaction_type="转入", amount=monthly_income,
                                    counterparty="公司工资", memo="工资", category="工资", timestamp=first))
    # 消费: 本月保证有数据，再补过去半年
    for i in range(150):
        days_ago = random.randint(0, 5) if i < 25 else random.randint(0, 180)
        ts = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        if ts > now:
            ts = now
        cat = random.choices(CATEGORIES, weights=[30, 22, 14, 8, 12, 14])[0]
        night = ts.hour >= 22 or ts.hour < 6
        suspicious = night and random.random() < 0.1
        session.add(Transaction(
            user_id=user_id, transaction_type="转出",
            amount=round(random.uniform(15, 700) if cat != "居住" else random.uniform(800, 2800), 2),
            counterparty=random.choice(MERCHANTS[cat]), memo=f"{cat}消费", category=cat,
            is_suspicious=suspicious, risk_score=random.uniform(0.3, 0.6) if suspicious else random.uniform(0, 0.1),
            timestamp=ts,
        ))

    session.add_all([
        Subscription(user_id=user_id, name="Netflix", logo="NF", cycle="月付", amount=45, next_date="2026-11-05"),
        Subscription(user_id=user_id, name="Spotify", logo="SP", cycle="月付", amount=18, next_date="2026-10-28"),
        Subscription(user_id=user_id, name="iCloud+", logo="IC", cycle="月付", amount=68, next_date="2026-10-15"),
        Subscription(user_id=user_id, name="京东PLUS", logo="JD", cycle="年付", amount=99, next_date="2027-01-12"),
    ])
    session.add_all([
        AutoRule(user_id=user_id, trigger="工资到账", action="工资的20%自动转入货币基金", amount=20, is_active=True),
        AutoRule(user_id=user_id, trigger="信用卡还款提醒", action="还款日前3天提醒", days_before=3, is_active=False),
    ])
    session.add_all([
        Contact(user_id=user_id, name="妈妈", phone="139****1234", memo="家人"),
        Contact(user_id=user_id, name="房东", phone="138****5678", memo="房租"),
        Contact(user_id=user_id, name="室友", phone="137****9012", memo="室友"),
    ])


async def init_db():
    """建表；结构过期时重建；首次建库写入产品和演示账号"""
    async with engine.begin() as conn:
        if not await _schema_is_current(conn):
            await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        if (await session.execute(select(Product).limit(1))).scalar_one_or_none() is None:
            for n, tag, desc, rate, risk, min_amt, cat in PRODUCTS:
                session.add(Product(name=n, tag=tag, description=desc, annual_rate=rate,
                                    risk_level=risk, min_amount=min_amt, category=cat))
            await session.flush()
        if (await session.execute(select(Account).limit(1))).scalar_one_or_none() is None:
            for username, pwd, name, phone, balance, income in DEMO_USERS:
                await seed_user(session, f"u_{username}", username, pwd, name, phone, balance, income)
        await session.commit()
        print("[OK] Database ready")


async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
