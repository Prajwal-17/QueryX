from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os

os.environ["GOOGLE_API_KEY"] = "dummy"

try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    print("embeddings ok")
except Exception as e:
    print(e)
    
try:
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview")
    print("llm ok")
except Exception as e:
    print(e)
