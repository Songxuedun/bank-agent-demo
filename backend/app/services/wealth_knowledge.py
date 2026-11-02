"""
理财知识库 - 基于指南的结构化数据
包含: 资产配置、产品选择、风险评估
"""

# ===== 五层资产配置金字塔 =====
ASSET_PYRAMID = {
    "layer_1": {
        "name": "应急资金 (底层)",
        "percentage": "3-6个月刚性支出",
        "products": [
            {"name": "货币基金", "rate": "0.8%-1.2%", "features": ["随时可取", "T+0赎回", "风险最低"]},
            {"name": "现金管理类理财", "rate": "1.0%-1.5%", "features": ["高流动性", "每日计息", "银行发行"]},
            {"name": "7天通知存款", "rate": "1.2%-1.5%", "features": ["提前支取有罚息", "银行产品", "安全性高"]},
        ],
        "rules": [
            "不能为了多0.3%收益放进有封闭期的产品",
            "确保随时可取",
            "优先选流动性强的"
        ]
    },
    
    "layer_2": {
        "name": "保本稳健 (第二层)",
        "percentage": "1-3年内确定支出",
        "products": [
            {"name": "定期存款", "rate": "1.3%-3.0%", "features": ["本息有保障", "利息固定", "需锁定"]},
            {"name": "大额存单", "rate": "1.5%-3.0%", "features": ["20万起", "利率更高", "提前支取有损失"]},
            {"name": "短债基金", "rate": "1.8%-2.5%", "features": ["低波动", "1-3年持有", "适合稳健"]},
        ],
        "rules": [
            "选择1-3年期限的定存",
            "大额存单需要20万起投",
            "短债基金不要频繁交易"
        ]
    },
    
    "layer_3": {
        "name": "收益增强 (中间层)",
        "percentage": "3-5年内可用资金",
        "products": [
            {"name": "债券基金", "rate": "2.0%-3.5%", "features": ["波动较小", "收益稳定", "可定投"]},
            {"name": "平衡混合基金", "rate": "3.0%-5.0%", "features": ["股债均衡", "收益稳健", "适合懒人"]},
            {"name": "指数基金", "rate": "5.0%-8.0%", "features": ["跟踪大盘", "费用低", "长期收益好"]},
        ],
        "rules": [
            "混合基金可作为核心持仓",
            "指数基金要长期持有(3年+)",
            "不要频繁换基金"
        ]
    },
    
    "layer_4": {
        "name": "增长动力 (上层)",
        "percentage": "5年以上用不到的钱",
        "products": [
            {"name": "主动管理股票基金", "rate": "8.0%-15.0%", "features": ["择时选股", "风险较高", "需选好基金经理"]},
            {"name": "科技成长主题", "rate": "10.0%-20.0%", "features": ["高波动", "高收益", "长期看好"]},
            {"name": "行业主题基金", "rate": "8.0%-15.0%", "features": ["聚焦赛道", "风险集中", "看好行业"]},
        ],
        "rules": [
            "要选择业绩稳定的基金经理",
            "坚持定投，不要择时",
            "最少要持有3-5年"
        ]
    },
    
    "layer_5": {
        "name": "保险保障 (顶层)",
        "percentage": "养老/重疾保险",
        "products": [
            {"name": "养老保险", "rate": "3.0%-4.0%", "features": ["强制储蓄", "税收优惠", "长期锁定"]},
            {"name": "重疾保险", "rate": "保障性", "features": ["保额高", "保障全面", "保费便宜"]},
            {"name": "医疗保险", "rate": "保障性", "features": ["覆盖范围广", "报销比例高"]},
        ],
        "rules": [
            "优先配置保障",
            "养老可用定投",
            "重疾选择保额足够的"
        ]
    }
}


