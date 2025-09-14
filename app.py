import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
import random
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum

# ページ設定
st.set_page_config(
    page_title="ネットワークの通信障害",
    page_icon="🌐",
    layout="wide"
)

class DeviceType(Enum):
    ROUTER = "router"
    SWITCH = "switch"
    PC = "pc"
    SERVER = "server"

class DeviceStatus(Enum):
    NORMAL = "normal"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class NetworkDevice:
    id: str
    name: str
    ip_address: str
    device_type: DeviceType
    status: DeviceStatus
    position: Tuple[float, float]

@dataclass
class PingResult:
    timestamp: str
    source: str
    destination: str
    result: bool
    response_time: Optional[float] = None

class NetworkSimulator:
    def __init__(self):
        self.devices = self._create_sample_network()
        self.connections = self._create_connections()
        self.ping_history = []
        
    def _create_sample_network(self) -> List[NetworkDevice]:
        """サンプルネットワークの作成"""
        devices = [
            NetworkDevice("R1", "メインルータ", "192.168.1.1", DeviceType.ROUTER, DeviceStatus.NORMAL, (0, 0)),
            NetworkDevice("SW1", "コアスイッチ", "192.168.1.2", DeviceType.SWITCH, DeviceStatus.NORMAL, (-2, -2)),
            NetworkDevice("SW2", "フロアスイッチA", "192.168.1.3", DeviceType.SWITCH, DeviceStatus.NORMAL, (2, -2)),
            NetworkDevice("PC1", "営業部PC1", "192.168.1.10", DeviceType.PC, DeviceStatus.NORMAL, (-3, -4)),
            NetworkDevice("PC2", "営業部PC2", "192.168.1.11", DeviceType.PC, DeviceStatus.NORMAL, (-1, -4)),
            NetworkDevice("PC3", "開発部PC1", "192.168.1.20", DeviceType.PC, DeviceStatus.NORMAL, (1, -4)),
            NetworkDevice("PC4", "開発部PC2", "192.168.1.21", DeviceType.PC, DeviceStatus.NORMAL, (3, -4)),
            NetworkDevice("SRV1", "ファイルサーバ", "192.168.1.100", DeviceType.SERVER, DeviceStatus.NORMAL, (0, -6)),
        ]
        return devices
    
    def _create_connections(self) -> List[Tuple[str, str]]:
        """ネットワーク接続の定義"""
        return [
            ("R1", "SW1"),
            ("R1", "SW2"),
            ("SW1", "PC1"),
            ("SW1", "PC2"),
            ("SW2", "PC3"),
            ("SW2", "PC4"),
            ("SW1", "SRV1"),
        ]
    
    def get_device_by_id(self, device_id: str) -> Optional[NetworkDevice]:
        """デバイスIDからデバイスを取得"""
        for device in self.devices:
            if device.id == device_id:
                return device
        return None
    
    def simulate_ping(self, source_id: str, destination_id: str) -> PingResult:
        """ping疎通をシミュレート"""
        source = self.get_device_by_id(source_id)
        destination = self.get_device_by_id(destination_id)
        
        if not source or not destination:
            return PingResult(
                timestamp=time.strftime("%H:%M:%S"),
                source=source_id,
                destination=destination_id,
                result=False
            )
        
        # 故障デバイスがある場合の疎通判定
        path = self._find_path(source_id, destination_id)
        success = True
        response_time = None
        
        for device_id in path:
            device = self.get_device_by_id(device_id)
            if device and device.status == DeviceStatus.FAILED:
                success = False
                break
        
        if success:
            response_time = random.uniform(1.0, 10.0)
        
        result = PingResult(
            timestamp=time.strftime("%H:%M:%S"),
            source=source.name,
            destination=destination.name,
            result=success,
            response_time=response_time
        )
        
        self.ping_history.append(result)
        return result
    
    def _find_path(self, source_id: str, destination_id: str) -> List[str]:
        """2つのデバイス間の経路を取得"""
        G = nx.Graph()
        for device in self.devices:
            G.add_node(device.id)
        for src, dst in self.connections:
            G.add_edge(src, dst)
        
        try:
            path = nx.shortest_path(G, source_id, destination_id)
            return path
        except nx.NetworkXNoPath:
            return []
    
    def set_device_status(self, device_id: str, status: DeviceStatus):
        """デバイスの状態を設定"""
        device = self.get_device_by_id(device_id)
        if device:
            device.status = status
    
    def diagnose_failure(self) -> Dict[str, List[str]]:
        """故障診断ロジック"""
        # 故障中のデバイスを確認
        failed_devices = [d for d in self.devices if d.status == DeviceStatus.FAILED]
        
        # ping履歴から失敗した疎通を確認
        failed_pings = [p for p in self.ping_history if not p.result]
        
        # 故障デバイスがある場合
        if failed_devices:
            candidates = []
            suggestions = []
            
            # 故障デバイスの種類による分析
            failed_infrastructure = [d for d in failed_devices if d.device_type in [DeviceType.ROUTER, DeviceType.SWITCH]]
            failed_endpoints = [d for d in failed_devices if d.device_type in [DeviceType.PC, DeviceType.SERVER]]
            
            if failed_infrastructure:
                candidates.extend([d.name for d in failed_infrastructure])
                suggestions.append("⚠️ インフラ機器（ルータ・スイッチ）の故障を検出")
                suggestions.append("影響範囲が広い可能性があります")
                suggestions.append("早急に機器の交換または修理を実施してください")
            
            if failed_endpoints:
                candidates.extend([d.name for d in failed_endpoints])
                suggestions.append("エンドポイント機器（PC・サーバ）の故障を検出")
                suggestions.append("個別機器の問題として対応してください")
            
            # ping失敗がある場合の追加情報
            if failed_pings:
                affected_devices = set()
                for ping in failed_pings:
                    affected_devices.add(ping.source)
                    affected_devices.add(ping.destination)
                suggestions.append(f"疎通失敗が確認されています（影響機器数: {len(affected_devices)}台）")
            else:
                suggestions.append("故障機器が検出されていますが、まだ疎通テストが実行されていません")
                suggestions.append("疎通確認を実施して影響範囲を特定してください")
            
            return {
                "candidates": candidates,
                "suggestions": suggestions,
                "affected_count": len(failed_devices),
                "status": "failure_detected"
            }
        
        # 故障デバイスはないが、ping失敗がある場合
        elif failed_pings:
            affected_devices = set()
            for ping in failed_pings:
                affected_devices.add(ping.source)
                affected_devices.add(ping.destination)
            
            # すべてのインフラ機器を候補として挙げる
            candidates = []
            for device in self.devices:
                if device.device_type in [DeviceType.ROUTER, DeviceType.SWITCH]:
                    candidates.append(device.name)
            
            suggestions = [
                "疎通失敗が検出されましたが、故障機器が特定されていません",
                "コアインフラ機器（ルータ・スイッチ）の確認を推奨",
                "複数のPCで同じ症状が出ている場合は上位機器の故障を疑う",
                "段階的に上位から下位へ疎通確認を実施"
            ]
            
            return {
                "candidates": candidates,
                "suggestions": suggestions,
                "affected_count": len(affected_devices),
                "status": "ping_failures"
            }
        
        # 故障デバイスもping失敗もない場合
        else:
            return {
                "status": "normal", 
                "suggestions": [],
                "candidates": [],
                "affected_count": 0
            }

