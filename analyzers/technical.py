"""技術分析模組（階段六）"""
from typing import Dict, List
import pandas as pd
from utils import safe_divide


class TechnicalAnalyzer:
    """技術分析器"""

    def analyze(self, price_data: pd.DataFrame) -> Dict:
        """
        執行技術分析

        Args:
            price_data: 日K線資料 DataFrame

        Returns:
            Dict: 分析結果
        """
        if price_data.empty or len(price_data) < 60:
            return {
                'trend': '資料不足',
                'macd': None,
                'rsi': None,
                'kd': None,
                'volume_analysis': None,
                'support_resistance': None,
                'overall_rating': '無法判斷',
                'details': [],
            }

        # 準備資料
        df = price_data.copy()
        df['close'] = df['close'].astype(float)
        df['Trading_Volume'] = df['Trading_Volume'].astype(float)
        df = df.sort_values('date').reset_index(drop=True)

        result = {
            'trend': self._analyze_trend(df),
            'macd': self._calculate_macd(df),
            'rsi': self._calculate_rsi(df),
            'kd': self._calculate_kd(df),
            'bollinger': self._calculate_bollinger(df),
            'volume_analysis': self._analyze_volume(df),
            'support_resistance': self._find_support_resistance(df),
            'overall_rating': '中性',
            'details': [],
        }

        # 綜合評分
        score = 0
        max_score = 0

        # 趨勢評分
        t = result['trend']
        if t['ma_alignment'] == '多頭排列':
            score += 2
        elif t['ma_alignment'] == '空頭排列':
            score -= 1
        max_score += 2

        # MACD 評分
        m = result['macd']
        if m and m.get('signal') == '黃金交叉':
            score += 1
        elif m and m.get('signal') == '死亡交叉':
            score -= 1
        max_score += 1

        # RSI 評分
        r = result['rsi']
        if r:
            if r < 30:
                score += 1  # 超賣，可能反彈
            elif r > 70:
                score -= 1  # 超買，注意風險
            max_score += 1

        # KD 評分
        k = result['kd']
        if k and k.get('signal') == '低檔黃金交叉':
            score += 1
        elif k and k.get('signal') == '高檔死亡交叉':
            score -= 1
        max_score += 1

        # 量價評分
        v = result['volume_analysis']
        if v and v.get('pattern') == '價漲量增':
            score += 1
        elif v and v.get('pattern') == '價漲量縮':
            score -= 0.5
        max_score += 1

        # 布林通道評分
        b = result['bollinger']
        if b:
            if b.get('percent_b') is not None:
                if b['percent_b'] < 0:
                    score += 1  # 超賣
                elif b['percent_b'] > 1:
                    score -= 1  # 超買
                elif b['percent_b'] > 0.5:
                    score += 0.5  # 偏多
                elif b['percent_b'] < 0.5:
                    score -= 0.5  # 偏空
            max_score += 1

        ratio = (score + max_score) / (2 * max_score) if max_score > 0 else 0.5
        if ratio >= 0.65:
            result['overall_rating'] = '多頭'
        elif ratio <= 0.35:
            result['overall_rating'] = '空頭'
        else:
            result['overall_rating'] = '中性'

        return result

    def _analyze_trend(self, df: pd.DataFrame) -> Dict:
        """分析均線趨勢"""
        closes = df['close']

        # 計算均線
        ma5 = closes.rolling(5).mean()
        ma20 = closes.rolling(20).mean()
        ma60 = closes.rolling(60).mean()

        latest = closes.iloc[-1]
        ma5_val = ma5.iloc[-1]
        ma20_val = ma20.iloc[-1]
        ma60_val = ma60.iloc[-1]

        # 判斷排列
        if ma5_val > ma20_val > ma60_val:
            alignment = '多頭排列'
        elif ma5_val < ma20_val < ma60_val:
            alignment = '空頭排列'
        else:
            alignment = '盤整'

        return {
            'ma5': ma5_val,
            'ma20': ma20_val,
            'ma60': ma60_val,
            'ma_alignment': alignment,
            'price_vs_ma5': '站上' if latest > ma5_val else '跌破',
            'price_vs_ma20': '站上' if latest > ma20_val else '跌破',
            'price_vs_ma60': '站上' if latest > ma60_val else '跌破',
        }

    def _calculate_macd(self, df: pd.DataFrame) -> Dict:
        """計算 MACD"""
        closes = df['close']
        ema12 = closes.ewm(span=12, adjust=False).mean()
        ema26 = closes.ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        macd_line = dif.ewm(span=9, adjust=False).mean()
        histogram = dif - macd_line

        latest_dif = dif.iloc[-1]
        latest_macd = macd_line.iloc[-1]
        latest_hist = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2] if len(histogram) > 1 else 0

        # 判斷信號
        if latest_dif > latest_macd and dif.iloc[-2] <= macd_line.iloc[-2]:
            signal = '黃金交叉'
        elif latest_dif < latest_macd and dif.iloc[-2] >= macd_line.iloc[-2]:
            signal = '死亡交叉'
        elif latest_hist > prev_hist:
            signal = '柱狀收斂/多頭'
        else:
            signal = '柱狀收斂/空頭'

        return {
            'dif': latest_dif,
            'macd': latest_macd,
            'histogram': latest_hist,
            'signal': signal,
        }

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """計算 RSI"""
        closes = df['close']
        delta = closes.diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1]

    def _calculate_kd(self, df: pd.DataFrame, n: int = 9) -> Dict:
        """計算 KD 指標"""
        highs = df['max'].astype(float)
        lows = df['min'].astype(float)
        closes = df['close']

        lowest_low = lows.rolling(n).min()
        highest_high = highs.rolling(n).max()

        rsv = (closes - lowest_low) / (highest_high - lowest_low) * 100

        # K 值 = 前一日 K 值 × 2/3 + 當日 RSV × 1/3
        k_values = []
        d_values = []
        k = 50
        d = 50

        for rsv_val in rsv:
            if pd.isna(rsv_val):
                k_values.append(k)
                d_values.append(d)
                continue
            k = k * 2 / 3 + rsv_val * 1 / 3
            d = d * 2 / 3 + k * 1 / 3
            k_values.append(k)
            d_values.append(d)

        latest_k = k_values[-1]
        latest_d = d_values[-1]

        # 判斷信號
        if latest_k > latest_d and k_values[-2] <= d_values[-2]:
            if latest_k < 30:
                signal = '低檔黃金交叉'
            else:
                signal = '黃金交叉'
        elif latest_k < latest_d and k_values[-2] >= d_values[-2]:
            if latest_k > 70:
                signal = '高檔死亡交叉'
            else:
                signal = '死亡交叉'
        else:
            signal = '無明顯信號'

        return {
            'k': latest_k,
            'd': latest_d,
            'signal': signal,
        }

    def _calculate_bollinger(self, df: pd.DataFrame, period: int = 20, num_std: int = 2) -> Dict:
        """計算布林通道"""
        closes = df['close'].astype(float)

        # 計算中軌、上軌、下軌
        middle_band = closes.rolling(period).mean()
        std = closes.rolling(period).std()
        upper_band = middle_band + num_std * std
        lower_band = middle_band - num_std * std

        latest_close = closes.iloc[-1]
        latest_upper = upper_band.iloc[-1]
        latest_middle = middle_band.iloc[-1]
        latest_lower = lower_band.iloc[-1]

        # 計算 %B
        band_width = latest_upper - latest_lower
        percent_b = (latest_close - latest_lower) / band_width if band_width > 0 else 0.5

        # 計算通道寬度
        bandwidth = band_width / latest_middle * 100 if latest_middle > 0 else 0

        # 判斷位置
        if latest_close > latest_upper:
            position = '突破上軌（超買）'
        elif latest_close > latest_middle:
            position = '中軌上方（偏多）'
        elif latest_close > latest_lower:
            position = '中軌下方（偏空）'
        else:
            position = '跌破下軌（超賣）'

        # 判斷通道狀態
        if len(df) >= period * 2:
            prev_bandwidth = bandwidth
            prev_bands = []
            for i in range(-period, 0):
                if i < 0 and abs(i) < len(df):
                    prev_upper = upper_band.iloc[i]
                    prev_lower = lower_band.iloc[i]
                    prev_middle = middle_band.iloc[i]
                    if prev_middle > 0:
                        prev_bw = (prev_upper - prev_lower) / prev_middle * 100
                        prev_bands.append(prev_bw)

            if prev_bands:
                avg_prev_bw = sum(prev_bands) / len(prev_bands)
                if bandwidth < avg_prev_bw * 0.8:
                    band_status = '縮口（波動率降低，即將變盤）'
                elif bandwidth > avg_prev_bw * 1.2:
                    band_status = '開口（波動率增加，趨勢展開）'
                else:
                    band_status = '穩定'
            else:
                band_status = '穩定'
        else:
            band_status = '資料不足'

        # 計算距離上下軌的百分比
        dist_to_upper = (latest_upper - latest_close) / latest_close * 100
        dist_to_lower = (latest_close - latest_lower) / latest_close * 100

        return {
            'upper_band': latest_upper,
            'middle_band': latest_middle,
            'lower_band': latest_lower,
            'percent_b': percent_b,
            'bandwidth': bandwidth,
            'band_status': band_status,
            'position': position,
            'dist_to_upper': dist_to_upper,
            'dist_to_lower': dist_to_lower,
        }

    def _analyze_volume(self, df: pd.DataFrame) -> Dict:
        """分析量價關係"""
        if len(df) < 2:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        price_change = latest['close'] - prev['close']
        volume_change = latest['Trading_Volume'] - prev['Trading_Volume']

        if price_change > 0 and volume_change > 0:
            pattern = '價漲量增'
            assessment = '健康上漲'
        elif price_change > 0 and volume_change < 0:
            pattern = '價漲量縮'
            assessment = '上漲動能不足'
        elif price_change < 0 and volume_change > 0:
            pattern = '價跌量增'
            assessment = '賣壓沉重'
        elif price_change < 0 and volume_change < 0:
            pattern = '價跌量縮'
            assessment = '賣壓減輕'
        else:
            pattern = '平盤'
            assessment = '觀望'

        # 檢查量能異常
        avg_volume = df['Trading_Volume'].tail(20).mean()
        volume_ratio = latest['Trading_Volume'] / avg_volume if avg_volume > 0 else 1

        if volume_ratio > 2:
            assessment += '（量能異常放大）'

        return {
            'pattern': pattern,
            'assessment': assessment,
            'volume_ratio': volume_ratio,
        }

    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """找出支撐與壓力位"""
        if len(df) < 20:
            return None

        recent = df.tail(20)
        latest_close = df['close'].iloc[-1]

        high_20 = recent['max'].astype(float).max()
        low_20 = recent['min'].astype(float).min()

        # 簡單計算支撐壓力
        resistance = high_20
        support = low_20

        # 計算距離
        dist_to_resistance = (resistance - latest_close) / latest_close * 100
        dist_to_support = (latest_close - support) / latest_close * 100

        return {
            'resistance': resistance,
            'support': support,
            'dist_to_resistance': dist_to_resistance,
            'dist_to_support': dist_to_support,
        }
