"""Altman Z-Score 分析模組"""
from typing import Dict
from utils import safe_divide


class AltmanZScoreAnalyzer:
    """Altman Z-Score 分析器"""

    def analyze(self, data: Dict, market_cap: float = None) -> Dict:
        """
        執行 Altman Z-Score 分析

        Args:
            data: 標準化財務數據
            market_cap: 市值（億元）

        Returns:
            Dict: 包含 z_score, zone, factors
        """
        if not data:
            return {
                'z_score': 0,
                'zone': '無法評估',
                'factors': [],
                'error': '無資料'
            }

        factors = []

        # A項：營運資本/總資產
        working_capital = data['current_assets'] - data['current_liabilities']
        a = safe_divide(working_capital, data['total_assets'])
        weighted_a = 1.2 * a
        factors.append({
            'name': 'A: 營運資本/總資產',
            'value': f'{a:.4f}',
            'weighted': f'{weighted_a:.4f}'
        })

        # B項：保留盈餘/總資產
        b = safe_divide(data.get('retained_earnings', 0), data['total_assets'])
        weighted_b = 1.4 * b
        factors.append({
            'name': 'B: 保留盈餘/總資產',
            'value': f'{b:.4f}',
            'weighted': f'{weighted_b:.4f}'
        })

        # C項：EBIT/總資產
        # EBIT = 營業利益 + 利息費用
        # 如果沒有利息費用，使用營業利益
        ebit = data.get('operating_income', 0)
        c = safe_divide(ebit, data['total_assets'])
        weighted_c = 3.3 * c
        factors.append({
            'name': 'C: EBIT/總資產',
            'value': f'{c:.4f}',
            'weighted': f'{weighted_c:.4f}'
        })

        # D項：市值/總負債
        # 注意：market_cap 單位是「億元」，需要轉換為「元」
        if market_cap and market_cap > 0:
            market_cap_yuan = market_cap * 100000000  # 轉換為元
            d = safe_divide(market_cap_yuan, data['total_liabilities'])
        else:
            # 如果沒有市值，使用股東權益代替
            d = safe_divide(data['stockholders_equity'], data['total_liabilities'])
        weighted_d = 0.6 * d
        factors.append({
            'name': 'D: 市值/總負債',
            'value': f'{d:.4f}',
            'weighted': f'{weighted_d:.4f}'
        })

        # E項：營收/總資產
        e = safe_divide(data.get('revenue', 0), data['total_assets'])
        weighted_e = 1.0 * e
        factors.append({
            'name': 'E: 營收/總資產',
            'value': f'{e:.4f}',
            'weighted': f'{weighted_e:.4f}'
        })

        # 計算 Z-Score
        z_score = weighted_a + weighted_b + weighted_c + weighted_d + weighted_e

        # 判斷區域
        if z_score > 2.99:
            zone = '安全區域'
        elif z_score > 1.81:
            zone = '灰色區域'
        else:
            zone = '危險區域'

        return {
            'z_score': z_score,
            'zone': zone,
            'factors': factors
        }
