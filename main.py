# --- Tab 3 내부의 다운로드 버튼 부분 수정 ---
with st.expander("학교별 생육 데이터 원본 + XLSX 다운로드"):
    st.dataframe(disp_growth)
    
    # 1. BytesIO 버퍼 생성
    buffer = io.BytesIO()
    
    # 2. ExcelWriter로 버퍼에 데이터 쓰기
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        disp_growth.to_excel(writer, index=False, sheet_name='Sheet1')
    
    # 3. 중요: getvalue()를 사용하여 바이너리 데이터를 추출하여 전달
    st.download_button(
        label="📊 XLSX 다운로드",
        data=buffer.getvalue(),  # <--- 이 부분이 핵심입니다!
        file_name=f"{selected_school}_생육데이터.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
