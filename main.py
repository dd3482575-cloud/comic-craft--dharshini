from fastapi import FastAPI
from routes import router

app = FastAPI(
    title="ComicCraft API",
    description="AI Comic Story Creator using Gemini Models",
    version="1.0.0"
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "ComicCraft API is running!"
    }
