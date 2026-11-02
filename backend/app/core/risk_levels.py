"""
权限分级机制 - 核心安全设计
绿: 查询类操作,自动执行
黄: 小额转账/订阅管理,需确认
红: 大额转账/挂失/改密码,需 MFA
"""
from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass


class RiskLevel(str, Enum):
    """风险等级枚举"""
    GREEN = "green"    # 自动执行
    YELLOW = "yellow" # 需确认
    RED = "red"       # 需 MFA


@dataclass
class ToolPermission:
    """工具权限配置"""
    name: str
    risk_level: RiskLevel
    mfa_required: bool = False
    amount_threshold: float = 1000.0  # 金额阈值
    description: str = ""
    category: str = ""


# ===== 工具注册表 =====
TOOL_REGISTRY: Dict[str, ToolPermission] = {
    # ===== 绿色: 查询类 (自动执行) =====
    "get_balance": ToolPermission(name="get_balance", risk_level=RiskLevel.GREEN, description="查询账户余额", category="查询"),
    "get_transaction_history": ToolPermission(name="get_transaction_history", risk_level=RiskLevel.GREEN, description="查询交易记录", category="查询"),
    "get_statement": ToolPermission(name="get_statement", risk_level=RiskLevel.GREEN, description="获取账单分析", category="账单"),
    "get_products": ToolPermission(name="get_products", risk_level=RiskLevel.GREEN, description="查询理财产品列表", category="理财"),
    "get_portfolio": ToolPermission(name="get_portfolio", risk_level=RiskLevel.GREEN, description="查询持仓情况", category="理财"),
    "get_cards": ToolPermission(name="get_cards", risk_level=RiskLevel.GREEN, description="查询银行卡列表", category="卡片"),
    "get_subscriptions": ToolPermission(name="get_subscriptions", risk_level=RiskLevel.GREEN, description="查询订阅列表", category="订阅"),
    "get_rules": ToolPermission(name="get_rules", risk_level=RiskLevel.GREEN, description="查询联动规则", category="联动"),
    "analyze_spending": ToolPermission(name="analyze_spending", risk_level=RiskLevel.GREEN, description="消费分析", category="账单"),
    "recommend_products": ToolPermission(name="recommend_products", risk_level=RiskLevel.GREEN, description="理财推荐", category="理财"),
    "get_summary": ToolPermission(name="get_summary", risk_level=RiskLevel.GREEN, description="账户概览", category="查询"),
    "get_contacts": ToolPermission(name="get_contacts", risk_level=RiskLevel.GREEN, description="常用收款人", category="转账"),
    "get_risk_assessment": ToolPermission(name="get_risk_assessment", risk_level=RiskLevel.GREEN, description="风险评估问卷", category="理财"),
    "assess_risk_profile": ToolPermission(name="assess_risk_profile", risk_level=RiskLevel.GREEN, description="风险等级评估", category="理财"),
    "get_wealth_recommendation": ToolPermission(name="get_wealth_recommendation", risk_level=RiskLevel.GREEN, description="理财推荐", category="理财"),
    "get_asset_pyramid": ToolPermission(name="get_asset_pyramid", risk_level=RiskLevel.GREEN, description="资产金字塔", category="理财"),
    "compare_products": ToolPermission(name="compare_products", risk_level=RiskLevel.GREEN, description="产品对比", category="理财"),
    "get_wealth_faq": ToolPermission(name="get_wealth_faq", risk_level=RiskLevel.GREEN, description="理财问答", category="理财"),
    "analyze_finance": ToolPermission(name="analyze_finance", risk_level=RiskLevel.GREEN, description="财务分析", category="理财"),

    # ===== 黄色: 需确认 =====
    "transfer": ToolPermission(name="transfer", risk_level=RiskLevel.YELLOW, amount_threshold=1000.0, description="转账(小额)", category="转账"),
    "cancel_subscription": ToolPermission(name="cancel_subscription", risk_level=RiskLevel.YELLOW, description="取消订阅", category="订阅"),
    "adjust_limit": ToolPermission(name="adjust_limit", risk_level=RiskLevel.YELLOW, description="调整额度", category="卡片"),
    "freeze_card": ToolPermission(name="freeze_card", risk_level=RiskLevel.YELLOW, description="冻结卡片", category="卡片"),
    "unfreeze_card": ToolPermission(name="unfreeze_card", risk_level=RiskLevel.YELLOW, description="解冻卡片", category="卡片"),
    "redeem_product": ToolPermission(name="redeem_product", risk_level=RiskLevel.YELLOW, description="赎回理财", category="理财"),
    "create_rule": ToolPermission(name="create_rule", risk_level=RiskLevel.YELLOW, description="创建联动规则", category="联动"),

    # ===== 红色: 需 MFA =====
    "large_transfer": ToolPermission(name="large_transfer", risk_level=RiskLevel.RED, mfa_required=True, description="大额转账(>1000)", category="转账"),
    "report_loss": ToolPermission(name="report_loss", risk_level=RiskLevel.RED, mfa_required=True, description="卡片挂失", category="卡片"),
    "unreport_loss": ToolPermission(name="unreport_loss", risk_level=RiskLevel.RED, mfa_required=True, description="解除挂失", category="卡片"),
    "buy_product": ToolPermission(name="buy_product", risk_level=RiskLevel.RED, mfa_required=True, description="申购理财", category="理财"),
    "change_password": ToolPermission(name="change_password", risk_level=RiskLevel.RED, mfa_required=True, description="修改密码", category="安全"),
}


def get_tool_risk_level(tool_name: str, amount: float = 0) -> RiskLevel:
    """
    获取工具的风险等级
    金额相关工具根据金额动态调整风险等级
    """
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return RiskLevel.RED  # 未知工具默认最高风险
    
    # 转账工具根据金额判断
    if tool_name == "transfer":
        return RiskLevel.YELLOW if amount <= tool.amount_threshold else RiskLevel.RED
    
    return tool.risk_level


def get_risk_level_display(risk: RiskLevel) -> Dict[str, Any]:
    """获取风险等级展示信息"""
    displays = {
        RiskLevel.GREEN: {"color": "#22C55E", "label": "绿色", "action": "自动执行", "icon": "✓"},
        RiskLevel.YELLOW: {"color": "#F59E0B", "label": "黄色", "action": "需确认", "icon": "⚠"},
        RiskLevel.RED: {"color": "#EF4444", "label": "红色", "action": "需验证", "icon": "🔴"}
    }
    return displays.get(risk, displays[RiskLevel.RED])
