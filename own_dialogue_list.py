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

def update_own_evaluation(idx, ktas, question, realism, evaluator):
    data = st.session_state.get("own_dialogues", [])
    if 0 <= idx < len(data):
        if "evaluation" not in data[idx]:
            data[idx]["evaluation"] = {}
        data[idx]["evaluation"].update(evaluation_data)
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
                # KTAS 레벨의 적절성 (기존 유지)
                st.markdown("**KTAS 레벨의 적절성**")
                ktas_appropriateness = st.selectbox(
                    "",
                    options=["Y", "N", "판단 불가"],
                    index=["Y", "N", "판단 불가"].index(entry.get("evaluation", {}).get("ktas_appropriateness", "판단 불가")),
                    key=f"own_ktas_{idx}", label_visibility="hidden"
                )

                # 대화의 적절성 평가
                st.markdown("**대화의 적절성**")
                appropriateness_questions = [
                    ("일반인이 이해할 수 있는 쉬운 용어로 대화하는가?", "어려운 용어(대화에 어려운 용어를 사용하여 실제 상황에서 의사소통이 어려울 것 같은 질문과 답변이 있다)\n쉬운 용어 사용(전체적으로 일반인들이 이해하기 쉬운 용어를 사용하여 실제 상황에서 의사소통이 원활할 것 같다)"),
                    ("질문과 답변이 명확하고 간결한가?", "복잡한 질문과 답변(동시에 2가지 이상의 내용을 질문하고 답하여 대화가 복잡하다)\n명확하고 간결한 질문(전체적으로 질문과 답변이 간결하고 대화의 내용이 명확하다)"),
                    ("환자의 응급도를 평가하는 대화가 포함되어 있는가?", "포함되어 있다(환자의 응급도 레벨을 결정하는데 필요한 정보를 묻고 답하는 대화가 포함되어 있다)\n포함되어 있지 않다(환자의 응급도 레벨을 결정하는데 필요한 정보를 묻고 답하는 대화가 포함되어 있지 않다)"),
                    ("대화의 순서는 논리적인가?", "비효율적인 질문 순서(대화의 순서가 논리적이지 않고 산만하다)\n체계적인 질문 흐름(첫 질문부터 결론까지 논리적으로 대화가 진행되었다)"),
                    ("적절한 공감이나 지지적 표현이 있는가?", "필요한 경우 공감 및 지지적 표현 없음(환자가 불안함을 느끼는 상황에서 공감과 지지적 표현을 하지 않았다)\n필요한 경우 공감 및 지지적 표현 사용(질문자가 사용자의 불안감을 이해하기 쉽게 중간에 적절한 공감을 해주었다)"),
                ]
                
                eval_cols_q_header = st.columns([0.6, 0.4])
                with eval_cols_q_header[0]:
                    st.markdown("**질문**")
                with eval_cols_q_header[1]:
                    st.markdown("**평가**")

                appropriate_ratings = {} 
                for i, (q, help_text) in enumerate(appropriateness_questions):
                    question_key = f"appropriate_q_{idx}_{i}"
                    current_rating = entry.get("evaluation", {}).get(question_key, "보통이다")
                    
                    cols = st.columns([0.6, 0.4])
                    with cols[0]:
                        st.markdown(f'<a title="{help_text}" style="text-decoration: none; color: inherit;">{q} ⓘ</a>', unsafe_allow_html=True)
                    with cols[1]:
                        radio_val = st.radio(
                            "",
                            options=["그렇다", "보통이다", "그렇지 않다"],
                            index=["그렇다", "보통이다", "그렇지 않다"].index(current_rating),
                            key=f"{question_key}_radio",
                            label_visibility="hidden",
                            horizontal=True
                        )
                        appropriate_ratings[question_key] = radio_val
                
                # 대화의 현실성 평가
                st.markdown("**대화의 현실성**")
                realism_questions = [
                    "실제 응급실 상황에 있을 수 있는 상황인가?",
                    "실제 대화처럼 자연스러운가?",
                    "환자는 환자답고, 의료진은 의료진다운가?",
                    "감정적인 표현이 현실적인가?",
                ]
                
                eval_cols_r_header = st.columns([0.6, 0.4])
                with eval_cols_r_header[0]:
                    st.markdown("**질문**")
                with eval_cols_r_header[1]:
                    st.markdown("**평가**")

                realism_ratings = {}
                for i, q in enumerate(realism_questions):
                    question_key = f"realism_q_{idx}_{i}"
                    current_rating = entry.get("evaluation", {}).get(question_key, "보통이다")
                    
                    cols = st.columns([0.6, 0.4])
                    with cols[0]:
                        st.markdown(f'<span style="text-decoration: none; color: inherit;">{q}</span>', unsafe_allow_html=True)
                    with cols[1]:
                        radio_val = st.radio(
                            "",
                            options=["그렇다", "보통이다", "그렇지 않다"],
                            index=["그렇다", "보통이다", "그렇지 않다"].index(current_rating),
                            key=f"{question_key}_radio",
                            label_visibility="hidden",
                            horizontal=True
                        )
                        realism_ratings[question_key] = radio_val
                    
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
                        
                        update_own_evaluation(
                            idx, 
                            ktas_appropriateness, 
                            question_appropriateness_score, 
                            dialogue_realism_score, 
                            evaluator
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
            "KTAS 레벨의 적절성": evals.get("ktas", ""),
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
            file_name="자체_응급실_문진_대화_데이터.csv",
            mime="text/csv",
            use_container_width=True
        )