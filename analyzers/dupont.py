"""杜邦分析模組"""
from typing import Dict, List
from utils import safe_divide


class DuPontAnalyzer:
    """杜邦分析器"""

    def analyze(self, data: List[Dict]) -> Dict:
        """
        執行杜邦分析（三年趨勢）

        Args:
            data: 標準化財務數據列表（按時間排序）

        Returns:
            Dict: 包含 factors, trend, analysis
        """
        if not data:
            return None

        results = []

        for period in data:
            # 計算三因子
            net_margin = safe_divide(
                period['net_income'],
                period['revenue']
            )

            asset_turnover = safe_divide(
                period['revenue'],
                period['total_assets']
            )

            equity_multiplier = safe_divide(
                period['total_assets'],
                period['stockholders_equity']
            )

            # 計算 ROE
            roe = net_margin * asset_turnover * equity_multiplier

            # 驗證：ROE = 淨利 / 股東權益
            roe_check = safe_divide(
                period['net_income'],
                period['stockholders_equity']
            )

            results.append({
                'period': period.get('period', ''),
                'net_margin': net_margin,
                'asset_turnover': asset_turnover,
                'equity_multiplier': equity_multiplier,
                'roe': roe,
                'roe_check': roe_check
            })

        # 分析趨勢
        analysis = self._analyze_trend(results)

        return {
            'factors': results,
            'analysis': analysis
        }

    def _analyze_trend(self, results: List[Dict]) -> Dict:
        """分析趨勢"""
        if len(results) < 2:
            return {'message': '資料不足，無法分析趨勢'}

        latest = results[0]
        previous = results[1]

        # 計算變化
        roe_change = latest['roe'] - previous['roe']
        margin_change = latest['net_margin'] - previous['net_margin']
        turnover_change = latest['asset_turnover'] - previous['asset_turnover']
        leverage_change = latest['equity_multiplier'] - previous['equity_multiplier']

        # 識別主要驅動因子
        drivers = []
        if abs(margin_change) > abs(turnover_change) and abs(margin_change) > abs(leverage_change):
            drivers.append('淨利率')
        if abs(turnover_change) > abs(margin_change) and abs(turnover_change) > abs(leverage_change):
            drivers.append('資產周轉率')
        if abs(leverage_change) > abs(margin_change) and abs(leverage_change) > abs(turnover_change):
            drivers.append('財務槓桿')

        # 評估槓桿水準
        leverage_level = '合理'
        if latest['equity_multiplier'] > 3:
            leverage_level = '偏高'
        elif latest['equity_multiplier'] < 1.5:
            leverage_level = '保守'

        return {
            'roe_change': roe_change,
            'margin_change': margin_change,
            'turnover_change': turnover_change,
            'leverage_change': leverage_change,
            'main_drivers': drivers if drivers else ['各因子變化相近'],
            'leverage_assessment': leverage_level
        }
