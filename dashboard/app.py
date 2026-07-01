import os
import time
import httpx
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="DevOps Dashboard",
    page_icon="🖥️",
    layout="wide"
)

st.title("🖥️ DevOps Monitoring Dashboard")

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "dev-secret-change-in-prod")
HEADERS = {"X-API-Key": API_KEY}


@st.cache_data(ttl=2)
def fetch_metrics() -> dict:
    """Fetches system metrics from the FastAPI backend."""
    try:
        resp = httpx.get(f"{API_BASE}/metrics", timeout=3)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch metrics: {e}")
        return {}


@st.cache_data(ttl=5)
def fetch_servers() -> list:
    """Fetches the list of monitored servers."""
    try:
        resp = httpx.get(f"{API_BASE}/servers", timeout=3)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []


tab1, tab2 = st.tabs(["📊 Metrics", "🖥️ Servers"])

with tab1:
    placeholder = st.empty()

    if "cpu_history" not in st.session_state:
        st.session_state.cpu_history = []

    # Stream metrics inside tab loop
    metrics = fetch_metrics()
    if metrics:
        st.session_state.cpu_history.append({
            "time": pd.Timestamp.now(),
            "cpu": metrics.get("cpu_percent", 0),
            "memory": metrics.get("memory_percent", 0),
            "disk": metrics.get("disk_percent", 0),
        })

    # Keep last 60 samples
    history = st.session_state.cpu_history[-60:]
    df = pd.DataFrame(history)

    with placeholder.container():
        col1, col2, col3 = st.columns(3)
        col1.metric("CPU Usage", f"{metrics.get('cpu_percent', 0):.1f} %")
        col2.metric("Memory Usage", f"{metrics.get('memory_percent', 0):.1f} %")
        col3.metric("Disk Usage", f"{metrics.get('disk_percent', 0):.1f} %")

        if not df.empty:
            st.subheader("CPU & Memory — Last 60 Samples")
            st.line_chart(df.set_index("time")[["cpu", "memory"]])

with tab2:
    st.subheader("Monitored Servers")
    servers = fetch_servers()

    if servers:
        df_servers = pd.DataFrame(servers)

        def colour_status(row):
            if row["status"] == "UP":
                return ["background-color: #d4edda"] * len(row)
            elif row["status"] == "DEGRADED":
                return ["background-color: #fff3cd"] * len(row)
            else:
                return ["background-color: #f8d7da"] * len(row)

        st.dataframe(
            df_servers.style.apply(colour_status, axis=1),
            use_container_width=True
        )
    else:
        st.info("No servers monitored.")

    col1, col2 = st.columns(2)

    with col1:
        with st.form("register_server"):
            st.subheader("Register a Server")
            name = st.text_input("Name", placeholder="api-prod-1")
            host = st.text_input("Host", placeholder="httpbin.dmuth.org")
            port = st.number_input("Port", min_value=1, max_value=65535, value=443)
            health_path = st.text_input("Health Path", value="/status/200")
            submitted = st.form_submit_button("Register")

        if submitted:
            if not name or not host:
                st.error("Name and host are required.")
            else:
                try:
                    resp = httpx.post(
                        f"{API_BASE}/servers",
                        json={"name": name, "host": host, "port": port, "health_path": health_path},
                        headers=HEADERS,
                        timeout=5
                    )
                    resp.raise_for_status()
                    st.success(f"✅ Registered {name} successfully.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to register server: {e}")

    with col2:
        st.subheader("Actions")
        if servers:
            server_options = {s["id"]: f"{s['name']} ({s['host']}:{s['port']})" for s in servers}
            selected_id = st.selectbox(
                "Select Server",
                list(server_options.keys()),
                format_func=lambda x: server_options[x]
            )

            if st.button("Trigger Immediate Check"):
                try:
                    resp = httpx.post(f"{API_BASE}/servers/{selected_id}/check", timeout=5)
                    resp.raise_for_status()
                    st.success(f"Check finished: Server is {resp.json().get('status')}")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to trigger check: {e}")

            if st.button("Delete Server"):
                try:
                    resp = httpx.delete(f"{API_BASE}/servers/{selected_id}", headers=HEADERS, timeout=5)
                    resp.raise_for_status()
                    st.success("Removed server successfully.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete server: {e}")

time.sleep(2)
st.rerun()
