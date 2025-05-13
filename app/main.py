from fastapi import FastAPI
from app.routes import public, user, admin

app = FastAPI()

app.include_router(public.router)
app.include_router(user.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {"message": "Toy Exchange API"}