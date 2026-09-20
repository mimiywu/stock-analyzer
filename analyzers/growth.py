"""質化與成長性分析模組（階段五）"""
from typing import Dict, List, Optional
import pandas as pd
from utils import safe_divide


class GrowthAnalyzer:
    """質化與成長性分析器"""

    def analyze(
        self,
        financial_data: List[Dict],
        revenue_data: Optional[pd.DataFrame] = None,
        dividend_data: Optional[pd.DataFrame] = None,
        per_pbr_data: Optional[Dict] = None,
    ) -> Dict:
        """
        執行質化與成長性分析

        Args:
            financial_data: 標準化財務數據列表
            revenue_data: 月營收 DataFrame
            dividend_data: 股利 DataFrame
            per_pbr_data: PER/PBR dict（最新一筆）

        Returns:
            Dict: 分析結果
        """
        result = {
            'growth': self._analyze_growth(financial_data, revenue_data),
            'dividend': self._analyze_dividend(dividend_data),
            'valuation': self._analyze_valuation(per_pbr_data),
            'overall_rating': '中性',
            'details': [],
        }

        # 綜合評分
        score = 0
        max_score = 0

        # 成長性評分
        g = result['growth']
        if g['revenue_yoy'] > 0.1:
            score += 2
        elif g['revenue_yoy'] > 0:
            score += 1
        max_score += 2

        if g['eps_yoy'] > 0.1:
            score += 2
        elif g['eps_yoy'] > 0:
            score += 1
        max_score += 2

        if g['growth_trend'] == '加速成長':
            score += 1
        elif g['growth_trend'] == '穩定成長':
            score += 0.5
        max_score += 1

        # 股利評分
        d = result['dividend']
        if d['consecutive_years'] >= 5:
            score += 1
        elif d['consecutive_years'] >= 3:
            score += 0.5
        max_score += 1

        if d['yield'] > 0.03:
            score += 1
        elif d['yield'] > 0.01:
            score += 0.5
        max_score += 1

        # 估值評分
        v = result['valuation']
        if v['per'] > 0 and v['per'] < 20:
            score += 1
        elif v['per'] > 0 and v['per'] < 30:
            score += 0.5
        max_score += 1

        ratio = score / max_score if max_score > 0 else 0
        if ratio >= 0.7:
            result['overall_rating'] = '正面'
        elif ratio >= 0.4:
            result['overall_rating'] = '中性'
        else:
            result['overall_rating'] = '負面'

        return result

    def _analyze_growth(
        self, financial_data: List[Dict], revenue_data: Optional[pd.DataFrame] = None
    ) -> Dict:
        """分析成長趨勢"""
        result = {
            'revenue_yoy': 0,
            'eps_yoy': 0,
            'growth_trend': '無法判斷',
            'details': [],
        }

        # 從財務數據計算 EPS 年增率
        if len(financial_data) >= 2:
            current = financial_data[0]
            previous = financial_data[1]

            current_eps = current.get('net_income', 0)
            previous_eps = previous.get('net_income', 0)

            if previous_eps > 0:
                eps_yoy = (current_eps - previous_eps) / previous_eps
                result['eps_yoy'] = eps_yoy
                result['details'].append(
                    f"EPS 年增率: {eps_yoy:.1%}"
                )

            current_rev = current.get('revenue', 0)
            previous_rev = previous.get('revenue', 0)
            if previous_rev > 0:
                rev_yoy = (current_rev - previous_rev) / previous_rev
                result['revenue_yoy'] = rev_yoy
                result['details'].append(
                    f"營收年增率: {rev_yoy:.1%}"
                )

        # 從月營收 DataFrame 計算更精確的成長率
        if revenue_data is not None and not revenue_data.empty:
            # 按月排序（最新在前）
            df = revenue_data.sort_values('date', ascending=False).reset_index(drop=True)

            if len(df) >= 13:
                # 取最近 12 個月與前 12 個月比較
                recent_12 = df['revenue'].iloc[:12].sum()
                prev_12 = df['revenue'].iloc[12:24].sum() if len(df) >= 24 else 0

                if prev_12 > 0:
                    rolling_yoy = (recent_12 - prev_12) / prev_12
                    result['revenue_yoy'] = rolling_yoy
                    result['details'].append(
                        f"滾動 12 個月營收年增率: {rolling_yoy:.1%}"
                    )

            # 判斷趨勢：近 3 月均營收 vs 前 3 月均營收
            if len(df) >= 6:
                recent_avg = df['revenue'].iloc[:3].mean()
                prev_avg = df['revenue'].iloc[3:6].mean()

                if recent_avg > prev_avg * 1.05:
                    result['growth_trend'] = '加速成長'
                elif recent_avg > prev_avg:
                    result['growth_trend'] = '穩定成長'
                elif recent_avg > prev_avg * 0.95:
                    result['growth_trend'] = '趨緩'
                else:
                    result['growth_trend'] = '衰退'

        return result

    def _analyze_dividend(self, dividend_data: Optional[pd.DataFrame] = None) -> Dict:
        """分析股利政策"""
        result = {
            'yield': 0,
            'consecutive_years': 0,
            'payout_ratio': 0,
            'recent_dividends': [],
            'details': [],
        }

        if dividend_data is None or dividend_data.empty:
            result['details'].append('無股利資料')
            return result

        # 按日期排序（最新在前）
        df = dividend_data.sort_values('date', ascending=False).reset_index(drop=True)

        # 計算連續配息年數
        consecutive = 0
        for _, row in df.iterrows():
            cash_div = row.get('CashEarningsDistribution', 0)
            if cash_div and cash_div > 0:
                consecutive += 1
            else:
                break
        result['consecutive_years'] = consecutive
        result['details'].append(
            f"連續配息年數: {consecutive} 年"
        )

        # 最近一次現金股利
        latest = df.iloc[0]
        cash_div = latest.get('CashEarningsDistribution', 0)
        result['recent_dividends'].append({
            'year': latest.get('year', ''),
            'cash_dividend': cash_div,
        })
        result['details'].append(
            f"最近現金股利: {cash_div:.2f} 元"
        )

        # 殖利率（從 per_pbr_data 取得，這裡先設 0）
        result['yield'] = 0

        return result

    def _analyze_valuation(self, per_pbr_data: Optional[Dict] = None) -> Dict:
        """分析估值"""
        result = {
            'per': 0,
            'pbr': 0,
            'dividend_yield': 0,
            'details': [],
        }

        if not per_pbr_data:
            result['details'].append('無估值資料')
            return result

        result['per'] = per_pbr_data.get('PER', 0)
        result['pbr'] = per_pbr_data.get('PBR', 0)
        result['dividend_yield'] = per_pbr_data.get('dividend_yield', 0)

        result['details'].append(f"本益比 (PER): {result['per']:.2f}")
        result['details'].append(f"股價淨值比 (PBR): {result['pbr']:.2f}")
        result['details'].append(
            f"殖利率: {result['dividend_yield']:.2f}%"
        )

        return result
