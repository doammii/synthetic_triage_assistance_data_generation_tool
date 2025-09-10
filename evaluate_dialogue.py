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
                    index=["Y", "N", "판단 불가"].index(entry.get("evaluation", {}).get("ktas_appropriateness", "판단 불가")),
                    key=f"ktas_{idx}", label_visibility="hidden"
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
                        appropriate_ratings.append(radio_val)
                
                # 대화의 현실성 평가
                st.markdown("**대화의 현실성**")
                realism_questions = [
                    ("실제 응급실 상황에 있을 수 있는 상황인가?", "실제 응급실 상황과 일치하는지 여부 확인"),
                    ("실제 대화처럼 자연스러운가?", "자연스럽고 현실적인 대화인지 확인"),
                    ("환자는 환자답고, 의료진은 의료진다운가?", "각 역할에 맞는 대화인지 확인"),
                    ("감정적인 표현이 현실적인가?", "감정 표현이 실제 상황과 유사한지 확인"),
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
                        
                        update_evaluation(
                            idx, 
                            ktas_appropriateness, 
                            question_appropriateness_score, 
                            dialogue_realism_score, 
                            evaluator
                        )
                        st.success(f"평가가 성공적으로 저장되었습니다.")
        
        st.divider()

if __name__ == "__main__":
    evaluate_dialogue_tab()
