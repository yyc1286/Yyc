import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pathlib import Path
import unicodedata
import io

# =========================
# Streamlit 기본 설정
# =========================
st.set_page_config(
    page_title="🌱 극지식물 최적 EC 농도 연구",
    layout="wide"
)

# =========================
# 한글 폰트 깨짐 방지 (UI)
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 유틸: 한글 파일 탐색 (NFC/NFD 대응)
# =========================
def find_file(data_dir: Path, target_name: str):
    target_nfc = unicodedata.normalize("NFC", target_name)
    target_nfd = unicodedata.normalize("NFD", target_name)

    for p in data_dir.iterdir():
        name_nfc = unicodedata.normalize("NFC", p.name)
        name_nfd = unicodedata.normalize("NFD", p.name)
        if name_nfc == target_nfc or name_nfd == target_nfd:
            return p
    return None

# =========================
# 데이터 로딩
# =========================
@st.cache_data
def load_env_data():
    data_dir = Path("data")
    school_files = {
        "송도고": "송도고_환경데이터.csv",
        "하늘고": "하늘고_환경데이터.csv",
        "아라고": "아라고_환경데이터.csv",
        "동산고": "동산고_환경데이터.csv",
    }

    dfs = {}
    for school, fname in school_files.items():
        file_path = find_file(data_dir, fname)
        if file_path is None:
            st.error(f"❌ {school} 환경 데이터 파일을 찾을 수 없습니다.")
            continue
        df = pd.read_csv(file_path)
        df["school"] = school
        dfs[school] = df
    return dfs

@st.cache_data
def load_growth_data():
    data_dir = Path("data")
    xlsx_path = find_file(data_dir, "4개교_생육결과데이터.xlsx")
    if xlsx_path is None:
        st.error("❌ 생육 결과 XLSX 파일을 찾을 수 없습니다.")
        return {}

    xls = pd.ExcelFile(xlsx_path)
    data = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df["school"] = sheet
        data[sheet] = df
    return data

# =========================
# 데이터 로딩 실행
# =========================
with st.spinner("📂 데이터 불러오는 중..."):
    env_data = load_env_data()
    growth_data = load_growth_data()

if not env_data or not growth_data:
    st.stop()

# =========================
# 기본 정보
# =========================
EC_SETTING = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

COLOR_MAP = {
    "송도고": "blue",
    "하늘고": "green",
    "아라고": "orange",
    "동산고": "red",
}

# =========================
# Sidebar
# =========================
st.sidebar.title("🏫 학교 선택")
selected_school = st.sidebar.selectbox(
    "학교",
    ["전체", "송도고", "하늘고", "아라고", "동산고"]
)

# =========================
# Tabs
# =========================
tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# =====================================================
# TAB 1: 실험 개요
# =====================================================
with tab1:
    st.markdown("## 🌱 연구 배경 및 목적")
    st.write(
        "본 연구는 EC 농도 차이에 따른 극지식물의 생육 반응을 분석하고, "
        "예측 모델을 통해 생중량이 최대가 되는 최적 환경 조건을 도출하는 것을 목표로 한다."
    )

    summary = []
    total_plants = 0
    for school, df in growth_data.items():
        n = len(df)
        total_plants += n
        summary.append([school, EC_SETTING[school], n, COLOR_MAP[school]])

    summary_df = pd.DataFrame(
        summary, columns=["School", "EC Setting", "Plant Count", "Color"]
    )
    st.dataframe(summary_df, use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Plants", total_plants)
    col2.metric("Avg Temperature (°C)", round(
        pd.concat(env_data.values())["temperature"].mean(), 2))
    col3.metric("Avg Humidity (%)", round(
        pd.concat(env_data.values())["humidity"].mean(), 2))
    col4.metric("Optimal EC", "2.0")

# =====================================================
# TAB 2: 환경 데이터
# =====================================================
with tab2:
    st.markdown("## 🌡️ 학교별 환경 평균 비교")

    env_all = pd.concat(env_data.values())
    avg_env = env_all.groupby("school").mean(numeric_only=True).reset_index()

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Average Temperature",
            "Average Humidity",
            "Average pH",
            "Target EC vs Measured EC"
        ]
    )

    fig.add_trace(go.Bar(
        x=avg_env["school"], y=avg_env["temperature"],
        marker_color=[COLOR_MAP[s] for s in avg_env["school"]],
        name="Temperature"
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=avg_env["school"], y=avg_env["humidity"],
        marker_color=[COLOR_MAP[s] for s in avg_env["school"]],
        name="Humidity"
    ), row=1, col=2)

    fig.add_trace(go.Bar(
        x=avg_env["school"], y=avg_env["ph"],
        marker_color=[COLOR_MAP[s] for s in avg_env["school"]],
        name="pH"
    ), row=2, col=1)

    fig.add_trace(go.Bar(
        x=avg_env["school"],
        y=[EC_SETTING[s] for s in avg_env["school"]],
        name="Target EC"
    ), row=2, col=2)

    fig.add_trace(go.Bar(
        x=avg_env["school"], y=avg_env["ec"],
        name="Measured EC"
    ), row=2, col=2)

    fig.update_layout(
        height=700,
        showlegend=True,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# TAB 3: 생육 결과
# =====================================================
with tab3:
    st.markdown("## 📊 EC별 생육 결과 분석")

    growth_all = pd.concat(growth_data.values())
    mean_weight = growth_all.groupby("school")["생중량(g)"].mean()

    best_school = mean_weight.idxmax()

    cols = st.columns(4)
    for i, (school, val) in enumerate(mean_weight.items()):
        cols[i].metric(
            f"{school} Avg Fresh Weight",
            round(val, 2),
            delta="⭐ Optimal" if school == best_school else ""
        )

    fig = px.box(
        growth_all,
        x="school",
        y="생중량(g)",
        color="school",
        color_discrete_map=COLOR_MAP,
        title="Fresh Weight Distribution by School"
    )
    fig.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🔍 Correlation Analysis")

    fig2 = px.scatter(
        growth_all,
        x="잎 수(장)",
        y="생중량(g)",
        color="school",
        title="Leaf Count vs Fresh Weight"
    )
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.scatter(
        growth_all,
        x="지상부 길이(mm)",
        y="생중량(g)",
        color="school",
        title="Shoot Length vs Fresh Weight"
    )
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📥 생육 데이터 다운로드"):
        buffer = io.BytesIO()
        growth_all.to_excel(buffer, index=False, engine="openpyxl")
        buffer.seek(0)
        st.download_button(
            data=buffer,
            file_name="growth_data_all.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
