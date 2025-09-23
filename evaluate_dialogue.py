import streamlit as st
import json
from utils import load_all_dialogues, update_evaluation

def evaluate_dialogue_tab():
    """
    첨부된 이미지 UI에 맞게 대화 평가 탭을 재구성합니다.
    """
    st.header("[생성된 대화 평가]")

    # 대화 데이터 로드
    data = load_all_dialogues()
    if not data:
        st.info("평가할 대화가 없습니다.")
        return

    # 목차 생성
    toc_lines = [f"- [대화 {i+1}](#대화-{i+1})" for i in range(len(data))]
    st.markdown("### 목차")
    st.markdown("\n".join(toc_lines))
    st.divider()

    # 각 대화에 대한 평가 섹션 생성
    for idx, entry in enumerate(data):
        st.markdown(f'<a name="대화-{idx+1}"></a>', unsafe_allow_html=True)
        st.subheader(f"대화 {idx+1}")

        # 2개 컬럼 생성: 왼쪽에 대화 내용, 오른쪽에 평가 항목
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 대화내용")
            st.json(entry.get("dialogue", {}))

        with col2:
            st.markdown("### 평가항목")
            
            with st.form(f"eval_form_{idx}"):
                # KTAS 레벨의 적절성
                st.markdown("**KTAS 레벨의 적절성**")
                ktas_appropriateness = st.selectbox(
                    "",
                    options=["Y", "N", "판단 불가"],
                    index=["Y", "N", "판단 불가"].index(entry.get("evaluation", {}).get("ktas", "판단 불가")),
                    key=f"ktas_{idx}", label_visibility="hidden"
                )

                # 대화의 적절성 평가
                st.markdown("**대화의 적절성**")
                appropriateness_questions = [
                    ("핵심 정보와 체계를 모두 갖춘 문진을 했는가?", "- 핵심 정보와 체계를 모두 갖춘 문진을 하였다(주증상·발병 시점·통증 특성 등 필수 정보를 OPQRST·SAMPLE 구조에 따라 묻고, 약물·알레르기·과거력·최근 외상 등 중요한 정보를 빠짐없이 확인하였다.) \n- 핵심 정보와 체계를 모두 갖춘 문진을 하지 않았다(필수 증상이나 약물·알레르기·과거력·최근 외상 등 핵심 정보를 충분히 묻지 않거나, 표준 문진 구조를 따르지 않아 중요한 정보가 누락되었다.)"),
                    ("응급 상태와 위험 신호(red flag)를 적절히 확인했는가?", "- 응급 상태와 위험 신호(red flag)를 적절히 확인하였다(의식 수준, 호흡곤란, 흉통, 출혈 등 응급 여부와 실신·심한 호흡곤란 등 중증 위험 신호를 빠짐없이 점검하였다.) \n- 응급 상태와 위험 신호(red flag)를 적절히 확인하지 않았다(응급 여부나 실신·심한 호흡곤란 등 중증 위험 신호를 충분히 확인하지 않았다.)"),
                    ("의학적 용어를 환자가 이해하기 쉽게 설명했는가?", "- 의학적 용어를 환자가 이해하기 쉽게 설명하였다(전문 용어를 환자가 이해할 수 있도록 쉬운 표현이나 설명으로 전달하였다.) \n- 의학적 용어를 환자가 이해하기 쉽게 설명하지 않았다(전문 용어를 그대로 사용하거나 설명이 부족해 환자가 이해하기 어려웠다.)"),
                    ("모호한 답변을 다시 확인했는가?", "- 모호한 답변을 다시 확인하였다(환자의 응답이 불명확하거나 애매할 때 추가 질문이나 재확인을 통해 정확히 파악하였다.) \n- 모호한 답변을 다시 확인하지 않았다(환자의 응답이 불명확하거나 애매했음에도 추가 질문이나 재확인을 하지 않았다.)"),
                    ("의료 윤리를 준수했는가?", "- 의료 윤리를 준수하였다(환자의 개인정보를 보호하고, 임신 여부·정신질환 등 민감한 질문을 할 때 적절한 배려와 존중을 보였다.) \n- 의료 윤리를 준수하지 않았다(환자의 개인정보 보호가 부족하거나, 임신 여부·정신질환 등 민감한 질문을 할 때 배려와 존중이 부족했다.)"),
                ]
                
                # 표 형식 UI 구현
                eval_cols_q = st.columns([0.6, 0.4])
                with eval_cols_q[0]:
                    st.markdown("**질문**")
                with eval_cols_q[1]:
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
                
                eval_cols_r = st.columns([0.6, 0.4])
                with eval_cols_r[0]:
                    st.markdown("**질문**")
                with eval_cols_r[1]:
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
                    key=f"evaluator_{idx}", 
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
                        
                        # 개별 문항 선택값을 저장하기 위한 키-값 맵 구성
                        ratings_map = {}
                        for i, val in enumerate(appropriate_ratings):
                            ratings_map[f"appropriate_q_{idx}_{i}"] = val
                        for i, val in enumerate(realism_ratings):
                            ratings_map[f"realism_q_{idx}_{i}"] = val

                        update_evaluation(
                            idx,
                            ktas_appropriateness,
                            question_appropriateness_score,
                            dialogue_realism_score,
                            evaluator,
                            ratings=ratings_map
                        )
                        st.success(f"평가가 성공적으로 저장되었습니다.")
        
        st.divider()

if __name__ == "__main__":
    evaluate_dialogue_tab()
