from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from app.backend.db import get_vector_collection
from typing import Tuple, List

# MongoDB Atlas Search Index 이름 상수 정의
# Atlas 대시보드에서 생성한 Search Index의 이름과 일치해야 합니다.
INDEX_NAME = "vector_index" 

from langchain_core.documents import Document

def ingest_text(text: str) -> int:
    """
    텍스트를 직접 입력받아 청킹(Chunking) 후 MongoDB에 벡터로 저장합니다.
    
    Args:
        text (str): 사용자가 입력한 텍스트
        
    Returns:
        int: 저장된 문서 청크(Chunk)의 개수
    """
    # 1. 텍스트를 Document 객체로 변환
    docs = [Document(page_content=text, metadata={"source": "User Input"})]

    # 2. 텍스트 분할 (Split)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(docs)

    # 3. 임베딩 및 저장 (Embed & Store)
    collection = get_vector_collection()
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name=INDEX_NAME
    )
    vector_store.add_documents(splits)
    
    return len(splits)

def ingest_pdf(file_path: str) -> int:
    """
    PDF 파일을 로드하고, 텍스트를 청크(Chunk)로 분할하여 MongoDB에 벡터로 저장합니다.
    
    Args:
        file_path (str): 업로드된 PDF 파일의 절대 경로
        
    Returns:
        int: 저장된 문서 청크(Chunk)의 개수
    """
    # 1. PDF 로드 (Load)
    # PyPDF를 사용하여 PDF의 텍스트를 추출합니다.
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # 2. 텍스트 분할 (Split)
    # 문맥 유지를 위해 200자의 중복(overlap)을 두고 1000자 단위로 자릅니다.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    splits = text_splitter.split_documents(docs)

    # 3. 임베딩 및 저장 (Embed & Store)
    collection = get_vector_collection()
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # MongoDBAtlasVectorSearch를 초기화하고 문서를 추가합니다.
    # 이 과정에서 OpenAI API를 호출하여 임베딩을 생성하므로 비용이 발생합니다.
    vector_store = MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name=INDEX_NAME
    )
    vector_store.add_documents(splits)
    
    return len(splits)

def get_answer(query: str, use_rag: bool = True) -> Tuple[str, List[str]]:
    """
    사용자의 질문에 대한 답변을 생성합니다.
    
    Args:
        query (str): 사용자의 질문 텍스트
        use_rag (bool): RAG(검색 증강 생성을) 사용할지 여부
        
    Returns:
        Tuple[str, List[str]]: (답변 텍스트, 참고한 소스 목록)
    """
    # GPT-3.5-turbo 모델 초기화 (비용 절감 및 무료 티어 호환)
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    if use_rag:
        # === RAG 파이프라인 (검색 + 생성) ===
        
        # 1. Vector Store 연결
        collection = get_vector_collection()
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embeddings,
            index_name=INDEX_NAME
        )
        
        # 2. Retriever 설정
        # 유사도 기반 검색(similarity), 상위 3개 문서(k=3) 조회
        retriever = vector_store.as_retriever(
            search_type="similarity", 
            search_kwargs={"k": 3}
        )
        
        # 3. 프롬프트 템플릿 구성
        # context: 검색된 문서 내용, question: 사용자 질문
        template = """Answer the question based only on the following context:
        {context}
        
        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)
        
        # 문서 리스트를 하나의 문자열로 합치는 헬퍼 함수
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # 4. 체인 구성 (LCEL: LangChain Expression Language)
        # context는 retriever를 통해 문서를 가져와 format_docs로 포맷팅합니다.
        # question은 그대로 전달됩니다.
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser() # Output을 문자열로 파싱
        )
        
        # 5. 실행 및 메타데이터 추출
        # 검색된 문서를 별도로 가져와서 출처(Source) 정보를 추출합니다.
        retrieved_docs = retriever.invoke(query)
        
        # 체인 실행으로 답변 생성
        response_text = rag_chain.invoke(query)
        
        # 소스 정보 포맷팅 (파일명 + 페이지 번호)
        sources = [f"{doc.metadata.get('source', 'Unknown')} (Page {doc.metadata.get('page', 0)})" for doc in retrieved_docs]
        
        return response_text, sources

    else:
        # === 일반 LLM 파이프라인 (검색 없음) ===
        # 모델이 학습한 지식만으로 답변을 생성합니다.
        response_text = llm.invoke(query).content
        return response_text, []
