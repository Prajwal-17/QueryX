import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.schema import Document
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Load environment variables
load_dotenv()

def initialize_bot():
    # 0. Check API key first before doing anything
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if not google_api_key or google_api_key in ("GOOGLE_API_KEY", "google_api_key"):
        print("Please set a valid GOOGLE_API_KEY in the .env file")
        return None

    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=google_api_key)

    # 3. Reuse existing ChromaDB if already built, otherwise build from PDF
    chroma_db_path = "./chroma_db"
    if os.path.exists(chroma_db_path) and os.listdir(chroma_db_path):
        print("Loading existing vector database...")
        vector_store = Chroma(persist_directory=chroma_db_path, embedding_function=embeddings)
    else:
        # 1. Load the requested PDF context
        try:
            loader = PyPDFLoader("AES.pdf")
            data = loader.load()
        except Exception as e:
            print(f"Error loading AES.pdf: {e}")
            print("Please ensure AES.pdf exists in the directory.")
            return None

        # 2. Split the text into manageable pieces
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.split_documents(data)

        # Filter out empty documents
        docs = [doc for doc in docs if doc.page_content.strip()]

        if not docs:
            print("Warning: Standard extraction failed. Trying OCR instead...")
            if OCR_AVAILABLE:
                try:
                    images = convert_from_path("AES.pdf")
                    ocr_text = ""
                    for i, image in enumerate(images):
                        ocr_text += f"\n--- Page {i+1} ---\n"
                        ocr_text += pytesseract.image_to_string(image)
                    
                    if ocr_text.strip():
                        # Create a single LangChain Document from the OCR text
                        doc = Document(page_content=ocr_text, metadata={"source": "AES.pdf tice(OCR)"})
                        docs = text_splitter.split_documents([doc])
                        print(f"Successfully extracted {len(ocr_text)} characters using OCR.")
                except Exception as e:
                    print(f"OCR failed: {e}")
            
            if not docs:
                print("ERROR: No text could be extracted from AES.pdf.")
                print("Your PDF is either empty, scanned with unreadable text, or OCR failed.")
                return None

        print(f"Building vector database from {len(docs)} document chunks...")
        vector_store = Chroma.from_documents(docs, embeddings, persist_directory=chroma_db_path)
    
    # 4. Setup the Multilingual Chat Brain with Context Management
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", google_api_key=google_api_key)
    
    template = """Answer this according to the pdf given only'.

Context:
{context}

Question: {question}

Assistant:"""

    QA_PROMPT = PromptTemplate(
        template=template, input_variables=["context", "question"]
    )
    
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT}
    )
    
    return qa_chain

if __name__ == "__main__":
    qa_chain = initialize_bot()
    if qa_chain:
        print("DBIT Student Assistant Initialized. Type 'exit' to quit.")
        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['exit', 'quit']:
                    break
                    
                response = qa_chain.invoke({"question": user_input})
                print(f"Assistant: {response['answer']}\n")
            except Exception as e:
                print(f"Error processing query: {e}")