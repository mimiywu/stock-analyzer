"""籌碼面分析模組（階段七）"""
from typing import Dict, List
import pandas as pd
from utils import safe_divide


class ChipAnalyzer:
    """籌碼面分析器"""

    def analyze(
        self,
        institutional_data: pd.DataFrame = None,
        margin_data: pd.DataFrame = None,
        shareholding_data: pd.DataFrame = None,
    ) -> Dict:
        """
        執行籌碼面分析

        Args:
            institutional_data: 三大法人買賣超資料
            margin_data: 融資融券資料
            shareholding_data: 股權分散資料

        Returns:
            Dict: 分析結果
        """
        result = {
            'institutional': self._analyze_institutional(institutional_data),
            'margin': self._analyze_margin(margin_data),
            'shareholding': self._analyze_shareholding(shareholding_data),
            'overall_rating': '中性',
            'details': [],
        }

        # 綜合評分
        score = 0
        max_score = 0

        # 法人評分
        inst = result['institutional']
        if inst['recent_5d_net'] > 0:
            score += 1
        elif inst['recent_5d_net'] < 0:
            score -= 1
        max_score += 1

        if inst['recent_20d_net'] > 0:
            score += 1
        elif inst['recent_20d_net'] < 0:
            score -= 1
        max_score += 1

        if inst['consecutive_buy_days'] >= 3:
            score += 1
        max_score += 1

        # 融資融券評分
        m = result['margin']
        if m['margin_trend'] == '減少':
            score += 1  # 散戶退場，籌碼穩定
        elif m['margin_trend'] == '增加':
            score -= 0.5  # 散戶加槓桿
        max_score += 1

        if m['short_ratio'] > 0.1:
            score += 0.5  # 有轧空可能
        max_score += 1

        # 股權集中度評分
        s = result['shareholding']
        if s.get('foreign_ratio', 0) > 0.3:
            score += 1  # 外資持股高
        max_score += 1

        ratio = (score + max_score) / (2 * max_score) if max_score > 0 else 0.5
        if ratio >= 0.65:
            result['overall_rating'] = '健康'
        elif ratio <= 0.35:
            result['overall_rating'] = '疑慮'
        else:
            result['overall_rating'] = '中性'

        return result

    def _analyze_institutional(self, data: pd.DataFrame) -> Dict:
        """分析三大法人買賣超"""
        result = {
            'recent_5d_net': 0,
            'recent_20d_net': 0,
            'consecutive_buy_days': 0,
            'details': [],
        }

        if data is None or data.empty:
            result['details'].append('無法人買賣超資料')
            return result

        df = data.copy()
        df = df.sort_values('date').reset_index(drop=True)

        # 只取外資和投信（自營商避險通常為反向操作）
        df_filtered = df[~df['name'].str.contains('Dealer_Hedging', na=False)].copy()

        if df_filtered.empty:
            result['details'].append('無外資/投信資料')
            return result

        # 計算買賣超（buy - sell）
        df_filtered = df_filtered.assign(
            net=df_filtered['buy'].astype(float) - df_filtered['sell'].astype(float)
        )

        # 按日期加總
        daily_net = df_filtered.groupby('date')['net'].sum()
        daily_net = daily_net.sort_index()

        # 近 5 日買賣超
        recent_5 = daily_net.tail(5).sum()
        result['recent_5d_net'] = recent_5
        result['details'].append(
            f"近 5 日法人買賣超: {recent_5:,.0f} 張"
        )

        # 近 20 日買賣超
        recent_20 = daily_net.tail(20).sum()
        result['recent_20d_net'] = recent_20
        result['details'].append(
            f"近 20 日法人買賣超: {recent_20:,.0f} 張"
        )

        # 連續買超天數
        consecutive = 0
        for val in reversed(daily_net.values):
            if val > 0:
                consecutive += 1
            else:
                break
        result['consecutive_buy_days'] = consecutive
        result['details'].append(
            f"連續買超天數: {consecutive} 天"
        )

        return result

    def _analyze_margin(self, data: pd.DataFrame) -> Dict:
        """分析融資融券"""
        result = {
            'margin_balance': 0,
            'short_balance': 0,
            'short_ratio': 0,
            'margin_trend': '穩定',
            'details': [],
        }

        if data is None or data.empty:
            result['details'].append('無融資融券資料')
            return result

        df = data.copy()
        df = df.sort_values('date').reset_index(drop=True)

        latest = df.iloc[-1]
        margin_balance = float(latest.get('MarginPurchaseTodayBalance', 0))
        short_balance = float(latest.get('ShortSaleTodayBalance', 0))

        result['margin_balance'] = margin_balance
        result['short_balance'] = short_balance

        # 券資比
        if margin_balance > 0:
            short_ratio = short_balance / margin_balance
            result['short_ratio'] = short_ratio
            result['details'].append(
                f"券資比: {short_ratio:.2%}"
            )

        result['details'].append(
            f"融資餘額: {margin_balance:,.0f} 張"
        )
        result['details'].append(
            f"融券餘額: {short_balance:,.0f} 張"
        )

        # 趨勢判斷
        if len(df) >= 5:
            recent_margin = float(
                df.tail(5)['MarginPurchaseTodayBalance'].mean()
            )
            prev_margin = float(
                df.tail(10).head(5)['MarginPurchaseTodayBalance'].mean()
            )

            if recent_margin > prev_margin * 1.1:
                result['margin_trend'] = '增加'
            elif recent_margin < prev_margin * 0.9:
                result['margin_trend'] = '減少'

        return result

    def _analyze_shareholding(self, data: pd.DataFrame) -> Dict:
        """分析股權分散"""
        result = {
            'foreign_ratio': 0,
            'total_shares': 0,
            'details': [],
        }

        if data is None or data.empty:
            result['details'].append('無股權分散資料')
            return result

        df = data.copy()
        df = df.sort_values('date').reset_index(drop=True)

        latest = df.iloc[-1]
        foreign_ratio = float(
            latest.get('ForeignInvestmentSharesRatio', 0)
        ) / 100  # 轉換為小數
        total_shares = float(latest.get('NumberOfSharesIssued', 0))

        result['foreign_ratio'] = foreign_ratio
        result['total_shares'] = total_shares
        result['details'].append(
            f"外資持股比例: {foreign_ratio:.1%}"
        )
        result['details'].append(
            f"發行股數: {total_shares:,.0f} 股"
        )

        return result
