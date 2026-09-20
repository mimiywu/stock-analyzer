"""台股財報分析 Web 應用程式 - 七階段分析 + 綜合評分 + 目標價 + 買賣建議"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data_fetcher import TaiwanStockDataFetcher
from data_validator import DataValidator
from self_verifier import SelfVerifier
from comprehensive_scorer import ComprehensiveScorer
from target_price_fetcher import TargetPriceFetcher
from analyzers.piotroski import PiotroskiAnalyzer
from analyzers.altman import AltmanZScoreAnalyzer
from analyzers.dupont import DuPontAnalyzer
from analyzers.cashflow import CashFlowAnalyzer
from analyzers.growth import GrowthAnalyzer
from analyzers.technical import TechnicalAnalyzer
from analyzers.chip import ChipAnalyzer
from analyzers.valuation import ValuationAnalyzer
from utils import format_number, format_percentage


def main():
    st.set_page_config(
        page_title='台股七階段分析工具',
        page_icon='',
        layout='wide'
    )

    st.title('📊 台股七階段綜合分析工具')
    st.markdown('輸入股票代碼，自動執行基本面 + 技術面 + 籌碼面完整分析')

    with st.sidebar:
        st.header('設定')
        stock_id = st.text_input('股票代碼', value='2330', help='例如：2330（台積電）')
        years = st.slider('分析年數', min_value=1, max_value=5, value=3)
        analyze_button = st.button('開始分析', type='primary', use_container_width=True)

        st.markdown('---')
        st.markdown('### 七階段分析法')
        st.markdown('''
        **基本面**
        1. Piotroski F-Score
        2. Altman Z-Score
        3. 杜邦分析
        4. 現金流量分析
        5. 質化與成長性

        **技術面**
        6. 均線/MACD/RSI/KD/布林通道

        **籌碼面**
        7. 法人/融資融券/股權分散
        ''')

    if not analyze_button:
        return

    with st.spinner(f'正在從 FinMind API 取得 {stock_id} 的數據...'):
        try:
            fetcher = TaiwanStockDataFetcher()

            standardized_data = fetcher.standardize_financial_data(stock_id, years)
            price_data = fetcher.fetch_stock_price_long(stock_id, years=1)
            revenue_data = fetcher.fetch_month_revenue(stock_id, years=3)
            dividend_data = fetcher.fetch_dividend(stock_id, years=5)
            per_pbr_df = fetcher.fetch_per_pbr(stock_id, days=365)  # 取一年資料做歷史比較
            latest_per_pbr = per_pbr_df.iloc[-1].to_dict() if not per_pbr_df.empty else None
            institutional_data = fetcher.fetch_institutional_investors(stock_id, days=30)
            margin_data = fetcher.fetch_margin_data(stock_id, days=30)
            shareholding_data = fetcher.fetch_shareholding(stock_id, days=30)

            st.success('✓ 成功取得所有數據')

            validator = DataValidator()
            validation_result = validator.validate_financial_data(standardized_data)
            if not validation_result['is_valid']:
                for error in validation_result['errors']:
                    st.error(f'  • {error}')
                st.stop()

            market_cap = fetcher.fetch_market_cap(stock_id) or 10000

            verifier = SelfVerifier()

            piotroski = PiotroskiAnalyzer()
            piotroski_result = piotroski.analyze(standardized_data)
            v1 = verifier.verify_piotroski(standardized_data, piotroski_result)

            altman = AltmanZScoreAnalyzer()
            altman_result = altman.analyze(standardized_data[0], market_cap)
            v2 = verifier.verify_altman(standardized_data[0], market_cap, altman_result)

            dupont = DuPontAnalyzer()
            dupont_result = dupont.analyze(standardized_data)
            v3 = verifier.verify_dupont(standardized_data, dupont_result)

            cashflow = CashFlowAnalyzer()
            cashflow_result = cashflow.analyze(standardized_data)
            v4 = verifier.verify_cashflow(standardized_data, cashflow_result)

            growth = GrowthAnalyzer()
            growth_result = growth.analyze(
                standardized_data, revenue_data, dividend_data, latest_per_pbr
            )

            technical = TechnicalAnalyzer()
            technical_result = technical.analyze(price_data)
            v6 = verifier.verify_technical(price_data, technical_result)

            chip = ChipAnalyzer()
            chip_result = chip.analyze(
                institutional_data, margin_data, shareholding_data
            )
            v7 = verifier.verify_chip(
                institutional_data, margin_data, shareholding_data, chip_result
            )

            # 估值分析
            current_price = price_data['close'].astype(float).iloc[-1] if not price_data.empty else None
            valuation = ValuationAnalyzer()
            valuation_result = valuation.analyze(
                stock_id, current_price, per_pbr_df, standardized_data, growth_result
            )

            verifications = [v1, v2, v3, v4, v6, v7]

            display_all_results(
                stock_id, piotroski_result, altman_result, dupont_result,
                cashflow_result, growth_result, technical_result, chip_result,
                price_data, valuation_result, verifications
            )

        except Exception as e:
            st.error(f'分析失敗：{str(e)}')
            import traceback
            st.code(traceback.format_exc())


def display_all_results(stock_id, piotroski, altman, dupont, cashflow,
                        growth, technical, chip, price_data, valuation_result, verifications):
    """顯示七階段分析結果 + 綜合評分 + 目標價 + 買賣建議"""

    # ===== 七階段綜合評估表格 =====
    st.subheader('📋 七階段綜合評估')

    score_rating = '優秀' if piotroski['total_score'] >= 7 else '良好' if piotroski['total_score'] >= 5 else '一般'
    latest_roe = dupont['factors'][0]['roe']
    roe_rating = '卓越' if latest_roe > 0.2 else '良好' if latest_roe > 0.1 else '一般'

    summary_data = {
        '分析階段': [
            'Piotroski F-Score', 'Altman Z-Score', '杜邦分析',
            '現金流量分析', '質化/成長性', '技術面', '籌碼面'
        ],
        '評分/狀態': [
            f"{piotroski['total_score']}/9",
            f"{format_number(altman['z_score'])}",
            f"ROE {format_percentage(latest_roe)}",
            format_number(cashflow['assessment']['latest_quality']),
            f"YoY {format_percentage(growth['growth']['revenue_yoy'])}",
            technical['trend']['ma_alignment'],
            format_number(chip['institutional']['recent_5d_net']),
        ],
        '評價': [
            score_rating, altman['zone'], roe_rating,
            cashflow['assessment']['quality_rating'],
            growth['overall_rating'],
            technical['overall_rating'],
            chip['overall_rating'],
        ],
        '驗證': [
            '✓' if verifications[0]['passed'] else '',
            '✓' if verifications[1]['passed'] else '',
            '✓' if verifications[2]['passed'] else '',
            '✓' if verifications[3]['passed'] else '',
            'N/A',
            '✓' if verifications[4]['passed'] else '',
            '✓' if verifications[5]['passed'] else '',
        ],
    }

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    st.markdown('---')

    # ===== 七階段綜合評分（0-100 分制） =====
    st.subheader('📊 七階段綜合評分（0-100 分制）')

    scorer = ComprehensiveScorer()
    scores = scorer.calculate_stage_scores(
        piotroski, altman, dupont, cashflow, growth, technical, chip
    )
    comprehensive = scorer.calculate_comprehensive_score(scores)

    stage_names = {
        'piotroski': 'Piotroski F-Score',
        'altman': 'Altman Z-Score',
        'dupont': '杜邦分析',
        'cashflow': '現金流量分析',
        'growth': '質化/成長性',
        'technical': '技術面',
        'chip': '籌碼面',
    }

    score_rows = []
    for stage_key, stage_name in stage_names.items():
        sd = scores[stage_key]
        score_rows.append({
            '分析階段': stage_name,
            '分數': f"{sd['normalized_score']:.1f}",
            '評價': sd['rating'],
            '權重': f"{sd['weight']*100:.0f}%",
        })

    score_df = pd.DataFrame(score_rows)
    st.dataframe(score_df, use_container_width=True, hide_index=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('綜合評分', f"{comprehensive['final_score']:.1f}分")
    with col2:
        st.metric('基本面分數', f"{comprehensive['fundamental_score']:.1f}分")
    with col3:
        st.metric('時機分數', f"{comprehensive['timing_score']:.1f}分")

    rating_color = 'green' if comprehensive['final_score'] >= 65 else 'orange' if comprehensive['final_score'] >= 50 else 'red'
    st.markdown(f"**綜合建議：** :{rating_color}[{comprehensive['overall_rating']}] — {comprehensive['recommendation']}")
    st.markdown('---')

    # ===== 機構目標價 =====
    st.subheader('🎯 機構目標價')

    target_fetcher = TargetPriceFetcher()
    target_prices = target_fetcher.get_sample_target_prices(stock_id)
    target_stats = target_fetcher.calculate_target_price_stats(target_prices)

    if target_prices:
        target_df = pd.DataFrame(target_prices)
        target_df.columns = ['機構名稱', '目標價', '日期', '評等']
        st.dataframe(target_df, use_container_width=True, hide_index=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric('平均目標價', f"{target_stats['mean']:,.0f}")
        with col2:
            st.metric('最高目標價', f"{target_stats['high']:,.0f}")
        with col3:
            st.metric('最低目標價', f"{target_stats['low']:,.0f}")
        with col4:
            st.metric('分析師數量', f"{target_stats['count']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('買進評等', f"{target_stats['buy_ratings']}")
        with col2:
            st.metric('持有評等', f"{target_stats['hold_ratings']}")
        with col3:
            st.metric('賣出評等', f"{target_stats['sell_ratings']}")
    else:
        st.info('暫無機構目標價資料')

    st.markdown('---')

    # ===== 估值分析：現在股價是貴還是便宜？ =====
    st.subheader('💰 估值分析：現在股價是貴還是便宜？')

    current_price = price_data['close'].astype(float).iloc[-1] if not price_data.empty else None

    if current_price:
        st.markdown(f'**目前股價：** {current_price:.2f} 元')

    # 綜合判斷
    verdict = valuation_result['overall_verdict']
    verdict_color = valuation_result['verdict_color']
    st.markdown(f'**綜合判斷：** :{verdict_color}[{verdict}]')

    # 五秒判斷法
    five_sec = valuation_result['five_second_check']
    st.markdown('###  五秒判斷法')

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'**① 現在 PE、PB：** {five_sec["pe_pb"]}')
        st.markdown(f'**② 和過去比：** {five_sec["vs_history"]}')
        st.markdown(f'**③ 和同業比：** {five_sec["vs_industry"]}')
    with col2:
        st.markdown(f'**④ 成長展望：** {five_sec["growth_outlook"]}')
        st.markdown(f'**⑤ 股票類型：** {five_sec["stock_type"]}')

    # 四層次詳細分析
    st.markdown('### 📊 四層次估值分析')

    # 層次一：歷史比較
    hist = valuation_result['historical_analysis']
    with st.expander('層次一：和自己歷史比', expanded=True):
        if hist['details']:
            for detail in hist['details']:
                st.markdown(f'- {detail}')
        st.markdown(f'**PE 狀態：** {hist["pe_status"]}')
        st.markdown(f'**PB 狀態：** {hist["pb_status"]}')

    # 層次二：同業比較
    industry = valuation_result['industry_analysis']
    with st.expander('層次二：和同業比', expanded=True):
        if industry['details']:
            for detail in industry['details']:
                st.markdown(f'- {detail}')
        st.markdown(f'**產業：** {industry["industry"]}')

    # 層次三：PEG
    peg = valuation_result['peg_analysis']
    with st.expander('層次三：和成長比（PEG）', expanded=True):
        if peg['details']:
            for detail in peg['details']:
                st.markdown(f'- {detail}')
        st.markdown(f'**PEG 狀態：** {peg["peg_status"]}')

    # 層次四：DCF
    dcf = valuation_result['dcf_analysis']
    with st.expander('層次四：和內在價值比（DCF）', expanded=True):
        if dcf['details']:
            for detail in dcf['details']:
                st.markdown(f'- {detail}')
        if dcf['intrinsic_value'] > 0:
            st.markdown(f'**內在價值：** {dcf["intrinsic_value"]:.2f} 元')
            st.markdown(f'**上漲/下跌空間：** {dcf["upside"]:.1f}%')

    st.markdown('---')

    # ===== 各階段詳細結果 =====

    # 階段一：Piotroski F-Score
    st.subheader(' 階段一：Piotroski F-Score 分析')
    col1, col2 = st.columns([1, 2])
    with col1:
        score = piotroski['total_score']
        score_color = 'green' if score >= 7 else 'orange' if score >= 5 else 'red'
        st.metric('總分', f'{score}/9')
        st.markdown(f'**評價：** :{score_color}[{score_rating}]')
    with col2:
        indicators_df = pd.DataFrame(piotroski['indicators'])
        indicators_df.columns = ['指標', '數值', '得分']
        st.dataframe(indicators_df, use_container_width=True, hide_index=True)
    st.markdown('---')

    # 階段二：Altman Z-Score
    st.subheader('📊 階段二：Altman Z-Score 分析')
    col1, col2 = st.columns([1, 2])
    with col1:
        z_score = altman['z_score']
        zone = altman['zone']
        zone_color = 'green' if zone == '安全區域' else 'orange' if zone == '灰色區域' else 'red'
        st.metric('Z-Score', format_number(z_score))
        st.markdown(f'**判斷：** :{zone_color}[{zone}]')
    with col2:
        factors_df = pd.DataFrame(altman['factors'])
        factors_df.columns = ['因子', '計算值', '加權值']
        st.dataframe(factors_df, use_container_width=True, hide_index=True)
    st.markdown('---')

    # 階段三：杜邦分析
    st.subheader('📊 階段三：杜邦分析')
    factors_df = pd.DataFrame(dupont['factors'])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=factors_df['period'], y=factors_df['net_margin'] * 100,
        name='淨利率 (%)', mode='lines+markers'
    ))
    fig.add_trace(go.Scatter(
        x=factors_df['period'], y=factors_df['asset_turnover'],
        name='資產周轉率', mode='lines+markers'
    ))
    fig.add_trace(go.Scatter(
        x=factors_df['period'], y=factors_df['equity_multiplier'],
        name='權益乘數', mode='lines+markers'
    ))
    fig.update_layout(title='杜邦分析三因子趨勢', hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

    if 'analysis' in dupont:
        analysis = dupont['analysis']
        st.markdown(f'''
        - **ROE 變化：** {format_percentage(analysis.get("roe_change", 0))}
        - **主要驅動因子：** {", ".join(analysis.get("main_drivers", []))}
        - **財務槓桿水準：** {analysis.get("leverage_assessment", "N/A")}
        ''')
    st.markdown('---')

    # 階段四：現金流量分析
    st.subheader('📊 階段四：現金流量分析')
    col1, col2 = st.columns(2)
    with col1:
        st.metric('營運現金流品質', format_number(cashflow['assessment']['latest_quality']))
        quality = cashflow["assessment"]["quality_rating"]
        quality_color = 'green' if quality == '優秀' else 'orange' if quality == '良好' else 'red'
        st.markdown(f'**評價：** :{quality_color}[{quality}]')
    with col2:
        fcf_in_wan = cashflow['assessment']['latest_fcf'] / 10000
        st.metric('自由現金流', f"{format_number(fcf_in_wan)} 萬元")
        fcf_trend = cashflow["assessment"]["fcf_trend"]
        trend_color = 'green' if fcf_trend == '增長' else 'orange' if fcf_trend == '穩定' else 'red'
        st.markdown(f'**趨勢：** :{trend_color}[{fcf_trend}]')

    latest_period = cashflow['periods'][0]
    structure = latest_period['structure']
    fig = go.Figure(data=[go.Pie(
        labels=['營運活動', '投資活動', '籌資活動'],
        values=[structure['operating_ratio'] * 100,
                structure['investing_ratio'] * 100,
                structure['financing_ratio'] * 100],
        hole=0.3
    )])
    fig.update_layout(title='現金流結構分析')
    st.plotly_chart(fig, use_container_width=True)

    cf_score = scores['cashflow']['normalized_score']
    cf_rating = scores['cashflow']['rating']
    cf_color = 'green' if cf_score >= 70 else 'orange' if cf_score >= 50 else 'red'
    st.markdown(f"**階段四評分：** :{cf_color}[{cf_score:.1f}分 — {cf_rating}]")
    st.markdown('---')

    # 階段五：質化與成長性
    st.subheader('📊 階段五：質化與成長性分析')
    g = growth['growth']
    d = growth['dividend']
    v = growth['valuation']
    st.markdown(f'''
    | 指標 | 數值 |
    |------|------|
    | 營收年增率 | {g['revenue_yoy']:.1%} |
    | EPS 年增率 | {g['eps_yoy']:.1%} |
    | 成長趨勢 | {g['growth_trend']} |
    | 連續配息年數 | {d['consecutive_years']} 年 |
    | 本益比 (PER) | {v['per']:.2f} |
    | 股價淨值比 (PBR) | {v['pbr']:.2f} |
    | 殖利率 | {v['dividend_yield']:.2f}% |
    ''')

    g_score = scores['growth']['normalized_score']
    g_rating = scores['growth']['rating']
    g_color = 'green' if g_score >= 70 else 'orange' if g_score >= 50 else 'red'
    st.markdown(f"**階段五評分：** :{g_color}[{g_score:.1f}分 — {g_rating}]")
    st.markdown('---')

    # 階段六：技術分析
    st.subheader('📊 階段六：技術分析')
    t = technical['trend']
    m = technical.get('macd')
    rsi_val = technical.get('rsi')
    k = technical.get('kd')
    b = technical.get('bollinger')
    vol = technical.get('volume_analysis')

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'''
        **均線系統**
        - 排列: {t['ma_alignment']}
        - MA5: {t['ma5']:.2f}
        - MA20: {t['ma20']:.2f}
        - MA60: {t['ma60']:.2f}
        ''')
    with col2:
        st.markdown(f'''
        **動能指標**
        - MACD: {m['signal'] if m else 'N/A'}
        - RSI(14): {f'{rsi_val:.2f}' if rsi_val else 'N/A'}
        - KD: {k['signal'] if k else 'N/A'}
        ''')
    with col3:
        if b:
            st.markdown(f'''
            **布林通道**
            - 上軌: {b['upper_band']:.2f}
            - 中軌: {b['middle_band']:.2f}
            - 下軌: {b['lower_band']:.2f}
            - %B: {b['percent_b']:.4f}
            - 位置: {b['position']}
            - 狀態: {b['band_status']}
            ''')

    if vol:
        st.markdown(f"**量價關係：** {vol['pattern']} — {vol['assessment']}")

    t_score = scores['technical']['normalized_score']
    t_rating = scores['technical']['rating']
    t_color = 'green' if t_score >= 70 else 'orange' if t_score >= 50 else 'red'
    st.markdown(f"**階段六評分：** :{t_color}[{t_score:.1f}分 — {t_rating}]")
    st.markdown('---')

    # 階段七：籌碼面分析
    st.subheader('📊 階段七：籌碼面分析')
    inst = chip['institutional']
    margin = chip['margin']
    sh = chip['shareholding']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'''
        **法人買賣超**
        - 近 5 日: {inst['recent_5d_net']:,.0f} 張
        - 近 20 日: {inst['recent_20d_net']:,.0f} 張
        - 連續買超: {inst['consecutive_buy_days']} 天
        ''')
    with col2:
        st.markdown(f'''
        **融資融券**
        - 融資餘額: {margin['margin_balance']:,.0f} 張
        - 融券餘額: {margin['short_balance']:,.0f} 張
        - 券資比: {margin['short_ratio']:.2%}
        - 趨勢: {margin['margin_trend']}
        ''')
    with col3:
        st.markdown(f'''
        **股權分散**
        - 外資持股: {sh['foreign_ratio']:.1%}
        - 發行股數: {sh['total_shares']:,.0f}
        ''')

    chip_score = scores['chip']['normalized_score']
    chip_rating = scores['chip']['rating']
    chip_color = 'green' if chip_score >= 70 else 'orange' if chip_score >= 50 else 'red'
    st.markdown(f"**階段七評分：** :{chip_color}[{chip_score:.1f}分 — {chip_rating}]")
    st.markdown('---')

    # ===== 綜合投資建議 =====
    st.subheader('💡 綜合投資建議')

    # 取得目前股價
    current_price = price_data['close'].astype(float).iloc[-1] if not price_data.empty else None

    advice = scorer.generate_investment_advice(
        comprehensive, scores, technical, chip, current_price
    )

    if advice['strengths']:
        st.markdown('**✅ 主要優勢：**')
        for s in advice['strengths']:
            st.markdown(f'- {s}')

    if advice['risks']:
        st.markdown('**⚠️ 風險因素：**')
        for r in advice['risks']:
            st.markdown(f'- {r}')

    if advice['suggestions']:
        st.markdown('**💡 建議：**')
        for s in advice['suggestions']:
            st.markdown(f'- {s}')

    # 等待明確信號
    if advice['waiting_signals']:
        st.markdown('**⏳ 需要等待的明確信號：**')
        for sig in advice['waiting_signals']:
            st.markdown(f'- {sig}')

    # 短中長線買入價建議
    if advice['buy_recommendations']:
        st.markdown('---')
        st.subheader(' 建議買入價分析')

        if current_price:
            st.markdown(f'**目前股價：** {current_price:.2f} 元')

        buy_recs = advice['buy_recommendations']

        st.markdown('**🔵 短線投資（1-2 週）**')
        short = buy_recs['short_term']
        st.markdown(f'- **建議買入價：** {short["price"]:.2f} 元')
        st.markdown(f'- **原因：** {short["reason"]}')
        st.markdown(f'- **評估：** {short["assessment"]}')

        st.markdown('**🟢 中線投資（1-3 個月）**')
        mid = buy_recs['mid_term']
        st.markdown(f'- **建議買入價：** {mid["price"]:.2f} 元')
        st.markdown(f'- **原因：** {mid["reason"]}')
        st.markdown(f'- **評估：** {mid["assessment"]}')

        st.markdown('**🟡 長線投資（3-12 個月）**')
        long = buy_recs['long_term']
        st.markdown(f'- **建議買入價：** {long["price"]:.2f} 元')
        st.markdown(f'- **原因：** {long["reason"]}')
        st.markdown(f'- **評估：** {long["assessment"]}')

    st.markdown('---')
    st.subheader(' 投資價值 vs 買賣時機')

    col1, col2 = st.columns(2)
    with col1:
        if comprehensive['fundamental_score'] >= 70:
            st.success('📈 投資價值: 優秀（基本面強健，值得長期持有）')
        elif comprehensive['fundamental_score'] >= 50:
            st.info('📊 投資價值: 良好（基本面穩健，可考慮布局）')
        else:
            st.warning('⚠️ 投資價值: 普通（基本面有疑慮，建議觀望）')

    with col2:
        if comprehensive['timing_score'] >= 70:
            st.success('⏰ 買賣時機: 良好（技術面與籌碼面配合，可考慮進場）')
        elif comprehensive['timing_score'] >= 40:
            st.info('⏳ 買賣時機: 中性（建議等待更明確信號）')
        else:
            st.warning(' 買賣時機: 不佳（技術面或籌碼面轉弱，建議觀望）')

    if comprehensive['fundamental_score'] >= 70 and comprehensive['timing_score'] < 40:
        st.warning('⚠️ 基本面優秀但技術面/籌碼面轉弱，可能是短期回檔，建議分批布局')
    elif comprehensive['fundamental_score'] < 50 and comprehensive['timing_score'] >= 70:
        st.warning('️ 技術面/籌碼面強但基本面普通，可能是短線投機，注意停損')


if __name__ == '__main__':
    main()
