from fastapi import FastAPI
import uvicorn
import dotenv

dotenv.load_dotenv()

app = FastAPI()

@app.get("/")
async def hello():
    return {'result': 'hello'}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
