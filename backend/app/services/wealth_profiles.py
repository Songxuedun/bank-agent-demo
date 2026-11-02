"""
理财专业分析引擎
基于《理财产品分析决策专家手册》的五步分析路径：
  财产盘点 → 安全评估 → 收益考量 → 横向对比 → 买哪只

落地要点（适当体现专业度，不做过度复杂化）：
- 收益口径：业绩比较基准 ≠ 收益承诺，区分基准与历史年化
- 费后收益：年化收益率 - 综合费率
- 风险调整后收益：夏普比率、最大回撤
- 合规红线：只能购买风险等级 R ≤ 自身 C 等级的产品
- 资金期限分层：应急 / 短期 / 中期 / 长期
- 核心-卫星配置：低风险核心 + 卫星增厚
- 风险预算：可投资金额 × 风险承受系数 = 可容忍亏损

说明：产品专业属性为演示数据，用于展示分析框架，不构成投资建议。
"""
from typing import Any, Dict, List, Optional

# ===== 风险等级与投资者等级映射（C1-C5） =====
# 与 wealth_knowledge.RISK_ASSESSMENT 的 risk_code 对应
INVESTOR_LEVEL = {
    "conservative": {"level": 1, "name": "谨慎型", "code": "C1"},
    "moderate": {"level": 2, "name": "稳健型", "code": "C2"},
    "balanced": {"level": 3, "name": "平衡型", "code": "C3"},
    "aggressive": {"level": 4, "name": "进取型", "code": "C4"},
    "very_aggressive": {"level": 5, "name": "激进型", "code": "C5"},
}

RISK_NAMES = {
    1: "R1 谨慎型", 2: "R2 稳健型", 3: "R3 平衡型",
    4: "R4 进取型", 5: "R5 激进型",
}

# 风险承受系数参考（手册 2.3）：可容忍亏损额 = 可投资金融资产 × 系数
RISK_TOLERANCE_COEF = {
    1: 0.10, 2: 0.15, 3: 0.20, 4: 0.30, 5: 0.40,
}

# ===== 产品专业画像（按产品名），与数据库 Product 数据一致 =====
# benchmark: 业绩比较基准(管理人投资目标, 非承诺)
# fee_rate: 综合费率(年化%)；max_drawdown: 近一年最大回撤%；sharpe: 夏普比率
# term: 建议持有期限；liquidity: 赎回规则；underlying: 底层资产；category: 手册品类
PRODUCT_PROFILES: Dict[str, Dict[str, Any]] = {
    "货币市场基金": {
        "category": "现金类", "risk_name": "R1 谨慎型",
        "benchmark": "1.80%", "fee_rate": 0.25, "max_drawdown": 0.0, "sharpe": 1.8,
        "term": "随时可取", "liquidity": "T+0 赎回", "underlying": "高等级货币工具、利率债",
    },
    "短债稳健基金": {
        "category": "固收类", "risk_name": "R2 稳健型",
        "benchmark": "3.00%", "fee_rate": 0.35, "max_drawdown": 0.5, "sharpe": 1.5,
        "term": "1-3 年", "liquidity": "赎回 T+1", "underlying": "高等级信用债、利率债",
    },
    "平衡混合基金": {
        "category": "固收+/混合", "risk_name": "R3 平衡型",
        "benchmark": "5.50%", "fee_rate": 0.60, "max_drawdown": 6.0, "sharpe": 1.1,
        "term": "1-3 年", "liquidity": "定期开放", "underlying": "债券为主 + 少量权益",
    },
    "养老目标日期基金": {
        "category": "养老/长期", "risk_name": "R3 平衡型",
        "benchmark": "4.20%", "fee_rate": 0.55, "max_drawdown": 3.5, "sharpe": 1.3,
        "term": "3 年以上", "liquidity": "定期开放", "underlying": "固收+ 动态配置",
    },
    "科技成长股票": {
        "category": "权益类", "risk_name": "R4 进取型",
        "benchmark": "7.50%", "fee_rate": 0.90, "max_drawdown": 18.0, "sharpe": 0.7,
        "term": "5 年以上", "liquidity": "赎回 T+1", "underlying": "科技成长权益",
    },
    "全球配置基金": {
        "category": "多资产", "risk_name": "R5 激进型",
        "benchmark": "9.50%", "fee_rate": 0.85, "max_drawdown": 14.0, "sharpe": 0.9,
        "term": "5 年以上", "liquidity": "定期开放", "underlying": "跨市场多资产配置",
    },
}

