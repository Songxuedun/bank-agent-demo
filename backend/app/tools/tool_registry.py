"""
工具基类和工具注册表
每个工具都有 schema 定义，供 LLM Function Calling 使用
"""
from typing import Any, Dict, List, Optional, Callable
from app.core.risk_levels import RiskLevel


class ToolResult:
    """工具执行结果"""
    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        risk_level: RiskLevel = RiskLevel.GREEN,
        requires_confirmation: bool = False,
        requires_mfa: bool = False,
        message: str = ""
    ):
        self.success = success
        self.data = data or {}
        self.error = error
        self.risk_level = risk_level
        self.requires_confirmation = requires_confirmation
        self.requires_mfa = requires_mfa
        self.message = message
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "risk_level": self.risk_level.value,
            "requires_confirmation": self.requires_confirmation,
            "requires_mfa": self.requires_mfa,
            "message": self.message
        }


# ===== 工具定义 (Function Calling Schema) =====
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    # ===== 查询类 =====
    {
        "name": "get_balance",
        "description": "查询当前用户的账户余额",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_transaction_history",
        "description": "查询用户的交易记录",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "查询最近天数，默认30"},
                "limit": {"type": "integer", "description": "返回记录数量，默认20"}
            },
            "required": []
        }
    },
    {
        "name": "get_statement",
        "description": "获取月度账单分析，包括消费分类统计",
        "parameters": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "月份，格式YYYY-MM，默认为当前月份"}
            },
            "required": []
        }
    },
    {
        "name": "get_products",
        "description": "获取理财产品列表",
        "parameters": {
            "type": "object",
            "properties": {
                "risk_level": {"type": "integer", "description": "风险等级筛选(1-5)"}
            },
            "required": []
        }
    },
    {
        "name": "get_portfolio",
        "description": "查询当前持仓情况",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_cards",
        "description": "查询用户的银行卡列表",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_subscriptions",
        "description": "查询用户的订阅列表",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_rules",
        "description": "查询用户的联动规则",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "analyze_spending",
        "description": "分析用户消费习惯，识别异常消费",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "分析周期，week/month/year"}
            },
            "required": []
        }
    },
    {
        "name": "recommend_products",
        "description": "根据用户风险偏好推荐理财产品",
        "parameters": {
            "type": "object",
            "properties": {
                "risk_tolerance": {"type": "integer", "description": "风险承受度1-5"},
                "amount": {"type": "number", "description": "投资金额(元)"}
            },
            "required": []
        }
    },

    # ===== 转账类 =====
    {
        "name": "transfer",
        "description": "执行转账操作",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "收款人姓名或手机号"},
                "amount": {"type": "number", "description": "转账金额(元)"},
                "memo": {"type": "string", "description": "转账备注"}
            },
            "required": ["to", "amount"]
        }
    },

    # ===== 理财类 =====
    {
        "name": "buy_product",
        "description": "申购理财产品",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "产品名称"},
                "amount": {"type": "number", "description": "申购金额(元)"}
            },
            "required": ["product_name", "amount"]
        }
    },
    {
        "name": "redeem_product",
        "description": "赎回理财产品",
        "parameters": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "产品名称"},
                "amount": {"type": "number", "description": "赎回金额(元)，留空则全额赎回"}
            },
            "required": ["product_name"]
        }
    },

    # ===== 卡片类 =====
    {
        "name": "freeze_card",
        "description": "冻结银行卡",
        "parameters": {
            "type": "object",
            "properties": {
                "card_number": {"type": "string", "description": "卡号后4位"}
            },
            "required": ["card_number"]
        }
    },
    {
        "name": "unfreeze_card",
        "description": "解冻银行卡",
        "parameters": {
            "type": "object",
            "properties": {
                "card_number": {"type": "string", "description": "卡号后4位"}
            },
            "required": ["card_number"]
        }
    },
    {
        "name": "report_loss",
        "description": "挂失银行卡",
        "parameters": {
            "type": "object",
            "properties": {
                "card_number": {"type": "string", "description": "卡号后4位"}
            },
            "required": ["card_number"]
        }
    },
    {
        "name": "adjust_limit",
        "description": "调整信用卡额度",
        "parameters": {
            "type": "object",
            "properties": {
                "card_number": {"type": "string", "description": "卡号后4位"},
                "new_limit": {"type": "number", "description": "新额度(元)"}
            },
            "required": ["card_number", "new_limit"]
        }
    },

    # ===== 订阅类 =====
    {
        "name": "cancel_subscription",
        "description": "取消订阅自动续费",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "订阅名称"}
            },
            "required": ["name"]
        }
    },

    # ===== 联动类 =====
    {
        "name": "create_rule",
        "description": "创建跨场景联动规则",
        "parameters": {
            "type": "object",
            "properties": {
                "trigger": {"type": "string", "description": "触发事件"},
                "action": {"type": "string", "description": "执行动作"},
                "amount": {"type": "number", "description": "金额(可选)"},
                "days_before": {"type": "integer", "description": "提前天数(可选)"}
            },
            "required": ["trigger", "action"]
        }
    },

    # ===== 理财增强类 =====
    {
        "name": "get_risk_assessment",
        "description": "获取风险评估问卷，帮助用户确定投资风格",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "assess_risk_profile",
        "description": "根据用户答案评估风险等级",
        "parameters": {
            "type": "object",
            "properties": {
                "q1": {"type": "integer", "description": "问题1答案"},
                "q2": {"type": "integer", "description": "问题2答案"},
                "q3": {"type": "integer", "description": "问题3答案"},
                "q4": {"type": "integer", "description": "问题4答案"},
                "q5": {"type": "integer", "description": "问题5答案"}
            },
            "required": ["q1", "q2", "q3", "q4", "q5"]
        }
    },
    {
        "name": "get_wealth_recommendation",
        "description": "根据风险等级获取理财产品推荐",
        "parameters": {
            "type": "object",
            "properties": {
                "risk_code": {"type": "string", "description": "风险等级代码(conservative/moderate/balanced/aggressive/very_aggressive)"}
            },
            "required": ["risk_code"]
        }
    },
    {
        "name": "get_asset_pyramid",
        "description": "获取资产配置金字塔信息",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "compare_products",
        "description": "对比多个理财产品",
        "parameters": {
            "type": "object",
            "properties": {
                "products": {"type": "array", "items": {"type": "string"}, "description": "产品名称列表"}
            },
            "required": ["products"]
        }
    },
    {
        "name": "get_wealth_faq",
        "description": "查询理财常见问题",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词"}
            },
            "required": []
        }
    },
    {
        "name": "analyze_finance",
        "description": "分析用户财务状况并给出投资建议",
        "parameters": {
            "type": "object",
            "properties": {
                "monthly_income": {"type": "number", "description": "月收入"},
                "monthly_expense": {"type": "number", "description": "月支出"},
                "current_savings": {"type": "number", "description": "当前储蓄"}
            },
            "required": ["monthly_income", "monthly_expense", "current_savings"]
        }
    },
    {
        "name": "get_summary",
        "description": "账户概览: 余额、本月收入支出、储蓄率、理财持仓总额",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_wealth_analysis",
        "description": "生成专业理财分析报告：按财产盘点→安全评估→收益考量→横向对比→买哪只五步路径，包含业绩比较基准、费后收益、夏普/最大回撤、资金期限分层、核心-卫星配置与风险等级合规匹配",
        "parameters": {
            "type": "object",
            "properties": {
                "risk_code": {"type": "string", "description": "投资者风险等级代码(conservative/moderate/balanced/aggressive/very_aggressive)，默认balanced"},
                "amount": {"type": "number", "description": "可投资金额(元)，不传则用账户余额"}
            },
            "required": []
        }
    },
    {
        "name": "get_contacts",
        "description": "查询常用收款人列表",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
]
