---
title: Stock Analyzer
emoji: 📊
colorFrom: red
colorTo: blue
sdk: streamlit
sdk_version: "1.41.0"
app_file: app.py
pinned: false
---

# 台股財報分析工具

自動化的台股七階段財務分析工具。

## 功能

- Piotroski F-Score（滿分 9 分）
- Altman Z-Score（破產風險評估）
- 杜邦分析（ROE 因子分解）
- 現金流量分析
- 質化與成長性分析
- 技術分析（均線/MACD/RSI/KD/布林通道）
- 籌碼面分析（法人/融資融券/股權分散）
- 估值分析（PE/PB/PEG/DCF）
- 機構目標價

## 資料來源

使用 FinMind API 取得真實財報數據。
