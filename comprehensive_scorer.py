"""綜合評分模組 - 七階段評分與綜合評估"""
from typing import Dict, List


class ComprehensiveScorer:
    """綜合評分器"""

    def calculate_stage_scores(self, piotroski, altman, dupont, cashflow,
                               growth, technical, chip) -> Dict:
        """
        計算每個階段的分數（0-100 分制）

        Returns:
            Dict: 各階段分數與評價
        """
        scores = {}

        # 階段一：Piotroski F-Score（滿分 9 分 → 0-100 分）
        p_score = piotroski['total_score']
        scores['piotroski'] = {
            'raw_score': f"{p_score}/9",
            'normalized_score': (p_score / 9) * 100,
            'rating': '優秀' if p_score >= 7 else '良好' if p_score >= 5 else '一般',
            'weight': 0.15,  # 權重 15%
        }

        # 階段二：Altman Z-Score
        z = altman['z_score']
        if z > 2.99:
            z_score_normalized = 100
        elif z > 1.81:
            z_score_normalized = 50 + (z - 1.81) / (2.99 - 1.81) * 50
        else:
            z_score_normalized = max(0, z / 1.81 * 50)

        scores['altman'] = {
            'raw_score': f"{z:.2f}",
            'normalized_score': z_score_normalized,
            'rating': altman['zone'],
            'weight': 0.15,
        }

        # 階段三：杜邦分析 ROE
        roe = dupont['factors'][0]['roe']
        roe_score = min(100, (roe / 0.20) * 100)  # 20% ROE = 100 分

        scores['dupont'] = {
            'raw_score': f"{roe:.2%}",
            'normalized_score': roe_score,
            'rating': '卓越' if roe > 0.20 else '良好' if roe > 0.10 else '一般',
            'weight': 0.15,
        }

        # 階段四：現金流量分析
        cf_quality = cashflow['assessment']['latest_quality']
        cf_score = min(100, (cf_quality / 1.5) * 100)  # 1.5 = 100 分

        scores['cashflow'] = {
            'raw_score': f"{cf_quality:.2f}",
            'normalized_score': cf_score,
            'rating': cashflow['assessment']['quality_rating'],
            'weight': 0.10,
        }

        # 階段五：質化與成長性
        g_rating = growth['overall_rating']
        g_score = 80 if g_rating == '正面' else 50 if g_rating == '中性' else 20

        scores['growth'] = {
            'raw_score': f"YoY {growth['growth']['revenue_yoy']:.1%}",
            'normalized_score': g_score,
            'rating': g_rating,
            'weight': 0.15,
        }

        # 階段六：技術分析
        t_rating = technical['overall_rating']
        t_score = 80 if t_rating == '多頭' else 50 if t_rating == '中性' else 20

        scores['technical'] = {
            'raw_score': technical['trend']['ma_alignment'],
            'normalized_score': t_score,
            'rating': t_rating,
            'weight': 0.15,
        }

        # 階段七：籌碼面分析
        c_rating = chip['overall_rating']
        c_score = 80 if c_rating == '健康' else 50 if c_rating == '中性' else 20

        scores['chip'] = {
            'raw_score': f"{chip['institutional']['recent_5d_net']:,.0f}",
            'normalized_score': c_score,
            'rating': c_rating,
            'weight': 0.15,
        }

        return scores

    def calculate_comprehensive_score(self, scores: Dict) -> Dict:
        """
        計算綜合評分（加權平均）

        Returns:
            Dict: 綜合評分與建議
        """
        total_score = 0
        total_weight = 0

        for stage, data in scores.items():
            total_score += data['normalized_score'] * data['weight']
            total_weight += data['weight']

        final_score = total_score / total_weight if total_weight > 0 else 0

        # 綜合評價
        if final_score >= 80:
            overall_rating = '強烈買進'
            recommendation = '基本面、技術面、籌碼面皆佳，建議積極布局'
        elif final_score >= 65:
            overall_rating = '買進'
            recommendation = '整體表現良好，可考慮分批進場'
        elif final_score >= 50:
            overall_rating = '持有'
            recommendation = '表現中等，已持有者續抱，未持有者觀望'
        elif final_score >= 35:
            overall_rating = '減碼'
            recommendation = '部分指標轉弱，建議減碼或停損'
        else:
            overall_rating = '賣出'
            recommendation = '多項指標不佳，建議出場觀望'

        # 投資價值 vs 買賣時機
        fundamental_score = (
            scores['piotroski']['normalized_score'] * 0.25 +
            scores['altman']['normalized_score'] * 0.20 +
            scores['dupont']['normalized_score'] * 0.20 +
            scores['cashflow']['normalized_score'] * 0.15 +
            scores['growth']['normalized_score'] * 0.20
        )

        timing_score = (
            scores['technical']['normalized_score'] * 0.50 +
            scores['chip']['normalized_score'] * 0.50
        )

        return {
            'final_score': final_score,
            'overall_rating': overall_rating,
            'recommendation': recommendation,
            'fundamental_score': fundamental_score,
            'timing_score': timing_score,
            'stage_scores': scores,
        }

    def generate_investment_advice(self, comprehensive: Dict, scores: Dict,
                                   technical_result: Dict = None,
                                   chip_result: Dict = None,
                                   current_price: float = None) -> Dict:
        """
        生成投資建議（包含明確信號、短中長線建議買入價）

        Returns:
            Dict: 包含優勢、風險、建議、等待信號、買入價建議
        """
        strengths = []
        risks = []
        suggestions = []
        waiting_signals = []
        buy_recommendations = {}

        # 基本面優勢
        if scores['piotroski']['normalized_score'] >= 70:
            strengths.append('Piotroski F-Score 優秀，獲利能力強')
        elif scores['piotroski']['normalized_score'] < 40:
            risks.append('Piotroski F-Score 偏低，獲利能力需關注')

        if scores['altman']['rating'] == '安全區域':
            strengths.append('Altman Z-Score 安全，財務風險低')
        elif scores['altman']['rating'] == '危險區域':
            risks.append('Altman Z-Score 危險，破產風險高')

        if scores['dupont']['normalized_score'] >= 70:
            strengths.append('ROE 表現優異，股東報酬佳')

        if scores['cashflow']['normalized_score'] >= 80:
            strengths.append('現金流品質優秀，營運健康')

        if scores['growth']['rating'] == '正面':
            strengths.append('營收成長強勁，前景看好')
        elif scores['growth']['rating'] == '負面':
            risks.append('營收衰退，成長動能不足')

        # 技術面判斷
        if technical_result:
            t_rating = scores['technical']['rating']
            if t_rating == '多頭':
                strengths.append('技術面多頭排列，趨勢向上')
                suggestions.append('技術面支持進場')
            elif t_rating == '空頭':
                risks.append('技術面空頭排列，趨勢向下')
                suggestions.append('建議等待技術面轉多')
            else:
                # 中性 - 列出需要等待的信號
                t = technical_result.get('trend', {})
                m = technical_result.get('macd', {})
                rsi = technical_result.get('rsi', 50)
                k = technical_result.get('kd', {})
                b = technical_result.get('bollinger', {})

                if t.get('ma_alignment') == '盤整':
                    waiting_signals.append('等待均線形成多頭排列（MA5 > MA20 > MA60）')
                elif t.get('ma_alignment') == '空頭排列':
                    waiting_signals.append('等待均線翻多（MA5 突破 MA20）')

                if m.get('signal') == '死亡交叉':
                    waiting_signals.append('等待 MACD 黃金交叉（DIF 突破 MACD 線）')
                elif m.get('signal') == '柱狀收斂/空頭':
                    waiting_signals.append('等待 MACD 柱狀圖翻紅')

                if rsi < 30:
                    waiting_signals.append('RSI 已超賣，可考慮分批布局')
                elif rsi > 70:
                    waiting_signals.append('RSI 超買，等待回檔至 50 以下')
                else:
                    waiting_signals.append(f'等待 RSI 突破 60 確認多頭動能（目前 {rsi:.1f}）')

                if k.get('signal') == '死亡交叉':
                    waiting_signals.append('等待 KD 低檔黃金交叉（K 值 < 30 時 K 突破 D）')
                elif k.get('signal') == '無明顯信號':
                    waiting_signals.append('等待 KD 明確交叉信號')

                if b:
                    pct_b = b.get('percent_b', 0.5)
                    if pct_b < 0:
                        waiting_signals.append('股價跌破布林下軌，等待反彈回通道內')
                    elif pct_b > 1:
                        waiting_signals.append('股價突破布林上軌，等待回測中軌支撐')
                    else:
                        waiting_signals.append(f'等待股價突破布林上軌（%B={pct_b:.2f}）')

                vol = technical_result.get('volume_analysis', {})
                if vol.get('pattern') == '價漲量縮':
                    waiting_signals.append('等待價漲量增確認上漲動能')

        # 籌碼面判斷
        if chip_result:
            c_rating = scores['chip']['rating']
            if c_rating == '健康':
                strengths.append('籌碼面健康，法人持續買超')
            elif c_rating == '疑慮':
                risks.append('籌碼面有疑慮，法人持續賣超')
                waiting_signals.append('等待法人轉為買超')

            inst = chip_result.get('institutional', {})
            if inst.get('recent_5d_net', 0) < 0:
                waiting_signals.append('等待近 5 日法人買賣超轉正')
            if inst.get('consecutive_buy_days', 0) < 3:
                waiting_signals.append('等待法人連續買超 3 天以上')

            margin = chip_result.get('margin', {})
            if margin.get('margin_trend') == '增加':
                waiting_signals.append('等待融資餘額減少（散戶退場）')

        # 計算建議買入價
        if current_price and technical_result:
            t = technical_result.get('trend', {})
            b = technical_result.get('bollinger', {})

            ma5 = t.get('ma5', current_price)
            ma20 = t.get('ma20', current_price)
            ma60 = t.get('ma60', current_price)
            lower_band = b.get('lower_band', current_price * 0.95) if b else current_price * 0.95
            middle_band = b.get('middle_band', current_price) if b else current_price

            # 短線買入價（1-2 週）：技術面支撐位
            short_term_price = min(ma5, middle_band)
            short_term_reason = f"短線支撐：MA5({ma5:.1f}) 與布林中軌({middle_band:.1f}) 附近"

            # 中線買入價（1-3 個月）：均線支撐 + 籌碼面
            mid_term_price = min(ma20, lower_band)
            mid_term_reason = f"中線支撐：MA20({ma20:.1f}) 與布林下軌({lower_band:.1f}) 附近"

            # 長線買入價（3-12 個月）：基本面價值 + 長期支撐
            long_term_price = ma60 * 0.95  # MA60 下方 5%
            long_term_reason = f"長線價值：MA60({ma60:.1f}) 下方 5%，逢低布局"

            # 評估保守/樂觀
            if short_term_price >= current_price * 0.98:
                short_term_assessment = '偏樂觀（接近現價）'
            elif short_term_price <= current_price * 0.90:
                short_term_assessment = '偏保守（低於現價 10% 以上）'
            else:
                short_term_assessment = '中性'

            if mid_term_price >= current_price * 0.95:
                mid_term_assessment = '偏樂觀'
            elif mid_term_price <= current_price * 0.85:
                mid_term_assessment = '偏保守'
            else:
                mid_term_assessment = '中性'

            if long_term_price >= current_price * 0.90:
                long_term_assessment = '偏樂觀'
            elif long_term_price <= current_price * 0.80:
                long_term_assessment = '偏保守'
            else:
                long_term_assessment = '中性'

            buy_recommendations = {
                'short_term': {
                    'price': short_term_price,
                    'reason': short_term_reason,
                    'assessment': short_term_assessment,
                    'period': '1-2 週',
                },
                'mid_term': {
                    'price': mid_term_price,
                    'reason': mid_term_reason,
                    'assessment': mid_term_assessment,
                    'period': '1-3 個月',
                },
                'long_term': {
                    'price': long_term_price,
                    'reason': long_term_reason,
                    'assessment': long_term_assessment,
                    'period': '3-12 個月',
                },
            }

        # 綜合建議
        if comprehensive['fundamental_score'] >= 70 and comprehensive['timing_score'] < 40:
            suggestions.append('基本面優秀但技術面/籌碼面轉弱，可能是短期回檔，建議分批布局')
        elif comprehensive['fundamental_score'] < 50 and comprehensive['timing_score'] >= 70:
            suggestions.append('技術面/籌碼面強但基本面普通，可能是短線投機，注意停損')

        return {
            'strengths': strengths,
            'risks': risks,
            'suggestions': suggestions,
            'waiting_signals': waiting_signals,
            'buy_recommendations': buy_recommendations,
        }
