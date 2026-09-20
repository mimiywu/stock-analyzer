"""估值分析模組 - 判斷股價便宜還是貴"""
from typing import Dict, List, Optional
import pandas as pd
from utils import safe_divide


# 產業合理 PE 區間參考
INDUSTRY_PE_RANGES = {
    '半導體': {'low': 15, 'mid': 25, 'high': 40},
    '記憶體': {'low': 5, 'mid': 12, 'high': 20},
    '傳產': {'low': 8, 'mid': 12, 'high': 15},
    '銀行': {'low': 8, 'mid': 10, 'high': 12},
    '金融': {'low': 8, 'mid': 12, 'high': 15},
    'AI/軟體': {'low': 20, 'mid': 35, 'high': 50},
    '電子零組件': {'low': 10, 'mid': 18, 'high': 25},
    '光電': {'low': 8, 'mid': 15, 'high': 25},
    '生技': {'low': 15, 'mid': 25, 'high': 40},
    '食品': {'low': 12, 'mid': 18, 'high': 25},
    '塑化': {'low': 8, 'mid': 12, 'high': 18},
    '鋼鐵': {'low': 5, 'mid': 10, 'high': 15},
    '航運': {'low': 3, 'mid': 8, 'high': 15},
    '營建': {'low': 5, 'mid': 10, 'high': 15},
    '電信': {'low': 10, 'mid': 15, 'high': 20},
}

# 同業對照表（主要台股）
PEER_COMPARISON = {
    '2330': {'name': '台積電', 'industry': '半導體', 'peers': ['2303', '2454', '3034', '6770']},
    '2408': {'name': '南亞科', 'industry': '記憶體', 'peers': ['2434', '2408', '2492', '2474']},
    '2454': {'name': '聯發科', 'industry': '半導體', 'peers': ['2330', '2303', '3034', '6770']},
    '2303': {'name': '聯電', 'industry': '半導體', 'peers': ['2330', '2454', '3034', '6770']},
    '2881': {'name': '富邦金', 'industry': '金融', 'peers': ['2882', '2883', '2884', '2886']},
    '2882': {'name': '國泰金', 'industry': '金融', 'peers': ['2881', '2883', '2884', '2886']},
    '1301': {'name': '台塑', 'industry': '塑化', 'peers': ['1302', '1303', '1304']},
    '2603': {'name': '長榮', 'industry': '航運', 'peers': ['2609', '2615', '2603']},
}


