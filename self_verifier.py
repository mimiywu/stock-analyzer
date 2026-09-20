"""自我驗證模組 - 驗證每個分析階段的計算正確性"""
from typing import Dict, List
from utils import safe_divide


class SelfVerifier:
    """自我驗證器 - 確保每個分析階段的數據和計算正確"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def reset(self):
        """重置驗證狀態"""
        self.errors = []
        self.warnings = []

    def verify_piotroski(self, data: List[Dict], result: Dict) -> Dict:
        """驗證 Piotroski F-Score 計算"""
        self.reset()

        if not data or len(data) < 2:
            self.errors.append('Piotroski: 資料不足，需要至少兩期')
            return self._result()

        current = data[0]
        previous = data[1]

        # 驗證 1: ROA 計算
        roa = safe_divide(current['net_income'], current['total_assets'])
        expected_score_1 = 1 if roa > 0 else 0
        actual_score_1 = result['indicators'][0]['score']
        if expected_score_1 != actual_score_1:
            self.errors.append(
                f'Piotroski 指標1 (ROA>0): 計算={roa:.4f}, '
                f'預期得分={expected_score_1}, 實際得分={actual_score_1}'
            )

        # 驗證 2: OCF > 0
        ocf = current.get('operating_cash_flow', 0)
        expected_score_2 = 1 if ocf > 0 else 0
        actual_score_2 = result['indicators'][1]['score']
        if expected_score_2 != actual_score_2:
            self.errors.append(
                f'Piotroski 指標2 (OCF>0): OCF={ocf:,.0f}, '
                f'預期得分={expected_score_2}, 實際得分={actual_score_2}'
            )

        # 驗證 4: OCF > NI
        ni = current['net_income']
        expected_score_4 = 1 if ocf > ni else 0
        actual_score_4 = result['indicators'][3]['score']
        if expected_score_4 != actual_score_4:
            self.errors.append(
                f'Piotroski 指標4 (OCF>NI): OCF={ocf:,.0f}, NI={ni:,.0f}, '
                f'預期得分={expected_score_4}, 實際得分={actual_score_4}'
            )

        # 驗證總分
        expected_total = sum(ind['score'] for ind in result['indicators'])
        if expected_total != result['total_score']:
            self.errors.append(
                f'Piotroski 總分: 各指標加總={expected_total}, '
                f'報告總分={result["total_score"]}'
            )

        # 合理性檢查
        if result['total_score'] > 9:
            self.errors.append(f'Piotroski 總分 {result["total_score"]} 超過最大值 9')

        return self._result()

    def verify_altman(self, data: Dict, market_cap: float, result: Dict) -> Dict:
        """驗證 Altman Z-Score 計算"""
        self.reset()

        if not data:
            self.errors.append('Altman: 無資料')
            return self._result()

        # 重新計算各因子
        working_capital = data['current_assets'] - data['current_liabilities']
        a = safe_divide(working_capital, data['total_assets'])
        b = safe_divide(data.get('retained_earnings', 0), data['total_assets'])
        ebit = data.get('operating_income', 0)
        c = safe_divide(ebit, data['total_assets'])

        market_cap_yuan = market_cap * 100000000 if market_cap else 0
        d = safe_divide(market_cap_yuan, data['total_liabilities'])
        e = safe_divide(data.get('revenue', 0), data['total_assets'])

        expected_z = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e

        # 允許 0.01 的誤差（浮點數精度）
        if abs(expected_z - result['z_score']) > 0.01:
            self.errors.append(
                f'Altman Z-Score: 重新計算={expected_z:.4f}, '
                f'報告值={result["z_score"]:.4f}, 差異={abs(expected_z - result["z_score"]):.4f}'
            )

        # 驗證區域判斷
        expected_zone = '安全區域' if expected_z > 2.99 else '灰色區域' if expected_z > 1.81 else '危險區域'
        if expected_zone != result['zone']:
            self.errors.append(
                f'Altman 區域: Z={expected_z:.4f} 應為 {expected_zone}, '
                f'報告為 {result["zone"]}'
            )

        # 合理性檢查
        if expected_z < 0:
            self.warnings.append(f'Altman Z-Score 為負值 ({expected_z:.4f})，極為異常')

        return self._result()

    def verify_dupont(self, data: List[Dict], result: Dict) -> Dict:
        """驗證杜邦分析計算"""
        self.reset()

        if not data:
            self.errors.append('DuPont: 無資料')
            return self._result()

        for i, period in enumerate(data):
            factor = result['factors'][i]

            # 重新計算三因子
            net_margin = safe_divide(period['net_income'], period['revenue'])
            asset_turnover = safe_divide(period['revenue'], period['total_assets'])
            equity_multiplier = safe_divide(period['total_assets'], period['stockholders_equity'])
            roe = net_margin * asset_turnover * equity_multiplier

            # 驗證 ROE = 淨利 / 股東權益
            roe_check = safe_divide(period['net_income'], period['stockholders_equity'])

            # 驗證三因子乘積 = ROE
            if abs(roe - roe_check) > 0.001:
                self.errors.append(
                    f'DuPont {period["period"]}: '
                    f'三因子乘積={roe:.6f}, 直接計算={roe_check:.6f}, '
                    f'差異={abs(roe - roe_check):.6f}'
                )

            # 驗證報告中的數值
            if abs(factor['roe'] - roe) > 0.001:
                self.errors.append(
                    f'DuPont {period["period"]} ROE: '
                    f'重新計算={roe:.6f}, 報告值={factor["roe"]:.6f}'
                )

        return self._result()

    def verify_cashflow(self, data: List[Dict], result: Dict) -> Dict:
        """驗證現金流量分析計算"""
        self.reset()

        if not data:
            self.errors.append('CashFlow: 無資料')
            return self._result()

        for i, period in enumerate(data):
            cf_result = result['periods'][i]

            ocf = period.get('operating_cash_flow', 0)
            ni = period.get('net_income', 0)
            capex = period.get('capex', 0)

            # 驗證現金流品質
            expected_quality = safe_divide(ocf, ni)
            if abs(expected_quality - cf_result['cash_quality_ratio']) > 0.001:
                self.errors.append(
                    f'CashFlow {period["period"]}: '
                    f'現金流品質 重新計算={expected_quality:.4f}, '
                    f'報告值={cf_result["cash_quality_ratio"]:.4f}'
                )

            # 驗證自由現金流
            expected_fcf = ocf - abs(capex)
            if abs(expected_fcf - cf_result['free_cash_flow']) > 1:
                self.errors.append(
                    f'CashFlow {period["period"]}: '
                    f'FCF 重新計算={expected_fcf:,.0f}, '
                    f'報告值={cf_result["free_cash_flow"]:,.0f}'
                )

        return self._result()

    def verify_technical(self, price_data, result: Dict) -> Dict:
        """驗證技術分析計算"""
        self.reset()

        if price_data.empty or len(price_data) < 60:
            self.warnings.append('Technical: 資料不足 60 筆，部分指標可能不準確')
            return self._result()

        import pandas as pd
        df = price_data.copy()
        df['close'] = df['close'].astype(float)
        df['Trading_Volume'] = df['Trading_Volume'].astype(float)
        df = df.sort_values('date').reset_index(drop=True)

        latest_close = df['close'].iloc[-1]

        # 驗證均線
        ma5 = df['close'].rolling(5).mean().iloc[-1]
        ma20 = df['close'].rolling(20).mean().iloc[-1]
        ma60 = df['close'].rolling(60).mean().iloc[-1]

        if abs(result['trend']['ma5'] - ma5) > 0.01:
            self.errors.append(
                f'Technical MA5: 重新計算={ma5:.2f}, 報告值={result["trend"]["ma5"]:.2f}'
            )

        # 驗證 RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        expected_rsi = rsi.iloc[-1]

        if abs(expected_rsi - result['rsi']) > 0.1:
            self.errors.append(
                f'Technical RSI: 重新計算={expected_rsi:.2f}, 報告值={result["rsi"]:.2f}'
            )

        # 驗證布林通道
        middle = df['close'].rolling(20).mean().iloc[-1]
        std = df['close'].rolling(20).std().iloc[-1]
        upper = middle + 2 * std
        lower = middle - 2 * std
        band_width = upper - lower
        expected_pct_b = (latest_close - lower) / band_width if band_width > 0 else 0.5

        if abs(expected_pct_b - result['bollinger']['percent_b']) > 0.01:
            self.errors.append(
                f'Technical %B: 重新計算={expected_pct_b:.4f}, '
                f'報告值={result["bollinger"]["percent_b"]:.4f}'
            )

        # 合理性檢查
        if result['rsi'] < 0 or result['rsi'] > 100:
            self.errors.append(f'RSI={result["rsi"]:.2f} 超出 0~100 範圍')

        if result['bollinger']['percent_b'] < -0.5 or result['bollinger']['percent_b'] > 1.5:
            self.warnings.append(
                f'%B={result["bollinger"]["percent_b"]:.4f} 異常偏離，股價可能大幅突破通道'
            )

        return self._result()

    def verify_chip(self, institutional_data, margin_data, shareholding_data, result: Dict) -> Dict:
        """驗證籌碼面分析計算"""
        self.reset()

        import pandas as pd

        # 驗證法人買賣超
        if institutional_data is not None and not institutional_data.empty:
            df = institutional_data.copy()
            df = df.sort_values('date').reset_index(drop=True)
            df_filtered = df[~df['name'].str.contains('Dealer_Hedging', na=False)].copy()

            if not df_filtered.empty:
                df_filtered = df_filtered.assign(
                    net=df_filtered['buy'].astype(float) - df_filtered['sell'].astype(float)
                )
                daily_net = df_filtered.groupby('date')['net'].sum().sort_index()

                expected_5d = daily_net.tail(5).sum()
                if abs(expected_5d - result['institutional']['recent_5d_net']) > 1:
                    self.errors.append(
                        f'Chip 近5日買賣超: 重新計算={expected_5d:,.0f}, '
                        f'報告值={result["institutional"]["recent_5d_net"]:,.0f}'
                    )

        # 驗證券資比
        if margin_data is not None and not margin_data.empty:
            df = margin_data.copy()
            df = df.sort_values('date').reset_index(drop=True)
            latest = df.iloc[-1]
            margin_bal = float(latest.get('MarginPurchaseTodayBalance', 0))
            short_bal = float(latest.get('ShortSaleTodayBalance', 0))

            if margin_bal > 0:
                expected_ratio = short_bal / margin_bal
                if abs(expected_ratio - result['margin']['short_ratio']) > 0.001:
                    self.errors.append(
                        f'Chip 券資比: 重新計算={expected_ratio:.4f}, '
                        f'報告值={result["margin"]["short_ratio"]:.4f}'
                    )

        return self._result()

    def _result(self) -> Dict:
        """返回驗證結果"""
        return {
            'passed': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
        }
