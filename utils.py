"""共用工具函數"""


def safe_divide(numerator, denominator, default=0):
    """安全除法，避免除以零"""
    if denominator == 0 or denominator is None:
        return default
    return numerator / denominator


def format_number(value, decimals=2):
    """格式化數字顯示"""
    if value is None:
        return 'N/A'
    return f'{value:,.{decimals}f}'


def format_percentage(value, decimals=2):
    """格式化百分比顯示"""
    if value is None:
        return 'N/A'
    return f'{value * 100:.{decimals}f}%'
