# 推奨コマンド

## アプリケーション実行
```bash
# メインアプリケーションの起動
streamlit run app.py

# CORS設定付きでの起動（Dev Container内では自動実行）
streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false
```

## 依存関係管理
```bash
# 依存関係のインストール
pip install -r requirements.txt

# 個別パッケージのインストール
pip install streamlit plotly networkx pandas numpy
```

## 開発用コマンド
```bash
# Pythonファイルの構文チェック
python -m py_compile app.py

# 型チェック（pylanceが利用可能な場合）
# IDE内で自動実行される

# ファイル一覧表示
ls -la

# プロジェクト構造表示
tree . -I '__pycache__|.git'
```

## Git操作
```bash
# 現在の状態確認
git status

# 変更の追加とコミット
git add .
git commit -m "コミットメッセージ"

# ログ確認
git log --oneline
```

## Dev Container
- **自動起動**: コンテナ開始時にStreamlitアプリが自動で起動
- **ポート**: 8501でアクセス可能
- **自動フォワード**: ブラウザプレビューが自動で開く