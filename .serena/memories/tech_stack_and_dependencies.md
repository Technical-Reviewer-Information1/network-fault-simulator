# 技術スタックと依存関係

## 言語とランタイム
- **Python 3.11** (Dev Container使用)

## 主要ライブラリ (requirements.txt)
- `streamlit`: Webアプリケーションフレームワーク
- `plotly`: インタラクティブグラフとデータ可視化
- `networkx`: グラフ理論とネットワーク解析
- `pandas`: データフレーム操作
- `numpy`: 数値計算

## 開発環境
- **Dev Container**: Visual Studio Code開発コンテナ
- **Base Image**: `mcr.microsoft.com/devcontainers/python:1-3.11-bullseye`
- **拡張機能**: 
  - ms-python.python
  - ms-python.vscode-pylance

## ポート設定
- **8501**: Streamlitアプリケーションのデフォルトポート
- 自動的にプレビューで開く設定