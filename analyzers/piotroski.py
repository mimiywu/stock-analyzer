"""Piotroski F-Score 分析模組"""
from typing import Dict, List
from utils import safe_divide


class PiotroskiAnalyzer:
    """Piotroski F-Score 分析器"""

    def analyze(self, data: List[Dict]) -> Dict:
        """
        執行 Piotroski F-Score 分析

        Args:
            data: 標準化財務數據列表（按時間排序，最新在前）

        Returns:
            Dict: 包含 total_score 和 indicators 明細
        """
        if not data or len(data) < 2:
            return {
                'total_score': 0,
                'indicators': [],
                'error': '資料不足，需要至少兩期數據'
            }

        current = data[0]
        previous = data[1]

        indicators = []

        # 獲利能力指標（4項）
        # 1. ROA > 0
        current_roa = safe_divide(current['net_income'], current['total_assets'])
        score = 1 if current_roa > 0 else 0
        indicators.append({
            'name': 'ROA > 0',
            'value': f'{current_roa:.4f}',
            'score': score
        })

        # 2. 營運現金流 > 0
        operating_cf = current.get('operating_cash_flow', 0)
        score = 1 if operating_cf > 0 else 0
        indicators.append({
            'name': '營運現金流 > 0',
            'value': f'{operating_cf:,.0f}',
            'score': score
        })

        # 3. ROA 年增率 > 0
        previous_roa = safe_divide(previous['net_income'], previous['total_assets'])
        roa_change = current_roa - previous_roa
        score = 1 if roa_change > 0 else 0
        indicators.append({
            'name': 'ROA 年增率 > 0',
            'value': f'{roa_change:.4f}',
            'score': score
        })

        # 4. 營運現金流 > 淨利
        score = 1 if operating_cf > current['net_income'] else 0
        indicators.append({
            'name': '營運現金流 > 淨利',
            'value': f'OCF: {operating_cf:,.0f}, NI: {current["net_income"]:,.0f}',
            'score': score
        })

        # 槓桿與流動性指標（3項）
        # 5. 長期負債比率下降
        current_lt_debt_ratio = safe_divide(
            current.get('long_term_debt', 0),
            current['total_assets']
        )
        previous_lt_debt_ratio = safe_divide(
            previous.get('long_term_debt', 0),
            previous['total_assets']
        )
        score = 1 if current_lt_debt_ratio < previous_lt_debt_ratio else 0
        indicators.append({
            'name': '長期負債比率下降',
            'value': f'本期: {current_lt_debt_ratio:.4f}, 前期: {previous_lt_debt_ratio:.4f}',
            'score': score
        })

        # 6. 流動比率上升
        current_ratio = safe_divide(
            current['current_assets'],
            current['current_liabilities']
        )
        previous_ratio = safe_divide(
            previous['current_assets'],
            previous['current_liabilities']
        )
        score = 1 if current_ratio > previous_ratio else 0
        indicators.append({
            'name': '流動比率上升',
            'value': f'本期: {current_ratio:.4f}, 前期: {previous_ratio:.4f}',
            'score': score
        })

        # 7. 股份未稀釋
        current_shares = current.get('weighted_average_shares', 0)
        previous_shares = previous.get('weighted_average_shares', 0)
        score = 1 if current_shares <= previous_shares else 0
        indicators.append({
            'name': '股份未稀釋',
            'value': f'本期: {current_shares:,.0f}, 前期: {previous_shares:,.0f}',
            'score': score
        })

        # 營運效率指標（2項）
        # 8. 毛利率上升
        current_gross_margin = safe_divide(
            current.get('gross_profit', 0),
            current.get('revenue', 1)
        )
        previous_gross_margin = safe_divide(
            previous.get('gross_profit', 0),
            previous.get('revenue', 1)
        )
        score = 1 if current_gross_margin > previous_gross_margin else 0
        indicators.append({
            'name': '毛利率上升',
            'value': f'本期: {current_gross_margin:.4f}, 前期: {previous_gross_margin:.4f}',
            'score': score
        })

        # 9. 資產周轉率上升
        current_turnover = safe_divide(
            current.get('revenue', 0),
            current['total_assets']
        )
        previous_turnover = safe_divide(
            previous.get('revenue', 0),
            previous['total_assets']
        )
        score = 1 if current_turnover > previous_turnover else 0
        indicators.append({
            'name': '資產周轉率上升',
            'value': f'本期: {current_turnover:.4f}, 前期: {previous_turnover:.4f}',
            'score': score
        })

        total_score = sum(ind['score'] for ind in indicators)

        return {
            'total_score': total_score,
            'indicators': indicators
        }