class ValuationAnalyzer:
    """估值分析器"""

    def analyze(
        self,
        stock_id: str,
        current_price: float,
        per_pbr_history: pd.DataFrame = None,
        financial_data: List[Dict] = None,
        growth_result: Dict = None,
    ) -> Dict:
        """
        執行完整估值分析

        Returns:
            Dict: 包含各層次估值結果與綜合判斷
        """
        result = {
            'current_pe': 0,
            'current_pb': 0,
            'peg': 0,
            'historical_analysis': self._analyze_historical(per_pbr_history),
            'industry_analysis': self._analyze_industry(stock_id),
            'peg_analysis': self._analyze_peg(growth_result),
            'dcf_analysis': self._analyze_dcf(financial_data, current_price),
            'five_second_check': {},
            'overall_verdict': '無法判斷',
            'verdict_color': 'gray',
            'details': [],
        }

        # 取得目前 PE/PB
        if per_pbr_history is not None and not per_pbr_history.empty:
            latest = per_pbr_history.iloc[-1]
            result['current_pe'] = float(latest.get('PER', 0))
            result['current_pb'] = float(latest.get('PBR', 0))

        # 五秒判斷法
        result['five_second_check'] = self._five_second_check(result)

        # 綜合判斷
        result['overall_verdict'], result['verdict_color'] = self._make_verdict(result)

        return result

    def _analyze_historical(self, per_pbr_history: pd.DataFrame = None) -> Dict:
        """層次一：和自己歷史比"""
        result = {
            'pe_percentile': 0,
            'pb_percentile': 0,
            'pe_status': '無法判斷',
            'pb_status': '無法判斷',
            'pe_min': 0, 'pe_avg': 0, 'pe_max': 0,
            'pb_min': 0, 'pb_avg': 0, 'pb_max': 0,
            'details': [],
        }

        if per_pbr_history is None or per_pbr_history.empty:
            result['details'].append('無歷史 PE/PB 資料')
            return result

        pe_series = per_pbr_history['PER'].astype(float)
        pb_series = per_pbr_history['PBR'].astype(float)

        # PE 歷史區間
        pe_min = pe_series.min()
        pe_avg = pe_series.mean()
        pe_max = pe_series.max()
        pe_current = pe_series.iloc[-1]

        result['pe_min'] = pe_min
        result['pe_avg'] = pe_avg
        result['pe_max'] = pe_max

        # PE 百分位
        pe_percentile = (pe_series < pe_current).sum() / len(pe_series) * 100
        result['pe_percentile'] = pe_percentile

        if pe_percentile < 30:
            result['pe_status'] = '偏便宜'
        elif pe_percentile < 70:
            result['pe_status'] = '合理'
        else:
            result['pe_status'] = '偏貴'

        result['details'].append(
            f"PE 歷史區間: {pe_min:.1f} ~ {pe_max:.1f}，平均 {pe_avg:.1f}，"
            f"目前 {pe_current:.1f}（百分位 {pe_percentile:.0f}%）"
        )

        # PB 歷史區間
        pb_min = pb_series.min()
        pb_avg = pb_series.mean()
        pb_max = pb_series.max()
        pb_current = pb_series.iloc[-1]

        result['pb_min'] = pb_min
        result['pb_avg'] = pb_avg
        result['pb_max'] = pb_max

        pb_percentile = (pb_series < pb_current).sum() / len(pb_series) * 100
        result['pb_percentile'] = pb_percentile

        if pb_percentile < 30:
            result['pb_status'] = '偏便宜'
        elif pb_percentile < 70:
            result['pb_status'] = '合理'
        else:
            result['pb_status'] = '偏貴'

        result['details'].append(
            f"PB 歷史區間: {pb_min:.2f} ~ {pb_max:.2f}，平均 {pb_avg:.2f}，"
            f"目前 {pb_current:.2f}（百分位 {pb_percentile:.0f}%）"
        )

        return result

    def _analyze_industry(self, stock_id: str) -> Dict:
        """層次二：和同業比"""
        result = {
            'industry': '未知',
            'industry_pe_range': {},
            'stock_pe_vs_industry': '無法比較',
            'details': [],
        }

        stock_info = PEER_COMPARISON.get(stock_id, {})
        industry = stock_info.get('industry', '未知')
        result['industry'] = industry

        if industry in INDUSTRY_PE_RANGES:
            pe_range = INDUSTRY_PE_RANGES[industry]
            result['industry_pe_range'] = pe_range
            result['details'].append(
                f"{industry}產業合理 PE 區間: {pe_range['low']}~{pe_range['high']}倍，"
                f"中位數 {pe_range['mid']}倍"
            )

        return result

    def _analyze_peg(self, growth_result: Dict = None) -> Dict:
        """層次三：和成長比（PEG）"""
        result = {
            'peg': 0,
            'peg_status': '無法判斷',
            'details': [],
        }

        if not growth_result:
            result['details'].append('無成長資料，無法計算 PEG')
            return result

        current_pe = 0
        # 從 valuation 取得 PE
        if 'valuation' in growth_result:
            current_pe = growth_result['valuation'].get('per', 0)

        # 從 growth 取得成長率
        growth_rate = growth_result.get('growth', {}).get('eps_yoy', 0) * 100  # 轉為百分比

        if current_pe > 0 and growth_rate > 0:
            peg = current_pe / growth_rate
            result['peg'] = peg

            if peg < 1:
                result['peg_status'] = '偏便宜（成長速度快於估值）'
            elif peg < 1.5:
                result['peg_status'] = '合理'
            elif peg < 2:
                result['peg_status'] = '偏高'
            else:
                result['peg_status'] = '偏貴（估值超過成長速度）'

            result['details'].append(
                f"PEG = PE({current_pe:.1f}) / 成長率({growth_rate:.1f}%) = {peg:.2f} → {result['peg_status']}"
            )
        else:
            result['details'].append(f"PE={current_pe:.1f}, 成長率={growth_rate:.1f}%，無法計算 PEG")

        return result

    def _analyze_dcf(self, financial_data: List[Dict] = None, current_price: float = 0) -> Dict:
        """層次四：簡化 DCF（現金流折現）"""
        result = {
            'intrinsic_value': 0,
            'upside': 0,
            'dcf_status': '無法判斷',
            'details': [],
        }

        if not financial_data or len(financial_data) < 1:
            result['details'].append('無財務資料，無法計算 DCF')
            return result

        # 使用最近一期自由現金流
        latest = financial_data[0]
        fcf = latest.get('operating_cash_flow', 0) - abs(latest.get('capex', 0))

        if fcf <= 0:
            result['details'].append(f'自由現金流為負（{fcf:,.0f}），不適用 DCF')
            result['dcf_status'] = '不適用'
            return result

        # 簡化 DCF：假設 10 年成長期 + 終值
        growth_rate = 0.05  # 假設 5% 長期成長率
        discount_rate = 0.10  # 折現率 10%
        terminal_growth = 0.02  # 終值成長率 2%
        years = 10

        # 估算股數（從 total_assets 和 stockholders_equity 推算）
        # 這裡用簡化方式：假設每股淨值約 100 元
        equity = latest.get('stockholders_equity', 0)
        if equity > 0 and current_price > 0:
            # 用市值/股價估算股數（但我們沒有市值）
            # 改用 PB 反推：假設 PB = 1.5
            estimated_shares = equity / (current_price / 1.5) if current_price > 0 else 1000000000
        else:
            estimated_shares = 1000000000

        # 計算 DCF
        total_pv = 0
        current_fcf = fcf
        for year in range(1, years + 1):
            current_fcf = current_fcf * (1 + growth_rate)
            pv = current_fcf / (1 + discount_rate) ** year
            total_pv += pv

        # 終值
        terminal_value = current_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
        terminal_pv = terminal_value / (1 + discount_rate) ** years
        total_pv += terminal_pv

        # 每股內在價值
        intrinsic_value = total_pv / estimated_shares if estimated_shares > 0 else 0
        result['intrinsic_value'] = intrinsic_value

        if current_price > 0 and intrinsic_value > 0:
            upside = (intrinsic_value - current_price) / current_price * 100
            result['upside'] = upside

            if upside > 20:
                result['dcf_status'] = f'偏便宜（內在價值 {intrinsic_value:.1f} 元，上漲空間 {upside:.1f}%）'
            elif upside > 0:
                result['dcf_status'] = f'合理（內在價值 {intrinsic_value:.1f} 元，上漲空間 {upside:.1f}%）'
            elif upside > -20:
                result['dcf_status'] = f'偏高（內在價值 {intrinsic_value:.1f} 元，下跌空間 {abs(upside):.1f}%）'
            else:
                result['dcf_status'] = f'偏貴（內在價值 {intrinsic_value:.1f} 元，下跌空間 {abs(upside):.1f}%）'

            result['details'].append(result['dcf_status'])

        return result

    def _five_second_check(self, result: Dict) -> Dict:
        """五秒判斷法"""
        check = {
            'pe_pb': '',
            'vs_history': '',
            'vs_industry': '',
            'growth_outlook': '',
            'stock_type': '',
            'score': 0,
        }

        # ① 現在 PE、PB 是多少？
        pe = result['current_pe']
        pb = result['current_pb']
        check['pe_pb'] = f'PE={pe:.1f}, PB={pb:.2f}'

        # ② 和過去五年比
        hist = result.get('historical_analysis', {})
        pe_status = hist.get('pe_status', '無法判斷')
        check['vs_history'] = f'PE 歷史比較: {pe_status}'

        # ③ 和同業比
        industry = result.get('industry_analysis', {}).get('industry', '未知')
        pe_range = result.get('industry_analysis', {}).get('industry_pe_range', {})
        if pe_range and pe > 0:
            if pe < pe_range.get('low', 999):
                check['vs_industry'] = f'{industry}產業 PE 低於同業（產業區間 {pe_range["low"]}-{pe_range["high"]}）'
            elif pe > pe_range.get('high', 0):
                check['vs_industry'] = f'{industry}產業 PE 高於同業（產業區間 {pe_range["low"]}-{pe_range["high"]}）'
            else:
                check['vs_industry'] = f'{industry}產業 PE 在同業區間內（{pe_range["low"]}-{pe_range["high"]}）'
        else:
            check['vs_industry'] = f'{industry}產業（無同業比較資料）'

        # ④ 未來獲利是成長還是衰退？
        peg = result.get('peg_analysis', {})
        check['growth_outlook'] = f'PEG={peg.get("peg", 0):.2f} → {peg.get("peg_status", "無法判斷")}'

        #  這是成長股還是循環股？
        if industry in ['記憶體', '鋼鐵', '航運', '塑化']:
            check['stock_type'] = f'{industry}（景氣循環股，注意景氣位置）'
        elif industry in ['AI/軟體', '生技', '半導體']:
            check['stock_type'] = f'{industry}（成長股，重視 PEG）'
        else:
            check['stock_type'] = f'{industry}（穩健型）'

        # 綜合評分（-2 到 +2）
        score = 0
        if pe_status == '偏便宜':
            score += 1
        elif pe_status == '偏貴':
            score -= 1

        peg_val = peg.get('peg', 0)
        if 0 < peg_val < 1:
            score += 1
        elif peg_val > 2:
            score -= 1

        if pe_range and pe > 0:
            if pe < pe_range.get('low', 999):
                score += 1
            elif pe > pe_range.get('high', 0):
                score -= 1

        dcf = result.get('dcf_analysis', {})
        if dcf.get('upside', 0) > 20:
            score += 1
        elif dcf.get('upside', 0) < -20:
            score -= 1

        check['score'] = score
        return check

    def _make_verdict(self, result: Dict) -> tuple:
        """綜合判斷：便宜/合理/貴"""
        score = result['five_second_check'].get('score', 0)

        if score >= 2:
            return '明顯偏便宜', 'green'
        elif score >= 1:
            return '偏便宜', 'green'
        elif score >= 0:
            return '合理', 'blue'
        elif score >= -1:
            return '偏高', 'orange'
        else:
            return '偏貴', 'red'
