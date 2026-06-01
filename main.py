from fastapi import FastAPI
from routers import home, admin

app = FastAPI(title="A Blunt Thought API Engine")

# Wire up core domain routers to backend engine
app.include_router(home.router)
app.include_router(admin.router, prefix="/admin")