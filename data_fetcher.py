"""台股財報資料取得模組 - 支援多資料來源"""
import sys
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

# 確保可以匯入 FinMind
sys.path.insert(0, '/Users/mac/Library/Python/3.9/lib/python/site-packages')

try:
    from FinMind.data import DataLoader
    FINMIND_AVAILABLE = True
except:
    FINMIND_AVAILABLE = False


class TaiwanStockDataFetcher:
    """台股財報資料取得器"""

    def __init__(self, api_token: Optional[str] = None):
        """
        初始化資料取得器

        Args:
            api_token: FinMind API token（可選）
        """
        if FINMIND_AVAILABLE:
            self.loader = DataLoader()
            self.source = 'finmind'
        else:
            self.loader = None
            self.source = 'mock'
            print("警告：FinMind 不可用，使用模擬資料")

    def fetch_balance_sheet(self, stock_id: str, years: int = 3) -> pd.DataFrame:
        """取得資產負債表"""
        if self.source == 'finmind':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')
            try:
                return self.loader.taiwan_stock_balance_sheet(
                    stock_id=stock_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"FinMind 連線失敗: {e}")
                return self._get_mock_balance_sheet(stock_id)
        return self._get_mock_balance_sheet(stock_id)

    def fetch_income_statement(self, stock_id: str, years: int = 3) -> pd.DataFrame:
        """取得損益表"""
        if self.source == 'finmind':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')
            try:
                return self.loader.taiwan_stock_financial_statement(
                    stock_id=stock_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"FinMind 連線失敗: {e}")
                return self._get_mock_income_statement(stock_id)
        return self._get_mock_income_statement(stock_id)

    def fetch_cash_flow(self, stock_id: str, years: int = 3) -> pd.DataFrame:
        """取得現金流量表"""
        if self.source == 'finmind':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')
            try:
                return self.loader.taiwan_stock_cash_flows_statement(
                    stock_id=stock_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"FinMind 連線失敗: {e}")
                return self._get_mock_cash_flow(stock_id)
        return self._get_mock_cash_flow(stock_id)

    def fetch_stock_price(self, stock_id: str, days: int = 30) -> pd.DataFrame:
        """取得股價資料"""
        if self.source == 'finmind':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            try:
                return self.loader.taiwan_stock_daily(
                    stock_id=stock_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"FinMind 連線失敗: {e}")
                return self._get_mock_stock_price(stock_id)
        return self._get_mock_stock_price(stock_id)

    def fetch_stock_price_long(self, stock_id: str, years: int = 1) -> pd.DataFrame:
        """取得長期股價資料"""
        return self.fetch_stock_price(stock_id, days=365 * years)

    def fetch_month_revenue(self, stock_id: str, years: int = 3) -> pd.DataFrame:
        """取得月營收資料"""
        if self.source == 'finmind':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')
            try:
                return self.loader.taiwan_stock_month_revenue(
                    stock_id=stock_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"FinMind 連線失敗: {e}")
                return pd.DataFrame()
        return pd.DataFrame()

    def fetch_dividend(self, stock_id: str, years: int = 5) -> pd.DataFrame:
        """取得股利資料"""
        if self.source == 'finmind':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')
            try:
                return self.loader.taiwan_stock_dividend(
                    stock_id=stock_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"FinMind 連線失敗: {e}")
                return pd.DataFrame()
        return pd.DataFrame()

    def fetch_per_pbr(self, stock_id: str, days: int = 365) -> pd.DataFrame:
        """取得 PER/PBR 資料"""
        if self.source == 'finmind':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            try:
                return self.loader.taiwan_stock_per_pbr(
                    stock_id=stock_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"FinMind 連線失敗: {e}")
                return pd.DataFrame()
        return pd.DataFrame()

    def fetch_institutional_investors(self, stock_id: str, days: int = 30) -> pd.DataFrame:
        """取得三大法人買賣超資料"""
        if self.source == 'finmind':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            try:
                return self.loader.taiwan_stock_institutional_investors(
                    stock_id=stock_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"FinMind 連線失敗: {e}")
                return pd.DataFrame()
        return pd.DataFrame()

    def fetch_margin_data(self, stock_id: str, days: int = 30) -> pd.DataFrame:
        """取得融資融券資料"""
        if self.source == 'finmind':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            try:
                return self.loader.taiwan_stock_margin_purchase_short_sale(
                    stock_id=stock_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"FinMind 連線失敗: {e}")
                return pd.DataFrame()
        return pd.DataFrame()

    def fetch_shareholding(self, stock_id: str, days: int = 30) -> pd.DataFrame:
        """取得股權分散資料"""
        if self.source == 'finmind':
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            try:
                return self.loader.taiwan_stock_shareholding(
                    stock_id=stock_id, start_date=start_date, end_date=end_date
                )
            except Exception as e:
                print(f"FinMind 連線失敗: {e}")
                return pd.DataFrame()
        return pd.DataFrame()

    def fetch_market_cap(self, stock_id: str) -> Optional[float]:
        """取得市值資料"""
        try:
            price_data = self.fetch_stock_price(stock_id, days=7)
            if price_data.empty:
                return None

            latest_price = price_data.iloc[-1]['close']
            balance_sheet = self.fetch_balance_sheet(stock_id, years=1)
            if balance_sheet.empty:
                return None

            latest_date = balance_sheet['date'].max()
            latest_bs = balance_sheet[balance_sheet['date'] == latest_date]

            shares = None
            for _, row in latest_bs.iterrows():
                if row['type'] == 'OrdinaryShare':
                    shares = row['value'] / 10
                    break

            if shares and shares > 0:
                return latest_price * shares / 100000000
            return None
        except:
            return None

    def standardize_financial_data(self, stock_id: str, years: int = 3) -> List[Dict]:
        """取得並標準化財務數據"""
        balance_sheet = self.fetch_balance_sheet(stock_id, years)
        income_statement = self.fetch_income_statement(stock_id, years)
        cash_flow = self.fetch_cash_flow(stock_id, years)

        if balance_sheet.empty or income_statement.empty or cash_flow.empty:
            raise Exception("無法取得完整的財務數據")

        all_dates = sorted(
            set(balance_sheet['date'].unique()) &
            set(income_statement['date'].unique()) &
            set(cash_flow['date'].unique()),
            reverse=True
        )

        standardized_data = []
        for date in all_dates:
            bs_data = balance_sheet[balance_sheet['date'] == date]
            bs_dict = {row['type']: row['value'] for _, row in bs_data.iterrows()}

            is_data = income_statement[income_statement['date'] == date]
            is_dict = {row['type']: row['value'] for _, row in is_data.iterrows()}

            cf_data = cash_flow[cash_flow['date'] == date]
            cf_dict = {row['type']: row['value'] for _, row in cf_data.iterrows()}

            if isinstance(date, str):
                period_str = date
            else:
                period_str = date.strftime('%Y-%m-%d')

            standardized = {
                'period': period_str,
                'total_assets': bs_dict.get('TotalAssets', 0),
                'current_assets': bs_dict.get('CurrentAssets', 0),
                'current_liabilities': bs_dict.get('CurrentLiabilities', 0),
                'long_term_debt': bs_dict.get('BondsPayable', 0) + bs_dict.get('LongtermBorrowings', 0),
                'total_liabilities': bs_dict.get('Liabilities', 0),
                'stockholders_equity': bs_dict.get('Equity', 0),
                'retained_earnings': bs_dict.get('RetainedEarnings', 0),
                'revenue': is_dict.get('Revenue', 0),
                'gross_profit': is_dict.get('GrossProfit', 0),
                'operating_income': is_dict.get('OperatingIncome', 0),
                'net_income': is_dict.get('EquityAttributableToOwnersOfParent', 0),
                'operating_cash_flow': cf_dict.get('NetCashInflowFromOperatingActivities', 0),
                'investing_cash_flow': cf_dict.get('CashProvidedByInvestingActivities', 0),
                'financing_cash_flow': cf_dict.get('CashFlowsProvidedFromFinancingActivities', 0),
                'capex': abs(cf_dict.get('PropertyAndPlantAndEquipment', 0)),
                'weighted_average_shares': 0
            }
            standardized_data.append(standardized)

        return standardized_data

    # ===== 模擬資料（備用） =====
    def _get_mock_balance_sheet(self, stock_id: str) -> pd.DataFrame:
        """模擬資產負債表"""
        data = {
            'date': ['2024-12-31', '2023-12-31'],
            'stock_id': [stock_id, stock_id],
            'type': ['TotalAssets', 'TotalAssets'],
            'value': [5000000, 4800000],
            'origin_name': ['資產總額', '資產總額']
        }
        return pd.DataFrame(data)

    def _get_mock_income_statement(self, stock_id: str) -> pd.DataFrame:
        """模擬損益表"""
        data = {
            'date': ['2024-12-31', '2023-12-31'],
            'stock_id': [stock_id, stock_id],
            'type': ['Revenue', 'Revenue'],
            'value': [1500000, 1400000],
            'origin_name': ['營業收入', '營業收入']
        }
        return pd.DataFrame(data)

    def _get_mock_cash_flow(self, stock_id: str) -> pd.DataFrame:
        """模擬現金流量表"""
        data = {
            'date': ['2024-12-31', '2023-12-31'],
            'stock_id': [stock_id, stock_id],
            'type': ['NetCashInflowFromOperatingActivities', 'NetCashInflowFromOperatingActivities'],
            'value': [650000, 580000],
            'origin_name': ['營業活動之淨現金流入', '營業活動之淨現金流入']
        }
        return pd.DataFrame(data)

    def _get_mock_stock_price(self, stock_id: str) -> pd.DataFrame:
        """模擬股價資料"""
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        data = {
            'date': dates,
            'stock_id': [stock_id] * 30,
            'Trading_Volume': [1000000] * 30,
            'Trading_money': [1000000000] * 30,
            'open': [100.0] * 30,
            'max': [105.0] * 30,
            'min': [98.0] * 30,
            'close': [102.0] * 30,
            'spread': [2.0] * 30,
            'Trading_turnover': [10000] * 30
        }
        return pd.DataFrame(data)
