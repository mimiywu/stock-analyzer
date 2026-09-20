"""現金流量分析模組"""
from typing import Dict, List
from utils import safe_divide


class CashFlowAnalyzer:
    """現金流量分析器"""

    def analyze(self, data: List[Dict]) -> Dict:
        """
        執行現金流量分析

        Args:
            data: 標準化財務數據列表

        Returns:
            Dict: 包含 quality, free_cash_flow, structure
        """
        if not data:
            return None

        results = []

        for period in data:
            operating_cf = period.get('operating_cash_flow', 0)
            net_income = period.get('net_income', 0)
            capex = period.get('capex', 0)
            investing_cf = period.get('investing_cash_flow', 0)
            financing_cf = period.get('financing_cash_flow', 0)

            # 1. 營運現金流品質
            cash_quality = safe_divide(operating_cf, net_income)

            # 2. 自由現金流
            free_cash_flow = operating_cf - abs(capex)

            # 3. 現金流結構
            total_cf = abs(operating_cf) + abs(investing_cf) + abs(financing_cf)
            structure = {
                'operating_ratio': safe_divide(abs(operating_cf), total_cf),
                'investing_ratio': safe_divide(abs(investing_cf), total_cf),
                'financing_ratio': safe_divide(abs(financing_cf), total_cf)
            }

            results.append({
                'period': period.get('period', ''),
                'operating_cash_flow': operating_cf,
                'net_income': net_income,
                'capex': capex,
                'free_cash_flow': free_cash_flow,
                'cash_quality_ratio': cash_quality,
                'structure': structure
            })

        # 綜合評估
        assessment = self._assess(results)

        return {
            'periods': results,
            'assessment': assessment
        }

    def _assess(self, results: List[Dict]) -> Dict:
        """綜合評估現金流狀況"""
        if not results:
            return {'rating': '無法評估', 'message': '無資料'}

        latest = results[0]

        # 評估營運現金流品質
        quality_rating = '優秀'
        if latest['cash_quality_ratio'] < 1.0:
            quality_rating = '需關注'
        elif latest['cash_quality_ratio'] < 1.2:
            quality_rating = '良好'

        # 評估自由現金流
        fcf_trend = '穩定'
        if len(results) >= 2:
            if latest['free_cash_flow'] > results[1]['free_cash_flow']:
                fcf_trend = '增長'
            elif latest['free_cash_flow'] < results[1]['free_cash_flow']:
                fcf_trend = '下降'

        # 評估現金流結構
        structure_assessment = '健康'
        if latest['structure']['operating_ratio'] < 0.5:
            structure_assessment = '營運現金流佔比偏低'

        return {
            'quality_rating': quality_rating,
            'fcf_trend': fcf_trend,
            'structure_assessment': structure_assessment,
            'latest_fcf': latest['free_cash_flow'],
            'latest_quality': latest['cash_quality_ratio']
        }
