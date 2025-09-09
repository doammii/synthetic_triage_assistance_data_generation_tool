import streamlit as st
import pandas as pd
from utils import load_all_dialogues
import json

def dialogue_list_tab():
    st.header("[전체 대화 확인 및 저장]")

    data = load_all_dialogues()
    rows = []

    for entry in data:
        conv_str = json.dumps(entry.get("dialogue", {}), ensure_ascii=False)

        evals = entry.get("evaluation", {})
        ktas_val = evals.get("ktas", "")         
        question = evals.get("question", "")
        realism = evals.get("realism", "")
        evaluator = evals.get("evaluator", "")    

        persona = entry.get("persona", {})

        rows.append({
            "대화 출처": "생성",
            "생성한 대화": conv_str,
            "평가자": evaluator,
            "KTAS 레벨의 적절성": ktas_val,
            "대화의 적절성": question,
            "대화의 현실성": realism,
            "나이": persona.get("age", ""),
            "성별": persona.get("gender", ""),
            "대분류": persona.get("main_category", ""),
            "중분류": persona.get("middle_category", ""),
            "KTAS 레벨": persona.get("ktas_level", "")
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    if not df.empty and "KTAS 레벨의 적절성" in df.columns:
        st.markdown("#### KTAS 적절성 요약")
        summary = df["KTAS 레벨의 적절성"].value_counts(dropna=False)
        st.write({
            "Y": int(summary.get("Y", 0)),
            "N": int(summary.get("N", 0)),
            "판단 불가": int(summary.get("판단 불가", 0)),
            "미평가": int(summary.get("", 0))  
        })

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "CSV 파일로 내보내기",
        csv,
        file_name="응급실_대화_데이터.csv",
        mime="text/csv"
    )