def create_network_graph(simulator: NetworkSimulator) -> go.Figure:
    """ネットワーク図の作成"""
    # デバイスアイコンのマッピング（文字列キーを使用）
    device_symbols = {
        "router": "diamond",
        "switch": "square", 
        "pc": "circle",
        "server": "hexagon"
    }
    
    # ステータス色のマッピング（文字列キーを使用）
    status_colors = {
        "normal": "green",
        "failed": "red",
        "unknown": "gray"
    }
    
    fig = go.Figure()
    
    # 接続線の描画
    for src_id, dst_id in simulator.connections:
        src_device = simulator.get_device_by_id(src_id)
        dst_device = simulator.get_device_by_id(dst_id)
        
        if src_device and dst_device:
            fig.add_trace(go.Scatter(
                x=[src_device.position[0], dst_device.position[0]],
                y=[src_device.position[1], dst_device.position[1]],
                mode="lines",
                line=dict(color="lightgray", width=2),
                showlegend=False,
                hoverinfo="skip"
            ))
    
    # 全デバイスの座標とプロパティを準備
    x_coords = []
    y_coords = []
    symbols = []
    colors = []
    texts = []
    names = []
    
    for device in simulator.devices:
        x_coords.append(device.position[0])
        y_coords.append(device.position[1])
        symbols.append(device_symbols[device.device_type.value])
        colors.append(status_colors[device.status.value])
        texts.append(f"{device.name}<br>{device.ip_address}")
        names.append(device.device_type.value.title())
    
    # すべてのデバイスを一つのトレースで描画
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode="markers+text",
        marker=dict(
            symbol=symbols,
            size=20,
            color=colors,
            line=dict(width=2, color="black")
        ),
        text=texts,
        textposition="bottom center",
        textfont=dict(color="black"),
        name="Network Devices",
        hovertemplate="<b>%{text}</b><br>状態: %{marker.color}<extra></extra>",
        showlegend=False
    ))
    
    fig.update_layout(
        title="ネットワーク構成図",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="white",
        height=500
    )
    
    return fig

