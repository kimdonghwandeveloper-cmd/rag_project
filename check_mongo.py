import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

def check_mongo():
    uri = os.getenv("MONGO_URI")
    print(f"Checking connection to: {uri[:20]}...") 
    
    try:
        client = MongoClient(uri)
        # 1. Ping test
        client.admin.command('ping')
        print("✅ MongoDB Connection Successful!")
        
        # 2. Database check
        db = client["rag_db"]
        print(f"✅ Database 'rag_db' selected.")
        
        # 3. Collection check
        collections = db.list_collection_names()
        print(f"📂 Collections in 'rag_db': {collections}")
        
        if "embeddings" not in collections:
            print("⚠️ 'embeddings' collection does not exist yet. It will be created on first insert.")
        else:
            count = db["embeddings"].count_documents({})
            print(f"📊 Documents in 'embeddings': {count}")
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    check_mongo()
