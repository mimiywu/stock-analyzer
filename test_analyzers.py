"""測試分析模組"""
from analyzers.piotroski import PiotroskiAnalyzer
from analyzers.altman import AltmanZScoreAnalyzer
from analyzers.dupont import DuPontAnalyzer
from analyzers.cashflow import CashFlowAnalyzer


def test_analyzers():
    """測試所有分析模組"""

    # 模擬財務數據（台積電風格）
    mock_data = [
        {
            'period': '2024-Q3',
            'total_assets': 5000000,
            'current_assets': 2000000,
            'current_liabilities': 1000000,
            'long_term_debt': 500000,
            'total_liabilities': 2000000,
            'stockholders_equity': 3000000,
            'retained_earnings': 2000000,
            'revenue': 1500000,
            'gross_profit': 800000,
            'operating_income': 600000,
            'net_income': 500000,
            'operating_cash_flow': 650000,
            'investing_cash_flow': -300000,
            'financing_cash_flow': -100000,
            'capex': 200000,
            'weighted_average_shares': 2500000
        },
        {
            'period': '2023-Q4',
            'total_assets': 4800000,
            'current_assets': 1900000,
            'current_liabilities': 1100000,
            'long_term_debt': 600000,
            'total_liabilities': 2100000,
            'stockholders_equity': 2700000,
            'retained_earnings': 1800000,
            'revenue': 1400000,
            'gross_profit': 700000,
            'operating_income': 550000,
            'net_income': 450000,
            'operating_cash_flow': 580000,
            'investing_cash_flow': -280000,
            'financing_cash_flow': -120000,
            'capex': 180000,
            'weighted_average_shares': 2500000
        }
    ]

    print("=" * 60)
    print("測試 Piotroski F-Score")
    print("=" * 60)
    piotroski = PiotroskiAnalyzer()
    result = piotroski.analyze(mock_data)
    print(f"總分: {result['total_score']}/9")
    print("\n指標明細:")
    for ind in result['indicators']:
        print(f"  {ind['name']}: {ind['value']} -> 得分 {ind['score']}")

    print("\n" + "=" * 60)
    print("測試 Altman Z-Score")
    print("=" * 60)
    altman = AltmanZScoreAnalyzer()
    market_cap = 15000  # 15000 億元
    result = altman.analyze(mock_data[0], market_cap)
    print(f"Z-Score: {result['z_score']:.4f}")
    print(f"判斷區域: {result['zone']}")
    print("\n因子明細:")
    for factor in result['factors']:
        print(f"  {factor['name']}: 計算值 {factor['value']}, 加權值 {factor['weighted']}")

    print("\n" + "=" * 60)
    print("測試杜邦分析")
    print("=" * 60)
    dupont = DuPontAnalyzer()
    result = dupont.analyze(mock_data)
    print("三因子趨勢:")
    for factor in result['factors']:
        print(f"  {factor['period']}:")
        print(f"    淨利率: {factor['net_margin']:.4f}")
        print(f"    資產周轉率: {factor['asset_turnover']:.4f}")
        print(f"    權益乘數: {factor['equity_multiplier']:.4f}")
        print(f"    ROE: {factor['roe']:.4f}")

    if 'analysis' in result:
        analysis = result['analysis']
        print(f"\n趨勢分析:")
        print(f"  ROE 變化: {analysis.get('roe_change', 0):.4f}")
        print(f"  主要驅動因子: {', '.join(analysis.get('main_drivers', []))}")
        print(f"  財務槓桿水準: {analysis.get('leverage_assessment', 'N/A')}")

    print("\n" + "=" * 60)
    print("測試現金流量分析")
    print("=" * 60)
    cashflow = CashFlowAnalyzer()
    result = cashflow.analyze(mock_data)
    print("最新期間現金流:")
    latest = result['periods'][0]
    print(f"  營運現金流: {latest['operating_cash_flow']:,.0f}")
    print(f"  淨利: {latest['net_income']:,.0f}")
    print(f"  自由現金流: {latest['free_cash_flow']:,.0f}")
    print(f"  現金流品質: {latest['cash_quality_ratio']:.4f}")

    print(f"\n綜合評估:")
    assessment = result['assessment']
    print(f"  品質評價: {assessment['quality_rating']}")
    print(f"  FCF 趨勢: {assessment['fcf_trend']}")
    print(f"  結構評估: {assessment['structure_assessment']}")

    print("\n" + "=" * 60)
    print("所有測試完成！")
    print("=" * 60)


if __name__ == '__main__':
    test_analyzers()
