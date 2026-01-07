import streamlit as st
import requests
import os

# 백엔드 API 기본 주소 (로컬 개발 환경 기준)
API_URL = "http://localhost:8000"

# --- 페이지 설정 ---
st.set_page_config(
    page_title="RAG vs LLM Chatbot",
    page_icon="📚",
    layout="wide"
)

st.title("📚 RAG(검색 증강 생성) vs 일반 LLM 비교 시스템")
st.markdown("""
이 시스템은 **MongoDB Atlas Vector Search**와 **OpenAI GPT-4**를 활용합니다.
좌측 사이드바에서 PDF를 업로드하여 지식베이스를 구축하고, RAG 기능을 켜고 끄며 답변의 차이를 비교해보세요.
""")

# --- 사이드바: 설정 및 데이터 관리 ---
with st.sidebar:
    st.header("⚙️ 설정 및 데이터")
    
    # 1. 파일 업로드 섹션
    st.subheader("📄 지식베이스 추가")
    st.markdown("PDF 문서를 업로드하면 AI가 해당 내용을 학습합니다.")
    uploaded_file = st.file_uploader("PDF 파일 선택", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("문서 업로드 및 처리 시작"):
            with st.spinner("문서를 분석하고 벡터화하는 중입니다..."):
                # 업로드할 파일 준비 (multipart/form-data)
                files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                try:
                    response = requests.post(f"{API_URL}/upload", files=files)
                    if response.status_code == 200:
                        chunks = response.json().get('chunks_added')
                        st.success(f"✅ 처리가 완료되었습니다! 총 {chunks}개의 지식 조각이 추가되었습니다.")
                    else:
                        st.error(f"❌ 업로드 실패: {response.text}")
                except Exception as e:
                    st.error(f"❌ 서버 연결 오류: {e}")

    st.divider()

    # 2. RAG 옵션 토글
    st.subheader("🔍 검색 옵션")
    use_rag = st.toggle("지식베이스 검색 사용 (RAG Mode)", value=True)
    
    if use_rag:
        st.success("✅ **RAG 모드 ON**\n\nAI가 업로드된 문서 내용을 우선적으로 참고하여 답변합니다.")
    else:
        st.warning("⚠️ **RAG 모드 OFF**\n\nAI가 GPT-4의 기본 지식만 사용하여 답변합니다.")

# --- 메인 화면: 채팅 인터페이스 ---

# 세션 상태(Session State)를 사용하여 채팅 기록을 관리합니다.
if "messages" not in st.session_state:
    st.session_state.messages = []

# 저장된 채팅 기록을 화면에 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # 답변에 참고 문헌(Sources) 정보가 있다면 Expander로 표시
        if "sources" in message and message["sources"]:
            with st.expander("📚 참고한 문서 소스 확인하기"):
                for source in message["sources"]:
                    st.write(f"- {source}")

# 사용자 입력 처리
if prompt := st.chat_input("질문을 입력하세요... (예: 이 문서의 핵심 내용은 무엇인가요?)"):
    # 1. 사용자 메시지 화면 표시 및 저장
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. AI 응답 요청
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        sources = []
        
        try:
            with st.spinner("답변을 생성하고 있습니다..."):
                # 백엔드 API로 질문 전송
                payload = {"query": prompt, "use_rag": use_rag}
                response = requests.post(f"{API_URL}/chat", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    full_response = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    # 답변 표시
                    message_placeholder.markdown(full_response)
                    
                    # 소스 표시
                    if sources:
                        with st.expander("📚 참고한 문서 소스 확인하기"):
                            for source in sources:
                                st.write(f"- {source}")
                else:
                    full_response = f"⚠️ 에러가 발생했습니다: {response.text}"
                    message_placeholder.error(full_response)
                    
        except Exception as e:
            full_response = f"🚫 서버 연결 실패: {e}"
            message_placeholder.error(full_response)
            
        # 3. AI 응답 저장
        st.session_state.messages.append({
            "role": "assistant", 
            "content": full_response,
            "sources": sources
        })