def main():
    st.title("ネットワークの通信障害（pp.112-114）")
    
    # セッション状態の初期化
    if "simulator" not in st.session_state:
        st.session_state.simulator = NetworkSimulator()
    if "last_action" not in st.session_state:
        st.session_state.last_action = None
    
    simulator = st.session_state.simulator
    
    # ネットワーク構成図を常に表示
    st.subheader("📊 ネットワーク構成図")
    network_fig = create_network_graph(simulator)
    st.plotly_chart(network_fig, use_container_width=True)
    
    # 凡例をカラムで整理
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **状態表示:**
        - 🟢 緑：正常
        - 🔴 赤：故障
        - ⚫ グレー：不明
        """)

    with col2:
        st.markdown("""
        **デバイス種別:**
        - ◆ ダイヤモンド：ルータ
        - ■ 四角：スイッチ
        - ● 円：PC
        - ⬡ 六角形：サーバ
        """)
    
    # 疎通確認と診断のタブを構成図の下に配置
    tab1, tab2 = st.tabs(["🔍 疎通確認", "⚙️ 設定・診断"])
    
    with tab1:
        st.subheader("🔍 疎通確認")
        
        col1, col2 = st.columns(2)
        
        with col1:
            device_list = [(d.id, f"{d.name} ({d.ip_address})") for d in simulator.devices]
            
            source_device = st.selectbox(
                "送信元デバイス",
                options=[d[0] for d in device_list],
                format_func=lambda x: next(d[1] for d in device_list if d[0] == x)
            )
            
            destination_device = st.selectbox(
                "送信先デバイス",
                options=[d[0] for d in device_list],
                format_func=lambda x: next(d[1] for d in device_list if d[0] == x)
            )
        
        with col2:
            if st.button("🚀 Ping実行", type="primary", key="ping_execute"):
                if source_device != destination_device:
                    with st.spinner("疎通確認中..."):
                        time.sleep(1)  # リアルな感じのための待機
                        result = simulator.simulate_ping(source_device, destination_device)
                    
                    # 結果をセッション状態に保存
                    if "ping_result" not in st.session_state:
                        st.session_state.ping_result = None
                    
                    st.session_state.ping_result = result
                    st.rerun()
                else:
                    st.warning("送信元と送信先は異なるデバイスを選択してください")
            
            # Ping結果の表示
            if "ping_result" in st.session_state and st.session_state.ping_result:
                result = st.session_state.ping_result
                if result.result:
                    st.success(f"✅ 疎通成功 ({result.response_time:.1f}ms)")
                else:
                    st.error("❌ 疎通失敗")
        
        # 疎通履歴
        st.subheader("📋 疎通確認履歴")
        if simulator.ping_history:
            history_df = pd.DataFrame([
                {
                    "時刻": p.timestamp,
                    "送信元": p.source,
                    "送信先": p.destination,
                    "結果": "✅ 成功" if p.result else "❌ 失敗",
                    "応答時間": f"{p.response_time:.1f}ms" if p.response_time else "-"
                }
                for p in simulator.ping_history[-10:]  # 最新10件
            ])
            st.dataframe(history_df, use_container_width=True)
        else:
            st.info("疎通確認の履歴がありません")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⚙️ 故障シミュレーション")
            device_options = [f"{d.id}: {d.name}" for d in simulator.devices]
            selected_device = st.selectbox("故障させるデバイス", ["なし"] + device_options)
            
            if selected_device != "なし":
                device_id = selected_device.split(":")[0]
                if st.button("故障状態に設定", key=f"fail_{device_id}"):
                    simulator.set_device_status(device_id, DeviceStatus.FAILED)
                    st.session_state.last_action = f"{selected_device} を故障状態に設定"
                    st.rerun()
            
            if st.button("全デバイスを正常状態にリセット", key="reset_all"):
                for device in simulator.devices:
                    device.status = DeviceStatus.NORMAL
                simulator.ping_history = []
                # 関連するセッションステートもクリア
                if "ping_result" in st.session_state:
                    del st.session_state.ping_result
                if "diagnosis_result" in st.session_state:
                    del st.session_state.diagnosis_result
                st.session_state.last_action = "全デバイスをリセット"
                st.rerun()
            
            # 最後のアクションを表示
            if st.session_state.last_action:
                st.success(f"✅ {st.session_state.last_action}")
                # 一定時間後にメッセージをクリア
                if st.button("メッセージをクリア", key="clear_msg"):
                    st.session_state.last_action = None
                    st.rerun()
        
        with col2:
            st.subheader("🔧 故障診断")
            if st.button("診断を実行", key="diagnose_button"):
                diagnosis = simulator.diagnose_failure()
                st.session_state.diagnosis_result = diagnosis

            # デバッグ情報を常に表示
            failed_devices = [f"{d.name}({d.status.value})" for d in simulator.devices if d.status.value != "normal"]
            st.write("DEBUG: 故障デバイス:", failed_devices)
            st.write("DEBUG: ping履歴数:", len(simulator.ping_history))
            if "diagnosis_result" in st.session_state:
                st.write("DEBUG: 診断結果:", st.session_state.diagnosis_result)

            # 診断結果の表示（セッションステートから）
            if "diagnosis_result" in st.session_state and st.session_state.diagnosis_result:
                diagnosis = st.session_state.diagnosis_result

                # 診断ステータスに応じた表示
                if diagnosis.get("status") == "failure_detected":
                    st.error("🚨 故障デバイスが検出されました")
                elif diagnosis.get("status") == "ping_failures":
                    st.warning("⚠️ 疎通失敗が検出されました")
                elif diagnosis.get("status") == "normal":
                    st.success("✅ ネットワークは正常に動作しています")

                if diagnosis.get("candidates"):
                    st.warning(f"⚠️ 故障の可能性があるデバイス: {len(diagnosis['candidates'])}台")
                    for candidate in diagnosis["candidates"]:
                        st.write(f"• {candidate}")

                if diagnosis.get("suggestions"):
                    st.info("💡 推奨アクション:")
                    for suggestion in diagnosis["suggestions"]:
                        st.write(f"• {suggestion}")

            # リセット時に診断結果もクリア
            if st.button("診断結果をクリア", key="clear_diagnosis"):
                if "diagnosis_result" in st.session_state:
                    del st.session_state.diagnosis_result
                st.rerun()

if __name__ == "__main__":
    main()