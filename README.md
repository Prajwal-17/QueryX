# DBIT Student Assistant / College Bot

## What is this project?
This project is a RAG-based (Retrieval-Augmented Generation) College Chatbot tailored to answer student queries using information from specific college documents. The system reads source PDFs, processes their text (including OCR for scanned pages), and converts this data into a searchable vector database. A frontend web interface allows users to ask questions, which are then passed to Google's Gemini LLM. The AI formulates precise answers based *only* on the context retrieved from the database, ensuring accurate and strictly relevant responses.

## Tech Stack
**Backend & AI Engine:**
- **Python**: The core language used for the backend code.
- **FastAPI**: A high-performance web framework used to create the API (`/chat`) and serve the frontend files.
- **LangChain**: An orchestration framework that connects the PDF parsing, memory, embedding, and LLM queries into a cohesive pipeline.
- **Google Generative AI (Gemini)**: Uses `gemini-3.1-flash-lite-preview` for conversational responses and `gemini-embedding-001` to generate vector representations of text.
- **ChromaDB**: A lightweight, SQLite-based vector database used to persist document embeddings locally.
- **PyPDFLoader / pdf2image / pytesseract**: Used to extract text from PDFs, falling back to Tesseract OCR when straightforward text extraction isn't possible.

**Frontend:**
- **HTML/CSS/Vanilla JavaScript**: A simple yet effective set of static files located in the `static/` directory to provide a browser-based chat interface.