# 资金期限分层（手册 2.4）
TERM_LAYERS = [
    {"layer": "应急层", "term": "随时可取（≤6 个月生活费）", "products": "现金管理类理财、货币基金", "need": "安全 + 高流动"},
    {"layer": "短期层", "term": "1 年内要用", "products": "短债基金、同业存单指数", "need": "流动 + 略增收益"},
    {"layer": "中期层", "term": "1-3 年", "products": "纯固收理财、储蓄国债", "need": "稳健增值"},
    {"layer": "长期层", "term": "3 年以上", "products": "固收+、养老理财（按风险承受）", "need": "收益增强"},
]


def _parse_rate(rate_str: str) -> float:
    """把 '2.15%' 解析成 2.15；空或异常返回 0"""
    try:
        return float(str(rate_str).replace("%", "").strip())
    except (TypeError, ValueError):
        return 0.0


def enrich_product(product: Dict[str, Any]) -> Dict[str, Any]:
    """把专业画像并入数据库产品记录，并计算费后收益等派生指标"""
    name = product.get("name", "")
    profile = PRODUCT_PROFILES.get(name, {})
    annual = _parse_rate(product.get("annual_rate"))
    fee = profile.get("fee_rate", 0.0)
    enriched = {
        **product,
        "category": profile.get("category", "未分类"),
        "risk_name": profile.get("risk_name", RISK_NAMES.get(product.get("risk_level", 0), "未知")),
        "benchmark": profile.get("benchmark", "-"),      # 业绩比较基准
        "benchmark_rate": _parse_rate(profile.get("benchmark", "")),
        "fee_rate": fee,                                 # 综合费率(年化%)
        "fee_after_rate": round(max(annual - fee, 0.0), 2),  # 费后年化
        "max_drawdown": profile.get("max_drawdown", 0.0),   # 最大回撤%
        "sharpe": profile.get("sharpe", 0.0),               # 夏普比率
        "term": profile.get("term", "-"),                   # 建议期限
        "liquidity": profile.get("liquidity", "-"),         # 赎回规则
        "underlying": profile.get("underlying", "-"),       # 底层资产
    }
    return enriched


def safety_score(p: Dict[str, Any]) -> Dict[str, Any]:
    """安全评估（手册 3.7，5 分制）：风险越低越安全"""
    risk = p.get("risk_level", 3)
    dd = p.get("max_drawdown", 0.0)
    score = max(1.0, round(5.0 - (risk - 1) * 0.9 - min(dd, 20) * 0.05, 1))
    return {"score": score, "max": 5, "note": f"风险等级{risk}，最大回撤约{dd}%"}


def return_score(p: Dict[str, Any]) -> Dict[str, Any]:
    """收益考量（手册 4.7，5 分制）：费后收益 + 夏普性价比"""
    fee_after = p.get("fee_after_rate", 0.0)
    sharpe = p.get("sharpe", 0.0)
    # 费后收益按 0-12% 折算，夏普 ≥1.2 计满分段
    s1 = min(fee_after / 12.0, 1.0) * 3.0
    s2 = 2.0 if sharpe >= 1.2 else (1.0 if sharpe >= 0.8 else 0.5)
    return {"score": round(min(5.0, s1 + s2), 1), "max": 5, "note": f"费后年化约{fee_after}%，夏普{sharpe}"}


