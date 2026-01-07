from fastapi import FastAPI
from app.backend.api import router

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title="RAG Chatbot API",
    description="RAG(Retrieval-Augmented Generation)와 일반 LLM을 비교할 수 있는 API 서버입니다.",
    version="1.0.0"
)

# API 라우터 등록 (app/backend/api.py)
app.include_router(router)

@app.get("/")
def read_root():
    """서버 생존 확인용 루트 엔드포인트"""
    return {"message": "Welcome to the RAG Chatbot API. Docs available at /docs"}

if __name__ == "__main__":
    # 개발 환경에서 직접 실행 시 uvicorn으로 서버 구동
    import uvicorn
    uvicorn.run("app.backend.main:app", host="0.0.0.0", port=8000, reload=True)
