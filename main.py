import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 페이지 설정
st.set_page_config(page_title="부서 근태 관리 시스템", layout="wide")

st.title("📊 부서 근태 관리 앱")
st.info("각 파트장은 해당 파트의 근태를 확인 후 '완료'를 눌러주세요.")

# 1. Google Sheets 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 불러오기 (캐시를 무효화하여 실시간성 유지)
df = conn.read(worksheet="Attendance", ttl=0)

# 2. 파트 선택 및 필터링
parts = ["1파트", "2파트", "3파트", "4파트"]
selected_part = st.selectbox("본인의 파트를 선택하세요", parts)

# 해당 파트원 데이터만 필터링
part_df = df[df['파트'] == selected_part].copy()

st.subheader(f"📍 {selected_part} 근태 체크")

# 3. 데이터 에디터 (클릭 최소화: 드롭다운 선택 방식)
# 상태 옵션 정의
status_options = ["근무", "휴가", "교육", "출장"]

edited_df = st.data_editor(
    part_df,
    column_config={
        "상태": st.column_config.SelectboxColumn(
            "근태 상태",
            help="파트원의 상태를 선택하세요",
            options=status_options,
            required=True,
        )
    },
    disabled=["이름", "파트"], # 이름과 파트는 수정 불가
    hide_index=True,
    use_container_width=True
)

# 4. 파트별 완료 처리 (Session State 활용)
if "completed_parts" not in st.session_state:
    st.session_state.completed_parts = {}

col1, col2 = st.columns([1, 5])
with col1:
    if st.button(f"{selected_part} 완료 및 저장"):
        # 전체 데이터프레임 업데이트
        df.update(edited_df)
        # 실제 Google Sheets에 업데이트 (인증 설정 필요)
        # conn.update(worksheet="Attendance", data=df) 
        
        st.session_state.completed_parts[selected_part] = True
        st.success(f"{selected_part} 저장 완료!")

# 5. 전체 취합 및 보고 문구 생성
st.divider()
st.subheader("📢 전체 취합 현황")

completed_list = list(st.session_state.completed_parts.keys())
st.write(f"현재 완료된 파트: {', '.join(completed_list) if completed_list else '없음'}")

# 모든 파트(4개)가 완료되었을 때 보고서 생성
if len(st.session_state.completed_parts) == 4:
    total_count = len(df)
    counts = df['상태'].value_counts()
    
    # 보고용 문구 포맷팅
    working = counts.get("근무", 0)
    vacation = counts.get("휴가", 0)
    education = counts.get("교육", 0)
    biz_trip = counts.get("출장", 0)
    
    report_text = f"총원 {total_count}명 중 {working}명 근무, {vacation}명 휴가, {education}명 교육, {biz_trip}명 출장 보고드립니다."
    
    st.code(report_text, language=None)
    st.button("📋 문구 복사하기 (위 박스 우측 버튼 클릭)")
else:
    st.warning("모든 파트(1~4파트)가 완료되어야 최종 보고 문구가 생성됩니다.")

# 관리자용: 데이터 초기화 버튼 (테스트용)
if st.sidebar.button("진행 상황 초기화"):
    st.session_state.completed_parts = {}
    st.rerun()
