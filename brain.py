import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from pymupdf4llm import to_markdown
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
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
    docs_dir = "./documents"
    
    # Check if documents directory exists
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
        print(f"Created '{docs_dir}' directory. Please place your PDFs there.")
        return None
        
    if os.path.exists(chroma_db_path) and os.listdir(chroma_db_path):
        print("Loading existing vector database...")
        vector_store = Chroma(persist_directory=chroma_db_path, embedding_function=embeddings)
    else:
        # 1. Load all PDFs in the documents directory
        pdf_files = [f for f in os.listdir(docs_dir) if f.lower().endswith(".pdf")]
        
        if not pdf_files:
            print(f"No PDFs found in the '{docs_dir}' directory.")
            return None
            
        all_docs = []
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(docs_dir, pdf_file)
            print(f"Processing: {pdf_file}...")
            
            try:
                # Use PyMuPDF4LLM to extract text as Markdown (preserves tables)
                md_text = to_markdown(pdf_path)
                
                # PREPEND the source name to the text itself so the LLM physically reads it
                content_with_source = f"DOCUMENT SOURCE: {pdf_file}\n\n{md_text}"
                
                # Wrap it in a single Langchain Document
                doc = Document(page_content=content_with_source, metadata={"source": pdf_file})
                
                # Split the text into manageable pieces
                docs = text_splitter.split_documents([doc])
                
                # Filter out empty documents
                docs = [doc for doc in docs if doc.page_content.strip()]
                
                if docs:
                    all_docs.extend(docs)
                    print(f"  Successfully extracted {len(docs)} chunks from {pdf_file}")
                else:
                    print(f"  Warning: Standard extraction failed for {pdf_file}. Trying OCR instead...")
                    if OCR_AVAILABLE:
                        try:
                            images = convert_from_path(pdf_path)
                            ocr_text = ""
                            for i, image in enumerate(images):
                                ocr_text += f"\n--- Page {i+1} ---\n"
                                ocr_text += pytesseract.image_to_string(image)
                            
                            if ocr_text.strip():
                                # Create a single LangChain Document from the OCR text
                                doc = Document(page_content=ocr_text, metadata={"source": pdf_file})
                                ocr_docs = text_splitter.split_documents([doc])
                                all_docs.extend(ocr_docs)
                                print(f"  Successfully extracted {len(ocr_text)} characters from {pdf_file} using OCR.")
                            else:
                                print(f"  ERROR: OCR failed to extract text from {pdf_file}.")
                        except Exception as e:
                            print(f"  OCR failed for {pdf_file}: {e}")
                    else:
                        print(f"  ERROR: Could not extract text from {pdf_file} and OCR is not available.")
                        
            except Exception as e:
                print(f"  Error loading {pdf_file}: {e}")
        
        if not all_docs:
            print("ERROR: No text could be extracted from any of the provided PDFs.")
            return None

        print(f"Building vector database from {len(all_docs)} total document chunks...")
        vector_store = Chroma.from_documents(all_docs, embeddings, persist_directory=chroma_db_path)
    
    # 4. Setup the Multilingual Chat Brain with Context Management
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", google_api_key=google_api_key)
    
    template = """You are a highly precise college assistant. Your job is to answer questions using ONLY the provided documents.
    
CRITICAL MULTI-DOCUMENT RULES:
1. You may receive chunks of text from multiple different PDFs. Look at the "DOCUMENT SOURCE:" written at the top of the text chunks.
2. If the user asks a broad question, ALWAYS separate your answer clearly based on the documents. Example: "According to the Class Timetable... According to the VTU Exam Timetable..."

CRITICAL FORMATTING INSTRUCTIONS - YOU MUST OBEY THIS:
1. If the user asks ANY question about a timetable, schedule, or list of classes/exams, YOU MUST OUTPUT A MARKDOWN TABLE. 
2. DO NOT use bullet points. DO NOT use plain text lists. ONLY use a Markdown table.
3. Example table format:
| Time | Subject |
| :--- | :--- |
| 9:00-10:00 AM | ML Class |
4. DO NOT include a "Document Source" column in the table itself. If you need to cite the source, mention it in the introductory text before the table.

CRITICAL INSTRUCTIONS FOR TIMETABLES & BREAKS: 
Timetables in the context are often flattened text. When answering about a specific day:
1. First, find the row starting with the Day (e.g., "MON", "TUE", "WED", "THU", "FRI", "SAT").
2. The subjects listed after the day correspond sequentially to the time slots (e.g., 9:00-10:00, 10:00-11:00, 11:15-12:15, 12:15-1:15, 2:00-2:55).
3. YOU MUST ALWAYS inject the following breaks into the daily schedule table, in their chronological order:
   - | 11:00-11:15 AM | Tea Break |
   - | 1:15-2:00 PM | Lunch Break |
4. If reading an Exam Date table, match the Subject Code explicitly to the Date listed.

Context:
{context}

Question: {question}

Assistant (Remember to output a Markdown Table if applicable!):"""

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