# ===== 风险评估问卷 =====
RISK_ASSESSMENT = {
    "questions": [
        {
            "id": "q1",
            "question": "您距离退休还有多少年?",
            "options": [
                {"value": 1, "text": "3年以内", "score": -2},
                {"value": 2, "text": "3-10年", "score": 0},
                {"value": 3, "text": "10-20年", "score": 1},
                {"value": 4, "text": "20年以上", "score": 2}
            ]
        },
        {
            "id": "q2",
            "question": "过去一年，您的收入是否稳定?",
            "options": [
                {"value": 1, "text": "不稳定，波动大", "score": -1},
                {"value": 2, "text": "基本稳定", "score": 0},
                {"value": 3, "text": "很稳定", "score": 1}
            ]
        },
        {
            "id": "q3",
            "question": "如果投资亏损10%，您会?",
            "options": [
                {"value": 1, "text": "立即卖出", "score": -2},
                {"value": 2, "text": "继续持有", "score": 0},
                {"value": 3, "text": "继续买入", "score": 2}
            ]
        },
        {
            "id": "q4",
            "question": "年收入中，可用于投资的比例?",
            "options": [
                {"value": 1, "text": "0-10%", "score": -1},
                {"value": 2, "text": "10-30%", "score": 0},
                {"value": 3, "text": "30-50%", "score": 1},
                {"value": 4, "text": "50%以上", "score": 2}
            ]
        },
        {
            "id": "q5",
            "question": "您对金融产品的了解程度?",
            "options": [
                {"value": 1, "text": "几乎不了解", "score": -1},
                {"value": 2, "text": "基本了解", "score": 0},
                {"value": 3, "text": "比较了解", "score": 1}
            ]
        }
    ],
    "score_ranges": {
        (-10, -5): {"name": "保守型", "code": "conservative", "allocation": "现金40% + 债券50% + 权益10%"},
        (-5, 0): {"name": "稳健型", "code": "moderate", "allocation": "现金20% + 债券50% + 权益30%"},
        (0, 5): {"name": "平衡型", "code": "balanced", "allocation": "现金10% + 债券40% + 权益50%"},
        (5, 10): {"name": "进取型", "code": "aggressive", "allocation": "现金5% + 债券25% + 权益70%"},
        (10, 15): {"name": "激进型", "code": "very_aggressive", "allocation": "现金2% + 债券15% + 权益83%"}
    }
}


# ===== 产品对比矩阵 =====
PRODUCT_COMPARISON = {
    "货币基金": {
        "annual_rate": "0.8%-1.5%",
        "risk_level": 1,
        "liquidity": "T+0",
        "min_amount": 100,
        "holding_period": "灵活",
        "suitable_for": ["应急资金", "闲散资金"],
        "pros": ["风险极低", "随时可取", "管理费低"],
        "cons": ["收益低", "无本金保障但实际无风险"],
        "tax": "不征税"
    },
    
    "债券基金": {
        "annual_rate": "2.0%-4.0%",
        "risk_level": 2,
        "liquidity": "T+1-2",
        "min_amount": 1000,
        "holding_period": "1-3年",
        "suitable_for": ["稳健投资者", "定投"],
        "pros": ["收益稳定", "波动小", "可定投"],
        "cons": ["利率上升时会贬值", "费用(0.5%-1%)相对高"],
        "tax": "不征税"
    },
    
    "混合基金": {
        "annual_rate": "4.0%-8.0%",
        "risk_level": 3,
        "liquidity": "T+1-2",
        "min_amount": 1000,
        "holding_period": "3-5年",
        "suitable_for": ["平衡投资者", "核心持仓"],
        "pros": ["股债均衡", "收益可观", "波动适中"],
        "cons": ["需要择基金经理", "费用(0.6%-1.5%)较高", "需要长期持有"],
        "tax": "不征税"
    },
    
    "股票基金": {
        "annual_rate": "8.0%-15.0%",
        "risk_level": 4,
        "liquidity": "T+1-2",
        "min_amount": 1000,
        "holding_period": "5年+",
        "suitable_for": ["进取投资者", "长期规划"],
        "pros": ["收益潜力大", "长期胜率高", "分散风险"],
        "cons": ["波动大", "需要心理承受能力", "短期可能亏损"],
        "tax": "不征税"
    },
    
    "定期存款": {
        "annual_rate": "1.3%-3.5%",
        "risk_level": 1,
        "liquidity": "到期支取",
        "min_amount": 50,
        "holding_period": "3个月-5年",
        "suitable_for": ["保本投资", "确定支出"],
        "pros": ["本息有保障", "利率固定", "安心"],
        "cons": ["流动性差", "提前支取无利息", "收益低"],
        "tax": "利息所得税20%"
    },
    
    "指数基金": {
        "annual_rate": "8.0%-12.0%",
        "risk_level": 4,
        "liquidity": "T+1-2",
        "min_amount": 1000,
        "holding_period": "5年+",
        "suitable_for": ["懒人投资", "定投"],
        "pros": ["管理费极低", "透明", "长期收益好"],
        "cons": ["只能跟踪大盘", "不能超额收益", "需定投"],
        "tax": "不征税"
    }
}


