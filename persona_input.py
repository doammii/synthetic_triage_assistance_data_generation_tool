import os
import pandas as pd
import streamlit as st
from utils import generate_conversation, save_conversation_json, delete_last_conversation

EXCEL_PATH = "./data/GT_KTAS카테고리_분류.xlsx"

@st.cache_data(show_spinner=False)
def load_category_table(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {path}")

    df = pd.read_excel(path, usecols=["나이", "대분류", "중분류"])
    df = df.astype(str).apply(lambda s: s.str.strip())

    return df

@st.cache_data(show_spinner=False)
def build_hierarchy(df: pd.DataFrame):
    """
    { "15세 이상": {"물질오용": [...], "정신건강": [...]}, "15세 미만": {...} }
    """
    tree = {}
    for age_val, dfa in df.groupby("나이"):
        if age_val not in ["15세 이상", "15세 미만"]:
            continue
        main_map = {}
        for main_val, dfm in dfa.groupby("대분류"):
            mids = sorted(dfm["중분류"].dropna().unique().tolist())
            main_map[main_val] = mids
        tree[age_val] = main_map
    return tree

def persona_input_tab():
    st.header("[환자 페르소나 설정 및 대화 생성]")

    try:
        cat_df = load_category_table(EXCEL_PATH)
        hierarchy = build_hierarchy(cat_df)
    except Exception as e:
        st.error(f"카테고리 엑셀 로드 중 오류: {e}")
        return

    gender = st.radio("성별", ["남성", "여성"], horizontal=True, key="gender_sel")
    age = st.radio("나이", ["15세 미만", "15세 이상"], horizontal=True, key="age_sel")

    main_options = sorted(hierarchy.get(age, {}).keys())
    if not main_options:
        st.warning("선택한 나이에 해당하는 대분류가 없습니다. 엑셀을 확인해주세요.")
        return
    main_category = st.selectbox("대분류", main_options, key="main_sel")

    middle_options = hierarchy.get(age, {}).get(main_category, [])
    if not middle_options:
        middle_category = st.text_input("중분류 (직접 입력)", key="mid_manual")
    else:
        middle_category = st.selectbox("중분류 (주증상)", middle_options, key="mid_sel")

    ktas_level = st.radio("KTAS 레벨", [1, 2, 3, 4, 5], horizontal=True, key="ktas_sel")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("대화 생성", type="primary", use_container_width=True):
            persona = {
                "age": age,
                "gender": gender,
                "main_category": main_category,
                "middle_category": middle_category,
                "ktas_level": ktas_level
            }
            conversation_json = generate_conversation(persona)
            st.session_state.last_generated = conversation_json
            st.json(conversation_json)
            save_conversation_json(conversation_json)
            st.success("대화가 생성되어 저장되었습니다.")
    with col2:
        if st.button("대화 삭제", use_container_width=True):
            delete_last_conversation()
            st.success("만들어진 대화가 삭제되었습니다.")
            if "last_generated" in st.session_state:
                del st.session_state["last_generated"]

