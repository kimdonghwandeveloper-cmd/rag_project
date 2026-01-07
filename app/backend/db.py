from pymongo import MongoClient
from pymongo.collection import Collection
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
# 이 함수는 앱 시작 시 한 번 호출되어야 하지만, 안정을 위해 모듈 레벨에서 호출합니다.
load_dotenv()

def get_mongo_client() -> MongoClient:
    """
    MongoDB 클라이언트를 생성하고 반환합니다.
    
    환경 변수 'MONGO_URI'가 설정되어 있어야 합니다.
    설정되지 않은 경우 ValueError를 발생시킵니다.
    
    Returns:
        MongoClient: MongoDB 클라이언트 인스턴스
    """
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        # 치명적인 오류이므로 예외를 발생시켜 앱이 잘못된 상태로 시작되는 것을 방지합니다.
        raise ValueError("MONGO_URI environment variable is not set. .env 파일을 확인해주세요.")
    
    # MongoClient는 내부적으로 커넥션 풀을 관리하므로 매번 새로 생성해도 괜찮으나,
    # 실제 프로덕션에서는 의존성 주입(Dependency Injection)을 사용하는 것이 좋습니다.
    return MongoClient(mongo_uri)

def get_vector_collection() -> Collection:
    """
    RAG 시스템에서 사용할 Vector Search 전용 컬렉션을 반환합니다.
    
    Database: rag_db
    Collection: embeddings
    
    Returns:
        Collection: MongoDB 컬렉션 객체
    """
    client = get_mongo_client()
    db = client["rag_db"]
    collection = db["embeddings"]
    return collection
