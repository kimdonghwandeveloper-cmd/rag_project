import shutil
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.backend.rag import ingest_pdf, get_answer

# API 라우터를 생성합니다. 
# 라우터는 main.py에서 등록하여 사용합니다.
router = APIRouter()

# 업로드된 파일이 임시 저장될 디렉토리 경로
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# [요청 모델] 채팅 요청 데이터 스키마 정의
class ChatRequest(BaseModel):
    query: str       # 사용자의 질문
    use_rag: bool = True # RAG 사용 여부 (기본값: True)

# [응답 모델] 채팅 응답 데이터 스키마 정의
class ChatResponse(BaseModel):
    answer: str      # LLM의 답변
    sources: list[str] # 참고한 문서 출처 목록

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    [POST] /upload
    PDF 파일을 받아 시스템에 업로드하고, LangChain을 통해 벡터 스토어에 추가합니다.
    
    Args:
        file: 업로드할 PDF 파일
        
    Returns:
        JSON: 처리 결과 메세지와 추가된 청크 개수
    """
    # 1. 파일 확장자 검사
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_path = os.path.join(DATA_DIR, file.filename)
    
    try:
        # 2. 파일 저장
        # 비동기 파일 처리를 위해 shutil을 사용합니다.
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 3. RAG Ingestion 실행 (rag.py)
        # 파일을 청킹하고 벡터화하여 MongoDB에 저장합니다.
        num_chunks = ingest_pdf(file_path)
        
        return {"message": f"Successfully processed {file.filename}", "chunks_added": num_chunks}
        
    except Exception as e:
        # 오류 발생 시 로컬에 저장된 임시 파일 삭제
        if os.path.exists(file_path):
            os.remove(file_path)
        # 상세 에러 메시지를 포함하여 500 에러 반환
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    [POST] /chat
    사용자의 질문을 받아 답변을 반환합니다. 
    use_rag 플래그에 따라 RAG 검색 또는 일반 LLM 답변을 수행합니다.
    
    Args:
        request: 사용자 질문과 옵션이 담긴 ChatRequest 객체
        
    Returns:
        ChatResponse: 답변 및 소스 정보
    """
    try:
        answer, sources = get_answer(request.query, request.use_rag)
        return ChatResponse(answer=answer, sources=sources)
    except Exception as e:
        print(f"Error during chat processing: {e}") # 서버 로그에 에러 출력
        raise HTTPException(status_code=500, detail=str(e))
