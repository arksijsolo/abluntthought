from fastapi import FastAPI
from app.routers import blog, admin, auth

app = FastAPI()

app.include_router(blog.router)
app.include_router(admin.router)
app.include_router(auth.router)