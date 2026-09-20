"""台股財報資料取得模組 - 使用 FinMind API"""
import sys
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

# 確保可以匯入 FinMind
sys.path.insert(0, '/Users/mac/Library/Python/3.9/lib/python/site-packages')
from FinMind.data import DataLoader


class TaiwanStockDataFetcher:
    """台股財報資料取得器"""

    def __init__(self, api_token: Optional[str] = None):
        """
        初始化 FinMind DataLoader

        Args:
            api_token: FinMind API token（可選，FinMind 2.0+ 不需要 token）
        """
        self.loader = DataLoader()

    def fetch_balance_sheet(self, stock_id: str, years: int = 3) -> pd.DataFrame:
        """
        取得資產負債表

        Args:
            stock_id: 股票代碼
            years: 取得幾年資料

        Returns:
            DataFrame: 資產負債表資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_balance_sheet(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得資產負債表失敗: {str(e)}")

    def fetch_income_statement(self, stock_id: str, years: int = 3) -> pd.DataFrame:
        """
        取得損益表

        Args:
            stock_id: 股票代碼
            years: 取得幾年資料

        Returns:
            DataFrame: 損益表資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_financial_statement(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得損益表失敗: {str(e)}")

    def fetch_cash_flow(self, stock_id: str, years: int = 3) -> pd.DataFrame:
        """
        取得現金流量表

        Args:
            stock_id: 股票代碼
            years: 取得幾年資料

        Returns:
            DataFrame: 現金流量表資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_cash_flows_statement(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得現金流量表失敗: {str(e)}")

    def fetch_stock_price(self, stock_id: str, days: int = 30) -> pd.DataFrame:
        """
        取得股價資料

        Args:
            stock_id: 股票代碼
            days: 取得幾天資料

        Returns:
            DataFrame: 股價資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得股價資料失敗: {str(e)}")

    def fetch_stock_price_long(self, stock_id: str, years: int = 1) -> pd.DataFrame:
        """
        取得長期股價資料（用於技術分析）

        Args:
            stock_id: 股票代碼
            years: 取得幾年資料

        Returns:
            DataFrame: 股價資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得長期股價資料失敗: {str(e)}")

    def fetch_month_revenue(self, stock_id: str, years: int = 3) -> pd.DataFrame:
        """
        取得月營收資料

        Args:
            stock_id: 股票代碼
            years: 取得幾年資料

        Returns:
            DataFrame: 月營收資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_month_revenue(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得月營收資料失敗: {str(e)}")

    def fetch_dividend(self, stock_id: str, years: int = 5) -> pd.DataFrame:
        """
        取得股利資料

        Args:
            stock_id: 股票代碼
            years: 取得幾年資料

        Returns:
            DataFrame: 股利資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365 * years)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_dividend(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得股利資料失敗: {str(e)}")

    def fetch_per_pbr(self, stock_id: str, days: int = 30) -> pd.DataFrame:
        """
        取得 PER/PBR 資料

        Args:
            stock_id: 股票代碼
            days: 取得幾天資料

        Returns:
            DataFrame: PER/PBR 資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_per_pbr(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得 PER/PBR 資料失敗: {str(e)}")

    def fetch_institutional_investors(self, stock_id: str, days: int = 30) -> pd.DataFrame:
        """
        取得三大法人買賣超資料

        Args:
            stock_id: 股票代碼
            days: 取得幾天資料

        Returns:
            DataFrame: 法人買賣超資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_institutional_investors(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得法人買賣超資料失敗: {str(e)}")

    def fetch_margin_data(self, stock_id: str, days: int = 30) -> pd.DataFrame:
        """
        取得融資融券資料

        Args:
            stock_id: 股票代碼
            days: 取得幾天資料

        Returns:
            DataFrame: 融資融券資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_margin_purchase_short_sale(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得融資融券資料失敗: {str(e)}")

    def fetch_shareholding(self, stock_id: str, days: int = 30) -> pd.DataFrame:
        """
        取得股權分散資料

        Args:
            stock_id: 股票代碼
            days: 取得幾天資料

        Returns:
            DataFrame: 股權分散資料
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        try:
            data = self.loader.taiwan_stock_shareholding(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            return data
        except Exception as e:
            raise Exception(f"取得股權分散資料失敗: {str(e)}")

    def fetch_market_cap(self, stock_id: str) -> Optional[float]:
        """
        取得市值資料

        Args:
            stock_id: 股票代碼

        Returns:
            float: 市值（億元），如無法取得則返回 None
        """
        try:
            # 取得股價
            price_data = self.fetch_stock_price(stock_id, days=7)
            if price_data.empty:
                print(f"警告：無法取得股價資料")
                return None

            latest_price = price_data.iloc[-1]['close']

            # 取得發行股數（從資產負債表）
            balance_sheet = self.fetch_balance_sheet(stock_id, years=1)
            if balance_sheet.empty:
                print(f"警告：無法取得資產負債表")
                return None

            # 找到最新一季的資料
            latest_date = balance_sheet['date'].max()
            latest_bs = balance_sheet[balance_sheet['date'] == latest_date]

            # 嘗試取得發行股數
            # FinMind 使用 OrdinaryShare（普通股股本，單位：元）
            # 每股面值通常是 10 元，所以發行股數 = OrdinaryShare / 10
            shares = None
            for _, row in latest_bs.iterrows():
                if row['type'] == 'OrdinaryShare':
                    # 普通股股本（元），轉換為股數（除以 10）
                    shares = row['value'] / 10
                    break

            if shares and shares > 0:
                # 轉換為億元（股數 × 股價 / 1億）
                market_cap = latest_price * shares / 100000000
                return market_cap
            else:
                print(f"警告：無法取得發行股數")
                return None

        except Exception as e:
            print(f"取得市值失敗: {str(e)}")
            return None

    def fetch_all_financial_data(self, stock_id: str, years: int = 3) -> Dict:
        """
        取得所有財報資料

        Args:
            stock_id: 股票代碼
            years: 取得幾年資料

        Returns:
            Dict: 包含 balance_sheet, income_statement, cash_flow
        """
        return {
            'balance_sheet': self.fetch_balance_sheet(stock_id, years),
            'income_statement': self.fetch_income_statement(stock_id, years),
            'cash_flow': self.fetch_cash_flow(stock_id, years),
            'stock_id': stock_id
        }

    def standardize_financial_data(self, stock_id: str, years: int = 3) -> List[Dict]:
        """
        取得並標準化財務數據，轉換為分析器需要的格式

        Args:
            stock_id: 股票代碼
            years: 取得幾年資料

        Returns:
            List[Dict]: 標準化後的財務數據列表（按時間排序，最新在前）
        """
        # 取得原始數據
        balance_sheet = self.fetch_balance_sheet(stock_id, years)
        income_statement = self.fetch_income_statement(stock_id, years)
        cash_flow = self.fetch_cash_flow(stock_id, years)

        if balance_sheet.empty or income_statement.empty or cash_flow.empty:
            raise Exception("無法取得完整的財務數據")

        # 取得所有日期並排序（最新在前）
        all_dates = sorted(
            set(balance_sheet['date'].unique()) &
            set(income_statement['date'].unique()) &
            set(cash_flow['date'].unique()),
            reverse=True
        )

        standardized_data = []

        for date in all_dates:
            # 從資產負債表提取數據
            bs_data = balance_sheet[balance_sheet['date'] == date]
            bs_dict = {row['type']: row['value'] for _, row in bs_data.iterrows()}

            # 從損益表提取數據
            is_data = income_statement[income_statement['date'] == date]
            is_dict = {row['type']: row['value'] for _, row in is_data.iterrows()}

            # 從現金流量表提取數據
            cf_data = cash_flow[cash_flow['date'] == date]
            cf_dict = {row['type']: row['value'] for _, row in cf_data.iterrows()}

            # 標準化為分析器需要的格式
            # 處理日期格式（可能是字串或 datetime 物件）
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
                'stockholders_equity': bs_dict.get('Equity', 0),  # 使用權益總額（包含非控制權益）
                'retained_earnings': bs_dict.get('RetainedEarnings', 0),
                'revenue': is_dict.get('Revenue', 0),
                'gross_profit': is_dict.get('GrossProfit', 0),
                'operating_income': is_dict.get('OperatingIncome', 0),
                'net_income': is_dict.get('EquityAttributableToOwnersOfParent', 0),  # 淨利使用歸屬母公司
                'operating_cash_flow': cf_dict.get('NetCashInflowFromOperatingActivities', 0),
                'investing_cash_flow': cf_dict.get('CashProvidedByInvestingActivities', 0),
                'financing_cash_flow': cf_dict.get('CashFlowsProvidedFromFinancingActivities', 0),
                'capex': abs(cf_dict.get('PropertyAndPlantAndEquipment', 0)),
                'weighted_average_shares': 0  # FinMind 沒有直接提供，需要另外計算
            }

            standardized_data.append(standardized)

        return standardized_data