def build_wealth_analysis(risk_code: str, products: List[Dict[str, Any]],
                          investable_amount: float) -> Dict[str, Any]:
    """按五步路径生成专业理财分析报告

    risk_code: conservative/moderate/balanced/aggressive/very_aggressive
    products: 数据库 Product 记录列表（含 name/annual_rate/risk_level/min_amount/tag/description）
    investable_amount: 可投资金融资产（元），用于风险预算测算
    """
    investor = INVESTOR_LEVEL.get(risk_code, INVESTOR_LEVEL["balanced"])
    c_level = investor["level"]
    c_name = investor["name"]
    c_code = investor["code"]

    enriched = [enrich_product(p) for p in products]
    enriched.sort(key=lambda x: x["risk_level"])

    # 合规红线：R ≤ C
    allowed = [p for p in enriched if p["risk_level"] <= c_level]
    blocked = [p for p in enriched if p["risk_level"] > c_level]
    allowed_names = [p["name"] for p in allowed]
    blocked_names = [p["name"] for p in blocked]

    # 核心-卫星（手册 6.3）：低风险核心 70-80% + 卫星 20-30%
    core = [p for p in allowed if p["risk_level"] <= min(c_level, 2)]
    satellite = [p for p in allowed if p["risk_level"] > min(c_level, 2)]
    core_pct = 80 if not satellite else 70

    # 风险预算（手册 2.3）
    coef = RISK_TOLERANCE_COEF[c_level]
    tolerable_loss = round(investable_amount * coef, 2)

    # 产品专业卡片
    product_cards = []
    for p in enriched:
        s = safety_score(p)
        r = return_score(p)
        fit = "合规可买" if p["risk_level"] <= c_level else "超过自身等级，不建议"
        product_cards.append({
            "name": p["name"],
            "category": p["category"],
            "risk_name": p["risk_name"],
            "benchmark": p["benchmark"],
            "annual_rate": p["annual_rate"],
            "fee_after_rate": p["fee_after_rate"],
            "fee_rate": p["fee_rate"],
            "max_drawdown": p["max_drawdown"],
            "sharpe": p["sharpe"],
            "term": p["term"],
            "liquidity": p["liquidity"],
            "underlying": p["underlying"],
            "min_amount": p["min_amount"],
            "description": p.get("description", ""),
            "safety_score": s,
            "return_score": r,
            "fit": fit,
            "tips": _product_tip(p),
        })

    # 收益口径提示（手册 1.1 / 4.1）
    benchmark_warning = (
        "业绩比较基准是管理人设定的投资目标，不是收益承诺；"
        "实际收益以净值表现为准，可能存在浮动甚至阶段性回撤。"
    )

    five_step = [
        {"step": "1. 财产盘点", "content": f"可投资金额约 ¥{investable_amount:,.0f}，建议按应急/短期/中期/长期四层切分，先留足应急资金。"},
        {"step": "2. 安全评估", "content": f"您为{c_code} {c_name}投资者，只宜购买风险等级 ≤ {c_level} 的产品。{'可买：' + '、'.join(allowed_names) if allowed_names else '当前无匹配产品'}。"},
        {"step": "3. 收益考量", "content": benchmark_warning + "比较时以费后年化与夏普比率为准，不只看展示收益率。"},
        {"step": "4. 横向对比", "content": "同类、同期限、同风险等级才可比，避免拿 R2 与 R4 的收益直接比较。"},
        {"step": "5. 买哪只", "content": f"建议核心-卫星配置：核心约 {core_pct}%（{('、'.join([c['name'] for c in core]) or '现金/固收')}），卫星约 {100 - core_pct}%（{('、'.join([s['name'] for s in satellite]) or '暂不配置')}）。"},
    ]

    return {
        "investor": {"code": c_code, "name": c_name, "risk_level": c_level, "risk_code": risk_code},
        "investable_amount": investable_amount,
        "risk_budget": {
            "coefficient": coef, "tolerable_loss": tolerable_loss,
            "note": f"按{c_name}风险承受系数 {coef:.0%}，单年可容忍亏损约 ¥{tolerable_loss:,.0f}",
        },
        "five_step": five_step,
        "compliance": {
            "rule": "只购买风险等级 R ≤ 自身等级 C 的产品",
            "allowed": allowed_names, "blocked": blocked_names,
        },
        "term_layers": TERM_LAYERS,
        "core_satellite": {
            "core": [c["name"] for c in core], "core_pct": core_pct,
            "satellite": [s["name"] for s in satellite], "satellite_pct": 100 - core_pct,
        },
        "products": product_cards,
        "disclaimer": "本分析为专业框架演示，不构成投资建议。理财非存款，产品有风险，投资须谨慎。",
    }


def _product_tip(p: Dict[str, Any]) -> str:
    """每只产品的风险提示"""
    risk = p["risk_level"]
    if risk <= 2:
        return "以利率债/高等级信用债为主，净值波动小，适合作为稳健底仓。"
    if risk == 3:
        return "含一定权益或可转债敞口，净值有波动，建议以中期资金配置。"
    return "高波动、高潜在收益，须以风险预算为上限，且用长期不用的钱配置。"
