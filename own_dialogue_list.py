import streamlit as st
import pandas as pd
import json
import os

OWN_DATA_PATH = "data/own_dialogues.json"

def load_own_dialogues():
    if not os.path.exists(OWN_DATA_PATH):
        return []
    with open(OWN_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_own_dialogues(data):
    os.makedirs(os.path.dirname(OWN_DATA_PATH), exist_ok=True)
    with open(OWN_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_own_evaluation(idx, question, realism, evaluator, ratings: dict | None = None):
    data = st.session_state.get("own_dialogues", [])
    if 0 <= idx < len(data):
        evaluation = {
            "question": question,
            "realism": realism,
            "evaluator": evaluator
        }
        if ratings:
            evaluation.update(ratings)
        data[idx]["evaluation"] = evaluation
    st.session_state["own_dialogues"] = data
    save_own_dialogues(data)

def read_csv_any_encoding(uploaded_file):
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr", "latin1"]
    last_err = None
    for enc in encodings:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=enc, sep=None, engine="python")
            return df
        except Exception as e:
            last_err = e
            continue
    # CSV 실패 시 엑셀 시도
    try:
        uploaded_file.seek(0)
        return pd.read_excel(uploaded_file)
    except Exception as e2:
        raise RuntimeError(f"파일을 읽지 못했습니다. 시도 인코딩={encodings}, 마지막 오류={last_err}, 엑셀 오류={e2}")

# --------- Main Tab: 업로드 & 평가 ---------
def upload_and_evaluate_tab():
    st.markdown("""
        <style>
        /* 체크박스 컨테이너에 최소 높이를 지정하여 정렬을 맞춥니다 */
        div[data-testid="stCheckbox"] {
            min-height: 45px; /* 라벨이 두 줄일 때를 고려한 높이, 필요시 조정 */
            display: flex;
            flex-direction: column;
            justify-content: center; /* 내용을 세로 중앙에 정렬 */
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.header("[자체 대화 업로드 및 평가]")

    st.markdown("CSV를 업로드하면 각 행의 대화를 확인하고 평가할 수 있습니다.")
    uploaded = st.file_uploader("CSV 파일 업로드", type=["csv", "xlsx"], accept_multiple_files=False)

    if "own_dialogues" not in st.session_state:
        st.session_state["own_dialogues"] = load_own_dialogues()

    if uploaded is not None:
        try:
            df = read_csv_any_encoding(uploaded)
        except Exception as e:
            st.error(f"파일을 읽는 중 오류: {e}")
            return

        dialogue_col = None
        for cand in ["dialogue", "생성한 대화", "대화", "챗GPT와 대화한 내용", "contents"]:
            if cand in df.columns:
                dialogue_col = cand
                break

        if dialogue_col is None:
            st.error("업로드한 파일에서 대화 컬럼을 찾지 못했습니다. 예: 'dialogue', '생성한 대화', '대화'")
            return

        own_list = []
        for _, row in df.iterrows():
            raw = row.get(dialogue_col, "")
            parsed = None
            if isinstance(raw, str):
                s = raw.strip()
                if s.startswith("{") or s.startswith("["):
                    try:
                        parsed = json.loads(s)
                    except Exception:
                        parsed = None
            item = {
                "dialogue": parsed if parsed is not None else raw,
                "source": "업로드",
                "evaluation": {}
            }
            own_list.append(item)

        st.session_state["own_dialogues"] = own_list
        save_own_dialogues(own_list)
        st.success(f"업로드 완료: {len(own_list)}개 대화가 로드되었습니다.")

    data = st.session_state.get("own_dialogues", [])

    if not data:
        st.info("업로드한 데이터가 없습니다. CSV를 업로드해 주세요.")
        if os.path.exists(OWN_DATA_PATH) and st.button("이전에 저장한 자체 대화 불러오기"):
            st.session_state["own_dialogues"] = load_own_dialogues()
        return

    toc_lines = [f"- [대화 {i+1}](#own-대화-{i+1})" for i in range(len(data))]
    st.markdown("### 목차")
    st.markdown("\n".join(toc_lines))
    st.divider()

    # 페이지네이션(옵션)
    with st.expander("표시 범위 설정", expanded=False):
        page_size = st.number_input("페이지 크기", min_value=1, max_value=50, value=10, step=1, key="own_page_size")
        page = st.number_input("페이지 번호 (1부터)", min_value=1, value=1, step=1, key="own_page_no")
    start = (page - 1) * page_size
    end = min(start + page_size, len(data))
    if start >= len(data):
        st.warning("페이지 범위를 벗어났습니다. 페이지 번호를 줄여주세요.")
        return

    # 행별 표시 + 평가 폼
    for idx in range(start, end):
        entry = data[idx]

        st.markdown(f'<a name="own-대화-{idx+1}"></a>', unsafe_allow_html=True)
        st.subheader(f"대화 {idx+1}")

        # 2개 컬럼 생성: 왼쪽에 대화 내용, 오른쪽에 평가 항목
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 대화내용")
            dlg = entry.get("dialogue", {})
            if isinstance(dlg, (dict, list)):
                pretty = json.dumps(dlg, ensure_ascii=False, indent=2)
                st.code(pretty, language="json") 
            else:
                st.code(str(dlg))

        with col2:
            st.markdown("### 평가항목")
            
            with st.form(f"own_eval_form_{idx}"):
                # 대화의 적절성 평가
                st.markdown("**대화의 적절성**")
                appropriateness_questions = [
                    ("핵심 정보와 체계를 모두 갖춘 문진을 했는가?", "- 핵심 정보와 체계를 모두 갖춘 문진을 하였다(주증상·발병 시점·통증 특성 등 필수 정보를 OPQRST·SAMPLE 구조에 따라 묻고, 약물·알레르기·과거력·최근 외상 등 중요한 정보를 빠짐없이 확인하였다.) \n- 핵심 정보와 체계를 모두 갖춘 문진을 하지 않았다(필수 증상이나 약물·알레르기·과거력·최근 외상 등 핵심 정보를 충분히 묻지 않거나, 표준 문진 구조를 따르지 않아 중요한 정보가 누락되었다.)"),
                    ("응급 상태와 위험 신호(red flag)를 적절히 확인했는가?", "- 응급 상태와 위험 신호(red flag)를 적절히 확인하였다(의식 수준, 호흡곤란, 흉통, 출혈 등 응급 여부와 실신·심한 호흡곤란 등 중증 위험 신호를 빠짐없이 점검하였다.) \n- 응급 상태와 위험 신호(red flag)를 적절히 확인하지 않았다(응급 여부나 실신·심한 호흡곤란 등 중증 위험 신호를 충분히 확인하지 않았다.)"),
                    ("의학적 용어를 환자가 이해하기 쉽게 설명했는가?", "- 의학적 용어를 환자가 이해하기 쉽게 설명하였다(전문 용어를 환자가 이해할 수 있도록 쉬운 표현이나 설명으로 전달하였다.) \n- 의학적 용어를 환자가 이해하기 쉽게 설명하지 않았다(전문 용어를 그대로 사용하거나 설명이 부족해 환자가 이해하기 어려웠다.)"),
                    ("모호한 답변을 다시 확인했는가?", "- 모호한 답변을 다시 확인하였다(환자의 응답이 불명확하거나 애매할 때 추가 질문이나 재확인을 통해 정확히 파악하였다.) \n- 모호한 답변을 다시 확인하지 않았다(환자의 응답이 불명확하거나 애매했음에도 추가 질문이나 재확인을 하지 않았다.)"),
                    ("의료 윤리를 준수했는가?", "- 의료 윤리를 준수하였다(환자의 개인정보를 보호하고, 임신 여부·정신질환 등 민감한 질문을 할 때 적절한 배려와 존중을 보였다.) \n- 의료 윤리를 준수하지 않았다(환자의 개인정보 보호가 부족하거나, 임신 여부·정신질환 등 민감한 질문을 할 때 배려와 존중이 부족했다.)"),
                ]
                
                eval_cols_q_header = st.columns([0.6, 0.4])
                with eval_cols_q_header[0]:
                    st.markdown("**질문**")
                with eval_cols_q_header[1]:
                    st.markdown("**평가**")

                appropriate_ratings = []
                for i, (q, help_text) in enumerate(appropriateness_questions):
                    question_key = f"appropriate_q_{idx}_{i}"
                    current_rating = entry.get("evaluation", {}).get(question_key, "보통이다")
                    
                    cols = st.columns([0.6, 0.4])
                    with cols[0]:
                        safe_help = help_text.replace('"', '&quot;').replace("\n", "&#10;")
                        st.markdown(
                            f'<span style="text-decoration: none; color: inherit;">{q}</span><span title="{safe_help}" style="cursor: help; margin-left: 6px;">ⓘ</span>',
                            unsafe_allow_html=True,
                        )
                    with cols[1]:
                        radio_val = st.radio(
                            "",
                            options=["그렇다", "보통이다", "그렇지 않다"],
                            index=["그렇다", "보통이다", "그렇지 않다"].index(current_rating),
                            key=f"{question_key}_radio",
                            label_visibility="hidden",
                            horizontal=True
                        )
                        appropriate_ratings.append(radio_val)
                
                # 대화의 현실성 평가
                st.markdown("**대화의 현실성**")
                realism_questions = [
                    ("공감과 안정적 의사소통을 보였는가?", "환자의 고통과 두려움을 이해하는 공감적 태도로 일관된 톤을 유지하며, 응급 상황에서도 불안감을 과도하게 유발하지 않았는지 평가한다."),
                    ("질문을 적절한 속도와 단계로 진행했는가?", "한 번에 너무 많은 질문을 하지 않고 차분히 단계적으로 진행했는지 평가한다."),
                    ("대화 흐름을 유연하게 이어갔는가?", "환자의 예상 밖 답변에도 어색하게 끊기지 않고 자연스럽게 대화를 이어갔는지 평가한다."),
                    ("동일한 질문을 불필요하게 반복하지 않았는가?", "같은 질문을 과도하게 되풀이하지 않고 필요한 경우에만 반복했는지 평가한다."),
                    ("필요한 정보를 모두 수집한 뒤 자연스럽게 대화를 마무리했는가?", "대화가 어색하게 끊기지 않고 필요한 정보를 확보한 후 적절히 종료했는지 평가한다."),
                ]
                
                eval_cols_r_header = st.columns([0.6, 0.4])
                with eval_cols_r_header[0]:
                    st.markdown("**질문**")
                with eval_cols_r_header[1]:
                    st.markdown("**평가**")

                realism_ratings = []
                for i, (q, help_text) in enumerate(realism_questions):
                    question_key = f"realism_q_{idx}_{i}"
                    current_rating = entry.get("evaluation", {}).get(question_key, "보통이다")
                    
                    cols = st.columns([0.6, 0.4])
                    with cols[0]:
                        safe_help = help_text.replace('"', '&quot;').replace("\n", "&#10;")
                        st.markdown(
                            f'<span style="text-decoration: none; color: inherit;">{q}</span><span title="{safe_help}" style="cursor: help; margin-left: 6px;">ⓘ</span>',
                            unsafe_allow_html=True,
                        )
                    with cols[1]:
                        radio_val = st.radio(
                            "",
                            options=["그렇다", "보통이다", "그렇지 않다"],
                            index=["그렇다", "보통이다", "그렇지 않다"].index(current_rating),
                            key=f"{question_key}_radio",
                            label_visibility="hidden",
                            horizontal=True
                        )
                        realism_ratings.append(radio_val)
                    
                # 평가자 이름
                evaluator = st.text_input(
                    "평가자 이름 또는 ID", 
                    value=entry.get("evaluation", {}).get("evaluator", ""),
                    key=f"own_evaluator_{idx}", 
                    placeholder="예: hong_gildong"
                )

                submitted = st.form_submit_button("결과 저장")

                if submitted:
                    if not evaluator.strip():
                        st.error("평가자 이름/ID를 입력해주세요.")
                    else:
                        # 점수 계산 함수
                        def calculate_score(ratings):
                            base_score = 5
                            score_change = {"그렇다": 1, "보통이다": 0, "그렇지 않다": -1}
                            total_score_change = sum(score_change[r] for r in ratings)
                            final_score = base_score + total_score_change
                            return max(0, min(10, final_score))

                        question_appropriateness_score = calculate_score(appropriate_ratings)
                        dialogue_realism_score = calculate_score(realism_ratings)
                        
                        ratings_map = {}
                        for i, val in enumerate(appropriate_ratings):
                            ratings_map[f"appropriate_q_{idx}_{i}"] = val
                        for i, val in enumerate(realism_ratings):
                            ratings_map[f"realism_q_{idx}_{i}"] = val

                        update_own_evaluation(
                            idx,
                            question_appropriateness_score,
                            dialogue_realism_score,
                            evaluator,
                            ratings=ratings_map
                        )
                        st.success(f"평가가 성공적으로 저장되었습니다.")
        
        st.divider()

# --------- Main Tab: 대화 리스트 확인 ---------
def own_dialogue_list_tab():
    st.header("[자체 대화 전체 확인 및 저장]")

    if "own_dialogues" not in st.session_state:
        st.session_state["own_dialogues"] = load_own_dialogues()

    data = st.session_state.get("own_dialogues", [])

    if not data:
        st.info("표시할 자체 대화가 없습니다. 먼저 '대화 업로드 및 평가' 탭에서 CSV를 업로드하세요.")
        if os.path.exists(OWN_DATA_PATH) and st.button("저장된 자체 대화 불러오기", use_container_width=True):
            st.session_state["own_dialogues"] = load_own_dialogues()
            st.success("저장된 자체 대화를 불러왔습니다.")
        return

    # 표용 rows 구성
    rows = []
    for i, entry in enumerate(data):
        dlg = entry.get("dialogue", {})
        conv_str = json.dumps(dlg, ensure_ascii=False) if isinstance(dlg, (dict, list)) else str(dlg)

        evals = entry.get("evaluation", {}) or {}
        rows.append({
            "__idx": i,  # 내부 인덱스 (삭제용)
            "대화 출처": "자체",
            "대화": conv_str,
            "평가자": evals.get("evaluator", ""),
            "대화의 적절성": evals.get("question", ""),
            "대화의 현실성": evals.get("realism", ""),
            "삭제": False
        })

    df = pd.DataFrame(rows)
    edited = st.data_editor(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "__idx": st.column_config.NumberColumn("__idx", help="내부 인덱스", disabled=True, required=True),
            "삭제": st.column_config.CheckboxColumn("삭제"),
            "대화": st.column_config.TextColumn("대화", help="원문 JSON/텍스트", width="large"),
        },
        disabled=["__idx"]
    )

    col_del, col_csv = st.columns([1, 1])

    # 선택 행 삭제
    with col_del:
        if st.button("선택 행 삭제", use_container_width=True):
            del_rows = edited[edited["삭제"] == True]
            if del_rows.empty:
                st.warning("삭제할 행을 선택하세요.")
            else:
                to_delete = set(del_rows["__idx"].tolist())
                new_data = [entry for j, entry in enumerate(data) if j not in to_delete]
                st.session_state["own_dialogues"] = new_data
                save_own_dialogues(new_data)
                st.success(f"{len(to_delete)}개 행을 삭제했습니다.")
                st.rerun()

    # CSV 내보내기
    with col_csv:
        export_df = edited.drop(columns=["__idx", "삭제"])
        csv = export_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "CSV 파일로 내보내기",
            csv,
            file_name="자체_대화_데이터.csv",
            mime="text/csv",
            use_container_width=True
        )