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
        failed_pings = [p for p in self.ping_history if not p.result]
        if not failed_pings:
            return {"status": "正常", "suggestions": []}
        
        # 失敗した疎通の分析
        affected_devices = set()
        for ping in failed_pings:
            affected_devices.add(ping.source)
            affected_devices.add(ping.destination)
        
        # 故障候補の特定
        candidates = []
        for device in self.devices:
            if device.device_type in [DeviceType.ROUTER, DeviceType.SWITCH]:
                candidates.append(device.name)
        
        suggestions = [
            "コアインフラ機器（ルータ・スイッチ）の確認を推奨",
            "複数のPCで同じ症状が出ている場合は上位機器の故障を疑う",
            "段階的に上位から下位へ疎通確認を実施"
        ]
        
        return {
            "candidates": candidates,
            "suggestions": suggestions,
            "affected_count": len(affected_devices)
        }

def create_network_graph(simulator: NetworkSimulator) -> go.Figure:
    """ネットワーク図の作成"""
    # デバイスアイコンのマッピング
    device_symbols = {
        DeviceType.ROUTER: "diamond",
        DeviceType.SWITCH: "square",
        DeviceType.PC: "circle",
        DeviceType.SERVER: "hexagon"
    }
    
    # ステータス色のマッピング
    status_colors = {
        DeviceStatus.NORMAL: "green",
        DeviceStatus.FAILED: "red",
        DeviceStatus.UNKNOWN: "gray"
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
    
    # デバイスの描画
    for device_type in DeviceType:
        devices_of_type = [d for d in simulator.devices if d.device_type == device_type]
        
        if devices_of_type:
            x_coords = [d.position[0] for d in devices_of_type]
            y_coords = [d.position[1] for d in devices_of_type]
            colors = [status_colors[d.status] for d in devices_of_type]
            names = [d.name for d in devices_of_type]
            ips = [d.ip_address for d in devices_of_type]
            
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode="markers+text",
                marker=dict(
                    symbol=device_symbols[device_type],
                    size=20,
                    color=colors,
                    line=dict(width=2, color="black")
                ),
                text=[f"{name}<br>{ip}" for name, ip in zip(names, ips)],
                textposition="bottom center",
                textfont=dict(color="black"),
                name=device_type.value.title(),
                hovertemplate="<b>%{text}</b><br>状態: %{marker.color}<extra></extra>"
            ))
    
    fig.update_layout(
        title="ネットワーク構成図",
        showlegend=True,
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
            if st.button("診断を実行"):
                diagnosis = simulator.diagnose_failure()
                
                if diagnosis.get("candidates"):
                    st.warning(f"⚠️ 故障の可能性があるデバイス: {len(diagnosis['candidates'])}台")
                    for candidate in diagnosis["candidates"]:
                        st.write(f"• {candidate}")
                
                if diagnosis.get("suggestions"):
                    st.info("💡 推奨アクション:")
                    for suggestion in diagnosis["suggestions"]:
                        st.write(f"• {suggestion}")
                
                if not simulator.ping_history or all(p.result for p in simulator.ping_history):
                    st.success("✅ ネットワークは正常に動作しています")

if __name__ == "__main__":
    main()