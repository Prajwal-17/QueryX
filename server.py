from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from brain import initialize_bot
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DBIT Student Assistant API", description="Multilingual API for Student Queries")

# Mount static directory for frontend assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Allow all origins for easy testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to hold our LangChain bot
bot_chain = None

@app.on_event("startup")
async def startup_event():
    """Initializes the chat brain once when the server starts."""
    global bot_chain
    print("Initializing DBIT Student Assistant...")
    bot_chain = initialize_bot()
    if bot_chain:
        print("Bot properly initialized and ready!")
    else:
        print("WARNING: Bot initialization failed. Did you configure GOOGLE_API_KEY?")

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint to send student queries to the brain.
    Receives JSON: { "query": "Your question here in any language" }
    """
    global bot_chain
    if not bot_chain:
        raise HTTPException(
            status_code=500, 
            detail="Bot is not initialized. Check your GOOGLE_API_KEY in the .env file."
        )
    
    try:
        response = bot_chain.invoke({"question": request.query})
        return ChatResponse(answer=response["answer"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Runs the server locally on port 8000
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
