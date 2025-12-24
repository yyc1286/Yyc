import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# 페이지 설정
st.set_page_config(
    page_title="극지식물 EC 농도 연구",
    page_icon="🌱",
    layout="wide"
)

# 한글 폰트 설정
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# 학교별 EC 설정
SCHOOL_EC = {
    "송도고": {"ec": 1.0, "color": "#4A90E2"},
    "하늘고": {"ec": 2.0, "color": "#50C878"},
    "아라고": {"ec": 4.0, "color": "#FFB347"},
    "동산고": {"ec": 8.0, "color": "#FF6B6B"}
}

@st.cache_data
def load_environment_data():
    """환경 데이터 로딩 (NFC/NFD 정규화 적용)"""
    data_dir = Path("data")
    env_data = {}
    
    if not data_dir.exists():
        st.error("data 폴더를 찾을 수 없습니다!")
        return None
    
    # CSV 파일 찾기
    csv_files = list(data_dir.glob("*환경데이터.csv"))
    
    for file_path in csv_files:
        # NFC/NFD 양방향 정규화로 학교명 추출
        filename = file_path.stem
        filename_nfc = unicodedata.normalize("NFC", filename)
        filename_nfd = unicodedata.normalize("NFD", filename)
        
        for school in SCHOOL_EC.keys():
            school_nfc = unicodedata.normalize("NFC", school)
            school_nfd = unicodedata.normalize("NFD", school)
            
            if school_nfc in filename_nfc or school_nfd in filename_nfd:
                try:
                    df = pd.read_csv(file_path)
                    env_data[school] = df
                    break
                except Exception as e:
                    st.error(f"{file_path.name} 로딩 실패: {e}")
    
    return env_data if env_data else None

@st.cache_data
def load_growth_data():
    """생육 결과 데이터 로딩"""
    data_dir = Path("data")
    
    # XLSX 파일 찾기
    xlsx_files = list(data_dir.glob("*생육결과데이터.xlsx"))
    
    if not xlsx_files:
        st.error("생육결과 XLSX 파일을 찾을 수 없습니다!")
        return None
    
    try:
        excel_file = pd.ExcelFile(xlsx_files[0])
        growth_data = {}
        
        for sheet_name in excel_file.sheet_names:
            sheet_nfc = unicodedata.normalize("NFC", sheet_name)
            sheet_nfd = unicodedata.normalize("NFD", sheet_name)
            
            for school in SCHOOL_EC.keys():
                school_nfc = unicodedata.normalize("NFC", school)
                school_nfd = unicodedata.normalize("NFD", school)
                
                if school_nfc in sheet_nfc or school_nfd in sheet_nfd:
                    df = pd.read_excel(xlsx_files[0], sheet_name=sheet_name)
                    growth_data[school] = df
                    break
        
        return growth_data if growth_data else None
    except Exception as e:
        st.error(f"생육 데이터 로딩 실패: {e}")
        return None

# 데이터 로딩
with st.spinner("데이터를 불러오는 중..."):
    env_data = load_environment_data()
    growth_data = load_growth_data()

if env_data is None or growth_data is None:
    st.error("필요한 데이터 파일을 찾을 수 없습니다. data 폴더와 파일을 확인해주세요.")
    st.stop()

# 타이틀
st.title("🌱 극지식물 최적 EC 농도 연구")

# 사이드바
st.sidebar.header("필터 설정")
schools = ["전체"] + list(SCHOOL_EC.keys())
selected_school = st.sidebar.selectbox("학교 선택", schools)

