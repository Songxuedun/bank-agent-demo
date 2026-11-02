"""
理财推荐服务 - 基于知识库的智能推荐
"""
from typing import Dict, List, Any, Optional
from app.services.wealth_knowledge import (
    RISK_ASSESSMENT,
    PRODUCT_COMPARISON,
    RECOMMENDATION_RULES,
    ASSET_PYRAMID,
    FAQS,
    calculate_risk_score,
    get_allocation_by_risk,
    get_product_info,
    recommend_products
)


class WealthRecommendationService:
    """理财推荐服务"""
    
    @staticmethod
    def generate_risk_assessment_questions() -> List[Dict[str, Any]]:
        """生成风险评估问卷"""
        return [
            {
                "id": q["id"],
                "question": q["question"],
                "options": [
                    {
                        "value": opt["value"],
                        "text": opt["text"]
                    }
                    for opt in q["options"]
                ]
            }
            for q in RISK_ASSESSMENT['questions']
        ]
    
    @staticmethod
    def assess_risk_profile(answers: Dict[str, int]) -> Dict[str, Any]:
        """
        根据答案评估风险等级
        answers: {
            "q1": 3,
            "q2": 2,
            ...
        }
        """
        # 构建答案列表
        answer_list = []
        for q in RISK_ASSESSMENT['questions']:
            q_id = q['id']
            if q_id in answers:
                for opt in q['options']:
                    if opt['value'] == answers[q_id]:
                        answer_list.append(opt)
                        break
        
        # 计算风险评分
        score = sum(opt['score'] for opt in answer_list)
        
        # 确定风险等级
        risk_profile = None
        for range_tuple, profile in RISK_ASSESSMENT['score_ranges'].items():
            if range_tuple[0] <= score <= range_tuple[1]:
                risk_profile = profile
                break
        
        if not risk_profile:
            risk_profile = RISK_ASSESSMENT['score_ranges'][(10, 15)]
        
        return {
            "risk_score": score,
            "risk_name": risk_profile['name'],
            "risk_code": risk_profile['code'],
            "allocation": risk_profile['allocation'],
            "message": f"根据您的问卷回答，您属于 {risk_profile['name']} 投资者。\n推荐配置：{risk_profile['allocation']}"
        }
    
    @staticmethod
    def get_product_recommendation(risk_code: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """获取产品推荐"""
        rules = get_allocation_by_risk(risk_code)
        
        # 构建详细推荐
        primary_details = []
        for prod_name in rules['primary']:
            info = get_product_info(prod_name)
            if info:
                primary_details.append({
                    "name": prod_name,
                    "annual_rate": info['annual_rate'],
                    "risk_level": info['risk_level'],
                    "suitable_for": info['suitable_for'],
                    "pros": info['pros']
                })
        
        return {
            "risk_level": risk_code,
            "primary_products": primary_details,
            "allocation_suggestion": rules['allocation'],
            "tips": rules['tips'],
            "message": f"根据您的风险等级，为您推荐以下产品组合...\n\n推荐配置：\n" + 
                      "\n".join([f"- {k}: {v*100:.0f}%" for k, v in rules['allocation'].items()])
        }
    
    @staticmethod
    def get_asset_pyramid() -> Dict[str, Any]:
        """获取资产配置金字塔"""
        return {
            "title": "资产配置金字塔",
            "description": "按照投资期限和风险承受度分层配置资产",
            "layers": [
                {
                    "layer": layer_key,
                    "name": layer_info['name'],
                    "percentage": layer_info['percentage'],
                    "products": layer_info['products'],
                    "rules": layer_info['rules']
                }
                for layer_key, layer_info in ASSET_PYRAMID.items()
            ]
        }
    
    @staticmethod
    def compare_products(product_names: List[str]) -> Dict[str, Any]:
        """对比多个产品"""
        comparison = {}
        for name in product_names:
            info = get_product_info(name)
            if info:
                comparison[name] = info
        
        return {
            "comparison": comparison,
            "message": "产品对比分析完成"
        }
    
    @staticmethod
    def get_faq(question_keyword: str) -> Optional[Dict[str, Any]]:
        """根据关键词查找常见问题"""
        for q, a in FAQS.items():
            if question_keyword in q:
                return {
                    "question": q,
                    "answer": a['answer'],
                    "related": a.get('related', [])
                }
        return None
    
    @staticmethod
    def get_all_faqs() -> Dict[str, Any]:
        """获取所有常见问题"""
        return {
            "faqs": [
                {
                    "question": q,
                    "answer": a['answer'],
                    "related": a.get('related', [])
                }
                for q, a in FAQS.items()
            ]
        }
    
    @staticmethod
    def analyze_financial_situation(
        monthly_income: float,
        monthly_expense: float,
        current_savings: float,
        investment_period_years: int = 5
    ) -> Dict[str, Any]:
        """
        分析财务状况并给出建议
        """
        monthly_surplus = monthly_income - monthly_expense
        monthly_rate = monthly_surplus / monthly_income if monthly_income > 0 else 0
        
        # 应急资金额度
        emergency_fund = monthly_expense * 3
        
        # 可投资额度
        investable = current_savings - emergency_fund
        
        # 推荐定投额度
        recommended_monthly_invest = monthly_surplus * 0.5
        
        analysis = {
            "monthly_income": monthly_income,
            "monthly_expense": monthly_expense,
            "monthly_surplus": monthly_surplus,
            "savings_rate": f"{monthly_rate*100:.1f}%",
            "current_savings": current_savings,
            "emergency_fund_needed": emergency_fund,
            "emergency_fund_status": "充足" if current_savings >= emergency_fund else "不足",
            "investable_amount": max(0, investable),
            "recommended_monthly_invest": recommended_monthly_invest,
            "investment_period": investment_period_years,
            "recommendations": []
        }
        
        # 给出建议
        if monthly_rate < 0.1:
            analysis["recommendations"].append("当前储蓄率过低，建议提升到至少20%")
        elif monthly_rate < 0.2:
            analysis["recommendations"].append("储蓄率一般，建议优化支出结构")
        else:
            analysis["recommendations"].append("储蓄率良好，建议加大投资")
        
        if current_savings < emergency_fund:
            analysis["recommendations"].append("应急资金不足，建议优先建立应急基金")
        else:
            analysis["recommendations"].append("应急资金充足，可进行长期投资")
        
        if investable > 0:
            analysis["recommendations"].append(
                f"可投资金额 ¥{investable:,.0f}，建议分批投入"
            )
        
        if recommended_monthly_invest > 0:
            analysis["recommendations"].append(
                f"建议月度定投 ¥{recommended_monthly_invest:,.0f}"
            )
        
        return analysis


# 服务实例
wealth_service = WealthRecommendationService()
