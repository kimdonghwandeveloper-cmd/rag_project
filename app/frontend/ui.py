import requests
import os

# 백엔드 API 기본 주소
# Docker 환경에서는 환경 변수에서 URL을 가져옵니다.
API_URL = os.getenv("API_URL", "http://localhost:8000")

# --- 페이지 설정 ---
st.set_page_config(
    page_title="DocuMind AI",
    page_icon="🧠",
    layout="wide"
)

st.title("DocuMind AI")
st.markdown("""
문서와 텍스트를 지식베이스에 업로드하고, AI와 대화하며 정확한 정보를 얻으세요.
지식베이스 활용 유무에 따른 답변 차이를 직접 비교할 수 있습니다.
""")

# --- 사이드바: 설정 및 데이터 관리 ---
with st.sidebar:
    st.header("Settings & Data")
    
    # 1. 지식베이스 추가 섹션 (탭으로 구분)
    st.subheader("Add Knowledge Base")
    
    tab1, tab2 = st.tabs(["PDF Upload", "Text Input"])
    
    # [Tab 1] PDF 업로드
    with tab1:
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
        if uploaded_file is not None:
            if st.button("Upload PDF", key="pdf_btn"):
                with st.spinner("Processing PDF..."):
                    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                    try:
                        response = requests.post(f"{API_URL}/upload", files=files)
                        if response.status_code == 200:
                            chunks = response.json().get('chunks_added')
                            st.success(f"Success! Added {chunks} chunks.")
                        else:
                            st.error(f"Failed: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # [Tab 2] 텍스트 입력
    with tab2:
        user_text = st.text_area("Enter text to add to knowledge base", height=200)
        if st.button("Add Text", key="text_btn"):
            if user_text.strip():
                with st.spinner("Processing text..."):
                    try:
                        response = requests.post(f"{API_URL}/upload/text", json={"text": user_text})
                        if response.status_code == 200:
                            chunks = response.json().get('chunks_added')
                            st.success(f"Success! Added {chunks} chunks.")
                        else:
                            st.error(f"Failed: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please enter some text.")

    st.divider()

    # 2. RAG 옵션 토글
    st.subheader("Search Options")
    use_rag = st.toggle("Use Knowledge Base (RAG)", value=True)
    
    if use_rag:
        st.success("Mode: RAG (Retrieval Augmented Generation)")
    else:
        st.warning("Mode: General LLM (GPT Only)")

# --- 메인 화면: 채팅 인터페이스 ---

if "messages" not in st.session_state:
    st.session_state.messages = []

# 채팅 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("Reference Sources"):
                for source in message["sources"]:
                    st.write(f"- {source}")

# 사용자 입력 처리
if prompt := st.chat_input("Ask a question..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        sources = []
        
        try:
            with st.spinner("Thinking..."):
                payload = {"query": prompt, "use_rag": use_rag}
                response = requests.post(f"{API_URL}/chat", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    full_response = data.get("answer", "")
                    sources = data.get("sources", [])
                    
                    message_placeholder.markdown(full_response)
                    
                    if sources:
                        with st.expander("Reference Sources"):
                            for source in sources:
                                st.write(f"- {source}")
                else:
                    full_response = f"Error: {response.text}"
                    message_placeholder.error(full_response)
                    
        except Exception as e:
            full_response = f"Connection Error: {e}"
            message_placeholder.error(full_response)
            
        st.session_state.messages.append({
            "role": "assistant", 
            "content": full_response,
            "sources": sources
        })