# 탭 생성
tab1, tab2, tab3 = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# Tab 1: 실험 개요
with tab1:
    st.header("연구 배경 및 목적")
    st.markdown("""
    본 연구는 극지식물(틸란드시아)의 최적 생육 조건을 찾기 위해 **EC(전기전도도) 농도**에 따른 
    생육 반응을 분석합니다.
    
    - **목표**: EC 농도별 생중량, 잎 수, 길이 등을 비교하여 최적 EC 조건 도출
    - **대상**: 4개 고등학교에서 서로 다른 EC 조건으로 재배
    - **기간**: 장기 환경 모니터링 및 최종 생육 측정
    """)
    
    st.subheader("학교별 EC 조건")
    
    # EC 조건 표
    ec_df = pd.DataFrame([
        {"학교": school, "목표 EC": f"{info['ec']} dS/m", 
         "개체수": len(growth_data[school]), "색상": info['color']}
        for school, info in SCHOOL_EC.items()
    ])
    
    st.dataframe(ec_df, hide_index=True, use_container_width=True)
    
    # 주요 지표 카드
    st.subheader("주요 지표")
    col1, col2, col3, col4 = st.columns(4)
    
    total_plants = sum(len(df) for df in growth_data.values())
    avg_temp = sum(env_data[s]['temperature'].mean() for s in env_data) / len(env_data)
    avg_humidity = sum(env_data[s]['humidity'].mean() for s in env_data) / len(env_data)
    
    # 최적 EC 찾기 (평균 생중량 기준)
    avg_weights = {school: growth_data[school]['생중량(g)'].mean() 
                   for school in SCHOOL_EC.keys()}
    optimal_school = max(avg_weights, key=avg_weights.get)
    optimal_ec = SCHOOL_EC[optimal_school]['ec']
    
    col1.metric("총 개체수", f"{total_plants}개")
    col2.metric("평균 온도", f"{avg_temp:.1f}°C")
    col3.metric("평균 습도", f"{avg_humidity:.1f}%")
    col4.metric("최적 EC", f"{optimal_ec} dS/m", delta=f"{optimal_school}")