# ===== 推荐规则引擎 =====
RECOMMENDATION_RULES = {
    "conservative": {
        "primary": ["货币基金", "7天通知存款", "定期存款"],
        "secondary": ["债券基金", "短债基金"],
        "avoid": ["股票基金", "科技主题", "指数基金"],
        "allocation": {
            "现金类": 0.4,
            "债券类": 0.5,
            "权益类": 0.1
        },
        "tips": [
            "不追求高收益，重点是本金安全",
            "可配置30%债券基金获得稳定增长",
            "剩余资金放在货币基金应急"
        ]
    },
    
    "moderate": {
        "primary": ["短债基金", "混合基金", "定期存款"],
        "secondary": ["债券基金", "指数基金"],
        "avoid": ["单一科技主题", "激进股票基金"],
        "allocation": {
            "现金类": 0.2,
            "债券类": 0.5,
            "权益类": 0.3
        },
        "tips": [
            "核心持仓混合基金 (40%)",
            "定投指数基金 (20%)",
            "债券基金提供稳定收益 (30%)",
            "保留应急资金 (10%)"
        ]
    },
    
    "balanced": {
        "primary": ["混合基金", "指数基金", "债券基金"],
        "secondary": ["股票基金", "短债基金"],
        "avoid": ["单一风险过高主题"],
        "allocation": {
            "现金类": 0.1,
            "债券类": 0.4,
            "权益类": 0.5
        },
        "tips": [
            "50%投入权益类获得增长",
            "混合基金 + 指数基金搭配",
            "40%债券提供稳定收益",
            "定投策略，坚持3年+"
        ]
    },
    
    "aggressive": {
        "primary": ["指数基金", "混合基金", "股票基金"],
        "secondary": ["科技主题", "行业基金"],
        "avoid": ["现金过多"],
        "allocation": {
            "现金类": 0.05,
            "债券类": 0.25,
            "权益类": 0.7
        },
        "tips": [
            "70%权益类获得增长",
            "60%定投指数基金 (不择时)",
            "20%主动基金寻求超额收益",
            "需要心理承受能力，可能有年亏损"
        ]
    },
    
    "very_aggressive": {
        "primary": ["股票基金", "指数基金", "科技主题"],
        "secondary": ["行业基金", "新兴市场"],
        "avoid": ["债券过多"],
        "allocation": {
            "现金类": 0.02,
            "债券类": 0.15,
            "权益类": 0.83
        },
        "tips": [
            "追求长期增长，忽视短期波动",
            "80%权益类配置",
            "可尝试科技、新兴行业",
            "需要5年+的投资周期",
            "建议定投，平滑成本"
        ]
    }
}


# ===== 常见问题库 =====
FAQS = {
    "我应该如何开始投资?": {
        "answer": "1. 先准备3-6个月生活费放在货币基金\n2. 完成风险评估问卷\n3. 根据建议选择3-5个基金\n4. 定投500元/月开始\n5. 每月检查一次，不频繁交易",
        "related": ["定投", "基金选择"]
    },
    
    "定投好还是一次性投入好?": {
        "answer": "对大多数人：定投更好\n理由：\n- 平滑成本，避免高位套牢\n- 坚持力更强\n- 心理压力小\n- 长期收益不差，甚至更好\n\n只有当你确定底部时，才用一次性投入。",
        "related": ["定投策略"]
    },
    
    "基金亏损了怎么办?": {
        "answer": "分情况：\n1. 如果还在投资期内：继续定投！低价买入更多\n2. 如果已到预定期限：按计划赎回\n3. 如果是突发事件导致的亏损：再给基金一年时间\n\n记住：长期看，股票基金的胜率是7-8成。不要被短期波动吓到。",
        "related": ["长期投资", "定投心态"]
    },
    
    "我应该买多少只基金?": {
        "answer": "建议：\n- 新手：3-5只就够\n- 稳健型：5-7只\n- 进取型：7-10只\n\n为什么不要太多：\n- 管理成本高\n- 容易重复持仓\n- 心理压力大\n\n宁可买得少，也别买太多。",
        "related": ["基金选择", "组合配置"]
    },
    
    "什么时候应该赎回基金?": {
        "answer": "赎回时机：\n1. 到达预定投资期限（3年/5年/10年）\n2. 目标金额达成\n3. 急需用钱（不得已）\n4. 基金长期表现很差（换新基金）\n\n不应该赎回：\n- 短期亏损\n- 看新闻吓到\n- 股市下跌时\n- 频繁\"抄底\"",
        "related": ["赎回策略", "长期投资"]
    }
}


# ===== 工具函数 =====
def calculate_risk_score(answers):
    """根据问卷计算风险评分"""
    total_score = sum(opt['score'] for opt in answers)
    for range_tuple, risk_info in RISK_ASSESSMENT['score_ranges'].items():
        if range_tuple[0] <= total_score < range_tuple[1]:
            return risk_info
    return RISK_ASSESSMENT['score_ranges'][(10, 15)]


def get_allocation_by_risk(risk_code):
    """根据风险等级获取推荐配置"""
    return RECOMMENDATION_RULES.get(risk_code, RECOMMENDATION_RULES['moderate'])


def get_product_info(product_name):
    """获取产品详细信息"""
    return PRODUCT_COMPARISON.get(product_name)


def recommend_products(risk_code, amount=None):
    """推荐产品列表"""
    rules = get_allocation_by_risk(risk_code)
    return {
        "primary_products": rules['primary'],
        "secondary_products": rules['secondary'],
        "allocation": rules['allocation'],
        "tips": rules['tips']
    }


def get_asset_pyramid_info():
    """获取资产配置金字塔信息"""
    return ASSET_PYRAMID
