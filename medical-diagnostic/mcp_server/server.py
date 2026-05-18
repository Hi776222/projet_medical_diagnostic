from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {
        "message": "MCP Server running"
    }


@app.get("/reference")
async def reference():

    return {
        "guideline": "Hydratation et surveillance recommandées."
    }