# Tab 2: 환경 데이터
with tab2:
    st.header("환경 데이터 분석")
    
    # 학교별 환경 평균 비교
    st.subheader("학교별 환경 평균 비교")
    
    env_summary = pd.DataFrame({
        school: {
            '평균 온도': env_data[school]['temperature'].mean(),
            '평균 습도': env_data[school]['humidity'].mean(),
            '평균 pH': env_data[school]['ph'].mean(),
            '평균 EC': env_data[school]['ec'].mean(),
            '목표 EC': SCHOOL_EC[school]['ec']
        }
        for school in SCHOOL_EC.keys()
    }).T
    
    # 2x2 서브플롯 생성
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("평균 온도 (°C)", "평균 습도 (%)", "평균 pH", "목표 EC vs 실측 EC"),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    schools_list = list(SCHOOL_EC.keys())
    colors = [SCHOOL_EC[s]['color'] for s in schools_list]
    
    # 온도
    fig.add_trace(
        go.Bar(x=schools_list, y=env_summary['평균 온도'], 
               marker_color=colors, name="온도", showlegend=False),
        row=1, col=1
    )
    
    # 습도
    fig.add_trace(
        go.Bar(x=schools_list, y=env_summary['평균 습도'], 
               marker_color=colors, name="습도", showlegend=False),
        row=1, col=2
    )
    
    # pH
    fig.add_trace(
        go.Bar(x=schools_list, y=env_summary['평균 pH'], 
               marker_color=colors, name="pH", showlegend=False),
        row=2, col=1
    )
    
    # EC 비교
    fig.add_trace(
        go.Bar(x=schools_list, y=env_summary['목표 EC'], 
               name="목표 EC", marker_color="lightgray"),
        row=2, col=2
    )
    fig.add_trace(
        go.Bar(x=schools_list, y=env_summary['평균 EC'], 
               name="실측 EC", marker_color=colors),
        row=2, col=2
    )
    
    fig.update_layout(
        height=600,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 선택한 학교 시계열
    if selected_school != "전체":
        st.subheader(f"{selected_school} 환경 시계열")
        
        school_env = env_data[selected_school].copy()
        
        # 3개 꺾은선 그래프
        fig_ts = make_subplots(
            rows=3, cols=1,
            subplot_titles=("온도 변화", "습도 변화", "EC 변화"),
            vertical_spacing=0.08
        )
        
        # 온도
        fig_ts.add_trace(
            go.Scatter(x=school_env.index, y=school_env['temperature'], 
                      mode='lines', name='온도', line=dict(color='#FF6B6B')),
            row=1, col=1
        )
        
        # 습도
        fig_ts.add_trace(
            go.Scatter(x=school_env.index, y=school_env['humidity'], 
                      mode='lines', name='습도', line=dict(color='#4A90E2')),
            row=2, col=1
        )
        
        # EC
        fig_ts.add_trace(
            go.Scatter(x=school_env.index, y=school_env['ec'], 
                      mode='lines', name='실측 EC', line=dict(color='#50C878')),
            row=3, col=1
        )
        
        # 목표 EC 선
        target_ec = SCHOOL_EC[selected_school]['ec']
        fig_ts.add_hline(
            y=target_ec, line_dash="dash", line_color="red", 
            annotation_text=f"목표 EC: {target_ec}", row=3, col=1
        )
        
        fig_ts.update_xaxes(title_text="측정 시점", row=3, col=1)
        fig_ts.update_yaxes(title_text="°C", row=1, col=1)
        fig_ts.update_yaxes(title_text="%", row=2, col=1)
        fig_ts.update_yaxes(title_text="dS/m", row=3, col=1)
        
        fig_ts.update_layout(
            height=800,
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
            showlegend=False
        )
        
        st.plotly_chart(fig_ts, use_container_width=True)
    
    # 환경 데이터 원본
    with st.expander("환경 데이터 원본 보기"):
        if selected_school == "전체":
            for school in SCHOOL_EC.keys():
                st.write(f"**{school}**")
                st.dataframe(env_data[school], use_container_width=True)
        else:
            st.dataframe(env_data[selected_school], use_container_width=True)
            
            # CSV 다운로드
            csv = env_data[selected_school].to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="CSV 다운로드",
                data=csv,
                file_name=f"{selected_school}_환경데이터.csv",
                mime="text/csv"
            )

