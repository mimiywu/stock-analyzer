#!/usr/bin/env python3
"""台股財報分析工具 - 命令列介面（七階段分析 + 自我驗證）"""
import sys
import argparse
from datetime import datetime

# 確保可以匯入 FinMind
sys.path.insert(0, '/Users/mac/Library/Python/3.9/lib/python/site-packages')

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
from utils import format_number, format_percentage


def main():
    parser = argparse.ArgumentParser(description='台股財報分析工具（七階段分析）')
    parser.add_argument('stock_id', help='股票代碼（例如：2330）')
    parser.add_argument('--years', type=int, default=3, help='分析年數（預設：3年）')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"台股財報分析工具 - 七階段綜合分析")
    print(f"{'='*60}")
    print(f"股票代碼: {args.stock_id}")
    print(f"分析年數: {args.years} 年")
    print(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    try:
        fetcher = TaiwanStockDataFetcher()

        # 1. 取得財務數據
        print("步驟 1/7: 取得財務數據...")
        standardized_data = fetcher.standardize_financial_data(args.stock_id, args.years)
        print(f"✓ 成功取得 {len(standardized_data)} 期財務數據")

        # 2. 取得技術面數據
        print("步驟 2/7: 取得技術面數據...")
        price_data = fetcher.fetch_stock_price_long(args.stock_id, years=1)
        print(f"✓ 成功取得 {len(price_data)} 筆股價數據")

        # 3. 取得質化與成長性數據
        print("步驟 3/7: 取得質化與成長性數據...")
        revenue_data = fetcher.fetch_month_revenue(args.stock_id, years=3)
        dividend_data = fetcher.fetch_dividend(args.stock_id, years=5)
        per_pbr_data = fetcher.fetch_per_pbr(args.stock_id, days=30)
        latest_per_pbr = per_pbr_data.iloc[-1].to_dict() if not per_pbr_data.empty else None
        print(f"✓ 成功取得月營收、股利、PER/PBR 數據")

        # 4. 取得籌碼面數據
        print("步驟 4/7: 取得籌碼面數據...")
        institutional_data = fetcher.fetch_institutional_investors(args.stock_id, days=30)
        margin_data = fetcher.fetch_margin_data(args.stock_id, days=30)
        shareholding_data = fetcher.fetch_shareholding(args.stock_id, days=30)
        print(f"✓ 成功取得法人買賣超、融資融券、股權分散數據")

        # 5. 驗證資料
        print("\n步驟 5/7: 驗證數據完整性...")
        validator = DataValidator()
        validation_result = validator.validate_financial_data(standardized_data)

        if not validation_result['is_valid']:
            print("✗ 數據驗證失敗:")
            for error in validation_result['errors']:
                print(f"  - {error}")
            return

        if validation_result['warnings']:
            print("⚠ 數據警告:")
            for warning in validation_result['warnings']:
                print(f"  - {warning}")
        else:
            print("✓ 數據驗證通過")

        # 6. 執行七階段分析
        print("\n步驟 6/7: 執行七階段分析...\n")

        # 初始化自我驗證器
        verifier = SelfVerifier()

        # 階段一：Piotroski F-Score
        print("【階段一】Piotroski F-Score 分析")
        piotroski = PiotroskiAnalyzer()
        piotroski_result = piotroski.analyze(standardized_data)
        print(f"  總分: {piotroski_result['total_score']}/9")
        score_rating = '優秀' if piotroski_result['total_score'] >= 7 else '良好' if piotroski_result['total_score'] >= 5 else '一般'
        print(f"  評價: {score_rating}")

        # 自我驗證
        v = verifier.verify_piotroski(standardized_data, piotroski_result)
        if v['errors']:
            print(f"  ✗ 驗證失敗:")
            for e in v['errors']:
                print(f"    - {e}")
        else:
            print(f"  ✓ 自我驗證通過")
        if v['warnings']:
            for w in v['warnings']:
                print(f"  ⚠ {w}")
        print()

        # 階段二：Altman Z-Score
        print("【階段二】Altman Z-Score 分析")
        market_cap = fetcher.fetch_market_cap(args.stock_id) or 10000
        altman = AltmanZScoreAnalyzer()
        altman_result = altman.analyze(standardized_data[0], market_cap)
        print(f"  Z-Score: {format_number(altman_result['z_score'])}")
        print(f"  判斷: {altman_result['zone']}")

        # 自我驗證
        v = verifier.verify_altman(standardized_data[0], market_cap, altman_result)
        if v['errors']:
            print(f"  ✗ 驗證失敗:")
            for e in v['errors']:
                print(f"    - {e}")
        else:
            print(f"  ✓ 自我驗證通過")
        if v['warnings']:
            for w in v['warnings']:
                print(f"  ⚠ {w}")
        print()

        # 階段三：杜邦分析
        print("【階段三】杜邦分析")
        dupont = DuPontAnalyzer()
        dupont_result = dupont.analyze(standardized_data)
        latest_roe = dupont_result['factors'][0]['roe']
        print(f"  ROE: {format_percentage(latest_roe)}")
        roe_rating = '卓越' if latest_roe > 0.2 else '良好' if latest_roe > 0.1 else '一般'
        print(f"  評價: {roe_rating}")

        # 自我驗證
        v = verifier.verify_dupont(standardized_data, dupont_result)
        if v['errors']:
            print(f"  ✗ 驗證失敗:")
            for e in v['errors']:
                print(f"    - {e}")
        else:
            print(f"  ✓ 自我驗證通過")
        if v['warnings']:
            for w in v['warnings']:
                print(f"  ⚠ {w}")
        print()

        # 階段四：現金流量分析
        print("【階段四】現金流量分析")
        cashflow = CashFlowAnalyzer()
        cashflow_result = cashflow.analyze(standardized_data)
        print(f"  營運現金流品質: {format_number(cashflow_result['assessment']['latest_quality'])}")
        fcf_in_wan = cashflow_result['assessment']['latest_fcf'] / 10000
        print(f"  自由現金流: {format_number(fcf_in_wan)} 萬元")
        print(f"  評價: {cashflow_result['assessment']['quality_rating']}")

        # 自我驗證
        v = verifier.verify_cashflow(standardized_data, cashflow_result)
        if v['errors']:
            print(f"  ✗ 驗證失敗:")
            for e in v['errors']:
                print(f"    - {e}")
        else:
            print(f"  ✓ 自我驗證通過")
        if v['warnings']:
            for w in v['warnings']:
                print(f"  ⚠ {w}")
        print()

        # 階段五：質化與成長性分析
        print("【階段五】質化與成長性分析")
        growth = GrowthAnalyzer()
        growth_result = growth.analyze(standardized_data, revenue_data, dividend_data, latest_per_pbr)
        print(f"  營收年增率: {growth_result['growth']['revenue_yoy']:.1%}")
        print(f"  EPS 年增率: {growth_result['growth']['eps_yoy']:.1%}")
        print(f"  成長趨勢: {growth_result['growth']['growth_trend']}")
        print(f"  連續配息年數: {growth_result['dividend']['consecutive_years']} 年")
        print(f"  本益比: {growth_result['valuation']['per']:.2f}")
        print(f"  評價: {growth_result['overall_rating']}")
        print()

        # 階段六：技術分析
        print("【階段六】技術分析")
        technical = TechnicalAnalyzer()
        technical_result = technical.analyze(price_data)
        print(f"  均線排列: {technical_result['trend']['ma_alignment']}")
        if technical_result['macd']:
            print(f"  MACD 信號: {technical_result['macd']['signal']}")
        if technical_result['rsi']:
            print(f"  RSI: {technical_result['rsi']:.2f}")
        if technical_result['kd']:
            print(f"  KD 信號: {technical_result['kd']['signal']}")
        if technical_result['bollinger']:
            b = technical_result['bollinger']
            print(f"  布林通道: %B={b['percent_b']:.4f}, 位置={b['position']}, 狀態={b['band_status']}")
        print(f"  量價關係: {technical_result['volume_analysis']['pattern'] if technical_result['volume_analysis'] else 'N/A'}")
        print(f"  評價: {technical_result['overall_rating']}")

        # 自我驗證
        v = verifier.verify_technical(price_data, technical_result)
        if v['errors']:
            print(f"  ✗ 驗證失敗:")
            for e in v['errors']:
                print(f"    - {e}")
        else:
            print(f"  ✓ 自我驗證通過")
        if v['warnings']:
            for w in v['warnings']:
                print(f"  ⚠ {w}")
        print()

        # 階段七：籌碼面分析
        print("【階段七】籌碼面分析")
        chip = ChipAnalyzer()
        chip_result = chip.analyze(institutional_data, margin_data, shareholding_data)
        print(f"  近 5 日法人買賣超: {chip_result['institutional']['recent_5d_net']:,.0f} 張")
        print(f"  近 20 日法人買賣超: {chip_result['institutional']['recent_20d_net']:,.0f} 張")
        print(f"  連續買超天數: {chip_result['institutional']['consecutive_buy_days']} 天")
        print(f"  融資餘額: {chip_result['margin']['margin_balance']:,.0f} 張")
        print(f"  外資持股比例: {chip_result['shareholding']['foreign_ratio']:.1%}")
        print(f"  評價: {chip_result['overall_rating']}")

        # 自我驗證
        v = verifier.verify_chip(institutional_data, margin_data, shareholding_data, chip_result)
        if v['errors']:
            print(f"  ✗ 驗證失敗:")
            for e in v['errors']:
                print(f"    - {e}")
        else:
            print(f"  ✓ 自我驗證通過")
        if v['warnings']:
            for w in v['warnings']:
                print(f"  ⚠ {w}")
        print()

        # 7. 綜合評估
        print("步驟 7/7: 綜合評估...\n")

        # 計算各階段分數
        scorer = ComprehensiveScorer()
        scores = scorer.calculate_stage_scores(
            piotroski_result, altman_result, dupont_result,
            cashflow_result, growth_result, technical_result, chip_result
        )

        # 計算綜合評分
        comprehensive = scorer.calculate_comprehensive_score(scores)

        # 取得目標價資料
        target_fetcher = TargetPriceFetcher()
        target_prices = target_fetcher.get_sample_target_prices(args.stock_id)
        target_stats = target_fetcher.calculate_target_price_stats(target_prices)

        print(f"{'='*60}")
        print("七階段綜合評估（0-100 分制）")
        print(f"{'='*60}")
        print(f"{'分析階段':<20} {'分數':<10} {'評價':<10} {'權重':<8}")
        print(f"{'-'*60}")

        stage_names = {
            'piotroski': 'Piotroski F-Score',
            'altman': 'Altman Z-Score',
            'dupont': '杜邦分析',
            'cashflow': '現金流量分析',
            'growth': '質化/成長性',
            'technical': '技術面',
            'chip': '籌碼面',
        }

        for stage_key, stage_name in stage_names.items():
            score_data = scores[stage_key]
            print(f"{stage_name:<20} {score_data['normalized_score']:>6.1f}分 {score_data['rating']:<10} {score_data['weight']*100:>5.0f}%")

        print(f"{'='*60}")
        print(f"{'綜合評分':<20} {comprehensive['final_score']:>6.1f}分 {comprehensive['overall_rating']:<10}")
        print(f"{'='*60}\n")

        # 目標價資訊
        if target_prices:
            print(f"{'='*60}")
            print("機構目標價")
            print(f"{'='*60}")
            print(f"{'機構名稱':<20} {'目標價':<10} {'日期':<12} {'評等':<10}")
            print(f"{'-'*60}")
            for tp in target_prices:
                print(f"{tp['institution']:<20} {tp['target_price']:>8.0f} {tp['date']:<12} {tp['rating']:<10}")

            print(f"\n統計:")
            print(f"  平均目標價: {target_stats['mean']:,.0f}")
            print(f"  最高目標價: {target_stats['high']:,.0f}")
            print(f"  最低目標價: {target_stats['low']:,.0f}")
            print(f"  分析師數量: {target_stats['count']}")
            print(f"  買進評等: {target_stats['buy_ratings']}")
            print(f"  持有評等: {target_stats['hold_ratings']}")
            print(f"  賣出評等: {target_stats['sell_ratings']}")
            print(f"{'='*60}\n")

        # 8. 投資建議
        print(f"{'='*60}")
        print("投資建議")
        print(f"{'='*60}")

        # 取得目前股價
        current_price = price_data['close'].astype(float).iloc[-1] if not price_data.empty else None

        advice = scorer.generate_investment_advice(
            comprehensive, scores, technical_result, chip_result, current_price
        )

        if advice['strengths']:
            print("\n✅ 主要優勢:")
            for s in advice['strengths']:
                print(f"  • {s}")

        if advice['risks']:
            print("\n⚠️  風險因素:")
            for r in advice['risks']:
                print(f"  • {r}")

        if advice['suggestions']:
            print("\n 建議:")
            for s in advice['suggestions']:
                print(f"  • {s}")

        # 等待明確信號
        if advice['waiting_signals']:
            print("\n⏳ 需要等待的明確信號:")
            for sig in advice['waiting_signals']:
                print(f"  • {sig}")

        # 短中長線買入價建議
        if advice['buy_recommendations']:
            print(f"\n{'='*60}")
            print("建議買入價分析")
            print(f"{'='*60}")

            if current_price:
                print(f"目前股價: {current_price:.2f} 元")

            buy_recs = advice['buy_recommendations']

            print("\n🔵 短線投資（1-2 週）:")
            short = buy_recs['short_term']
            print(f"  建議買入價: {short['price']:.2f} 元")
            print(f"  原因: {short['reason']}")
            print(f"  評估: {short['assessment']}")

            print("\n🟢 中線投資（1-3 個月）:")
            mid = buy_recs['mid_term']
            print(f"  建議買入價: {mid['price']:.2f} 元")
            print(f"  原因: {mid['reason']}")
            print(f"  評估: {mid['assessment']}")

            print("\n🟡 長線投資（3-12 個月）:")
            long = buy_recs['long_term']
            print(f"  建議買入價: {long['price']:.2f} 元")
            print(f"  原因: {long['reason']}")
            print(f"  評估: {long['assessment']}")

        print(f"\n{'='*60}")
        print(f"綜合建議: {comprehensive['recommendation']}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n✗ 分析失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
