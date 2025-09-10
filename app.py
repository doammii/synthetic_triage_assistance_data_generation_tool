import streamlit as st
from persona_input import persona_input_tab
from evaluate_dialogue import evaluate_dialogue_tab
from dialogue_list import dialogue_list_tab
from own_dialogue_list import upload_and_evaluate_tab, own_dialogue_list_tab

st.set_page_config(page_title="응급실 문진 대화 생성 TOOL", layout="wide")

# 상위 섹션
section = st.sidebar.radio(
    "SECTION",
    ["생성한 대화", "자체 대화"],
    index=0,
    key="section_radio"
)

# 하위 메뉴
if section == "생성한 대화":
    st.sidebar.markdown("### [ 생성한 대화 ]")
    sub = st.sidebar.radio(
        "MENU",
        ["1. 환자 페르소나 및 대화 생성",
         "2. 생성 대화 평가",
         "3. 전체 대화 확인 및 저장"],
        key="generated_submenu"
    )

    if sub == "1. 환자 페르소나 및 대화 생성":
        persona_input_tab()
    elif sub == "2. 생성 대화 평가":
        evaluate_dialogue_tab()
    elif sub == "3. 전체 대화 확인 및 저장":
        dialogue_list_tab()

else:  # "자체 대화"
    st.sidebar.markdown("### [ 자체 대화 ]")
    sub = st.sidebar.radio(
        "메뉴",
        ["1. 대화 업로드 및 평가",
         "2. 전체 대화 확인 및 저장"],
        key="own_submenu"
    )

    if sub == "1. 대화 업로드 및 평가":
        upload_and_evaluate_tab()
    elif sub == "2. 전체 대화 확인 및 저장":
        own_dialogue_list_tab()
