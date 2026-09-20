"""資料驗證模組 - 驗證財務數據的真實性和完整性"""
from typing import Dict, List
from datetime import datetime


class DataValidator:
    """財務數據驗證器"""

    def validate_financial_data(self, data: List[Dict]) -> Dict:
        """
        驗證財務數據的完整性和合理性

        Args:
            data: 標準化後的財務數據列表

        Returns:
            Dict: 包含驗證結果和警告訊息
        """
        warnings = []
        errors = []

        if not data:
            errors.append("無財務數據")
            return {
                'is_valid': False,
                'errors': errors,
                'warnings': warnings
            }

        # 檢查每個期間的數據
        for period_data in data:
            period = period_data.get('period', '未知')

            # 檢查必填欄位
            required_fields = [
                'total_assets', 'current_assets', 'current_liabilities',
                'total_liabilities', 'stockholders_equity', 'revenue',
                'net_income', 'operating_cash_flow'
            ]

            for field in required_fields:
                if field not in period_data:
                    warnings.append(f"{period}: 缺少 {field}")
                elif period_data[field] is None or period_data[field] == 0:
                    warnings.append(f"{period}: {field} 為 0 或缺失")

            # 檢查資產負債表平衡
            total_assets = period_data.get('total_assets', 0)
            total_liabilities = period_data.get('total_liabilities', 0)
            stockholders_equity = period_data.get('stockholders_equity', 0)

            if total_assets > 0:
                balance_check = total_liabilities + stockholders_equity
                if abs(total_assets - balance_check) / total_assets > 0.01:
                    errors.append(
                        f"{period}: 資產負債表不平衡 "
                        f"(資產: {total_assets:,.0f}, "
                        f"負債+權益: {balance_check:,.0f})"
                    )

            # 檢查數值合理性
            if total_assets < 0:
                errors.append(f"{period}: 總資產為負值")

            if period_data.get('revenue', 0) < 0:
                warnings.append(f"{period}: 營收為負值")

            # 檢查現金流合理性
            operating_cf = period_data.get('operating_cash_flow', 0)
            net_income = period_data.get('net_income', 0)

            if operating_cf != 0 and net_income != 0:
                cash_quality = operating_cf / net_income
                if cash_quality < 0:
                    warnings.append(
                        f"{period}: 營運現金流與淨利方向相反"
                    )

        # 檢查趨勢合理性
        if len(data) >= 2:
            latest = data[0]
            previous = data[1]

            # 檢查資產變化
            asset_change_rate = (
                (latest['total_assets'] - previous['total_assets'])
                / previous['total_assets']
                if previous['total_assets'] > 0 else 0
            )

            if abs(asset_change_rate) > 0.5:
                warnings.append(
                    f"總資產變化過大 ({asset_change_rate:.1%})，請確認數據正確性"
                )

        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def validate_real_data(self, data: List[Dict]) -> bool:
        """
        驗證是否為真實數據（非模擬數據）

        Args:
            data: 財務數據列表

        Returns:
            bool: 是否為真實數據
        """
        if not data:
            return False

        # 檢查是否有模擬數據的特徵
        for period_data in data:
            # 模擬數據通常有整數值
            total_assets = period_data.get('total_assets', 0)

            # 真實數據通常有較複雜的數值
            if total_assets > 0:
                # 檢查是否有小數點或複雜數值
                if isinstance(total_assets, (int, float)):
                    # 真實財報數據通常不是整百萬的倍數
                    if total_assets % 1000000 == 0:
                        # 可能是模擬數據
                        return False

        return True

    def get_data_source_info(self, data: List[Dict]) -> str:
        """
        取得數據來源資訊

        Args:
            data: 財務數據列表

        Returns:
            str: 數據來源描述
        """
        if not data:
            return "無數據"

        periods = [d.get('period', '') for d in data]
        return f"數據期間: {min(periods)} 至 {max(periods)}，共 {len(data)} 期"
