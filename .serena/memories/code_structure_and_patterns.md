# コード構造とパターン

## ファイル構成
```
/
├── app.py                 # メインアプリケーションファイル
├── requirements.txt       # Python依存関係
├── README.md             # プロジェクト説明（現在は最小限）
└── .devcontainer/        # 開発環境設定
    └── devcontainer.json
```

## コード構造（app.py内）

### クラスとEnum定義
- `DeviceType(Enum)`: router, switch, pc, server
- `DeviceStatus(Enum)`: normal, failed, unknown
- `NetworkDevice(@dataclass)`: ネットワークデバイスの定義
- `PingResult(@dataclass)`: ping結果の格納
- `NetworkSimulator(class)`: メインのシミュレーションロジック

### 主要関数
- `create_network_graph()`: Plotlyを使ったネットワーク図生成
- `main()`: Streamlitアプリのメイン関数

## 設計パターン
- **データクラス活用**: `@dataclass`でイミュータブルなデータ構造
- **Enum活用**: 型安全な定数定義
- **セッション状態管理**: Streamlitの`st.session_state`でアプリ状態保持
- **タブ形式UI**: 機能別に整理されたインターフェース

## コーディング規約
- **Type Hints**: 関数の引数と戻り値に型注釈
- **日本語コメント**: クラスや関数の説明
- **命名規則**: snake_case（Python標準）
- **インポート整理**: 標準ライブラリ → サードパーティ → ローカル