# Tab 3: 생육 결과
with tab3:
    st.header("생육 결과 분석")
    
    # 핵심 결과 카드
    st.subheader("🥇 EC별 평균 생중량")
    
    cols = st.columns(4)
    for idx, school in enumerate(SCHOOL_EC.keys()):
        avg_weight = growth_data[school]['생중량(g)'].mean()
        ec_value = SCHOOL_EC[school]['ec']
        
        with cols[idx]:
            if school == optimal_school:
                st.success(f"**{school}** (EC {ec_value})")
                st.metric("평균 생중량", f"{avg_weight:.2f}g", delta="최적 ⭐")
            else:
                st.info(f"**{school}** (EC {ec_value})")
                st.metric("평균 생중량", f"{avg_weight:.2f}g")
    
    # EC별 생육 비교 (2x2)
    st.subheader("EC별 생육 비교")
    
    growth_summary = pd.DataFrame({
        school: {
            '평균 생중량': growth_data[school]['생중량(g)'].mean(),
            '평균 잎 수': growth_data[school]['잎 수(장)'].mean(),
            '평균 지상부 길이': growth_data[school]['지상부 길이(mm)'].mean(),
            '개체수': len(growth_data[school]),
            'EC': SCHOOL_EC[school]['ec']
        }
        for school in SCHOOL_EC.keys()
    }).T.sort_values('EC')
    
    fig_growth = make_subplots(
        rows=2, cols=2,
        subplot_titles=("평균 생중량 (g) ⭐", "평균 잎 수 (장)", 
                       "평균 지상부 길이 (mm)", "개체수"),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    schools_sorted = growth_summary.index.tolist()
    colors_sorted = [SCHOOL_EC[s]['color'] for s in schools_sorted]
    
    # 생중량
    fig_growth.add_trace(
        go.Bar(x=schools_sorted, y=growth_summary['평균 생중량'], 
               marker_color=colors_sorted, showlegend=False),
        row=1, col=1
    )
    
    # 잎 수
    fig_growth.add_trace(
        go.Bar(x=schools_sorted, y=growth_summary['평균 잎 수'], 
               marker_color=colors_sorted, showlegend=False),
        row=1, col=2
    )
    
    # 지상부 길이
    fig_growth.add_trace(
        go.Bar(x=schools_sorted, y=growth_summary['평균 지상부 길이'], 
               marker_color=colors_sorted, showlegend=False),
        row=2, col=1
    )
    
    # 개체수
    fig_growth.add_trace(
        go.Bar(x=schools_sorted, y=growth_summary['개체수'], 
               marker_color=colors_sorted, showlegend=False),
        row=2, col=2
    )
    
    fig_growth.update_layout(
        height=600,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    
    st.plotly_chart(fig_growth, use_container_width=True)
    
    # 생중량 분포
    st.subheader("학교별 생중량 분포")
    
    fig_box = go.Figure()
    
    for school in SCHOOL_EC.keys():
        fig_box.add_trace(go.Box(
            y=growth_data[school]['생중량(g)'],
            name=f"{school} (EC {SCHOOL_EC[school]['ec']})",
            marker_color=SCHOOL_EC[school]['color']
        ))
    
    fig_box.update_layout(
        yaxis_title="생중량 (g)",
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
        height=400
    )
    
    st.plotly_chart(fig_box, use_container_width=True)
    
    # 상관관계 분석
    st.subheader("상관관계 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_corr1 = go.Figure()
        
        for school in SCHOOL_EC.keys():
            df_school = growth_data[school]
            fig_corr1.add_trace(go.Scatter(
                x=df_school['잎 수(장)'],
                y=df_school['생중량(g)'],
                mode='markers',
                name=school,
                marker=dict(color=SCHOOL_EC[school]['color'], size=8)
            ))
        
        fig_corr1.update_layout(
            title="잎 수 vs 생중량",
            xaxis_title="잎 수 (장)",
            yaxis_title="생중량 (g)",
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
            height=400
        )
        
        st.plotly_chart(fig_corr1, use_container_width=True)
    
    with col2:
        fig_corr2 = go.Figure()
        
        for school in SCHOOL_EC.keys():
            df_school = growth_data[school]
            fig_corr2.add_trace(go.Scatter(
                x=df_school['지상부 길이(mm)'],
                y=df_school['생중량(g)'],
                mode='markers',
                name=school,
                marker=dict(color=SCHOOL_EC[school]['color'], size=8)
            ))
        
        fig_corr2.update_layout(
            title="지상부 길이 vs 생중량",
            xaxis_title="지상부 길이 (mm)",
            yaxis_title="생중량 (g)",
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
            height=400
        )
        
        st.plotly_chart(fig_corr2, use_container_width=True)
    
    # 생육 데이터 원본
    with st.expander("생육 데이터 원본 보기"):
        if selected_school == "전체":
            for school in SCHOOL_EC.keys():
                st.write(f"**{school}** (개체수: {len(growth_data[school])})")
                st.dataframe(growth_data[school], use_container_width=True)
        else:
            st.dataframe(growth_data[selected_school], use_container_width=True)
            
            # XLSX 다운로드
            buffer = io.BytesIO()
            growth_data[selected_school].to_excel(buffer, index=False, engine="openpyxl")
            buffer.seek(0)
            
            st.download_button(
                label="XLSX 다운로드",
                data=buffer,
                file_name=f"{selected_school}_생육데이터.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# 푸터
st.markdown("---")
st.markdown("🌱 극지식물 최적 EC 농도 연구 대시보드 | Powered by Streamlit")
