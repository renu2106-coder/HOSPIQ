import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database.session import engine, Base, SessionLocal
from backend.models import *
from backend.synthetic_data.seed_data import generate_department_files, seed_database

# API Routers
from backend.api.auth import router as auth_router
from backend.api.users import router as users_router
from backend.api.patients import router as patients_router
from backend.api.records import router as records_router
from backend.api.documents import router as documents_router
from backend.api.validation import router as validation_router
from backend.api.alerts import router as alerts_router
from backend.api.corrections import router as corrections_router
from backend.api.uploads import router as uploads_router
from backend.api.agents import router as agents_router
from backend.api.audit import router as audit_router
from backend.api.dashboard import router as dashboard_router
from backend.api.tools_api import router as tools_router

app = FastAPI(
    title="HOSPIQ API",
    description="Hospital Information & Quality Intelligence System — Multi-Agent Healthcare Management Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware for React Vite Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(patients_router)
app.include_router(records_router)
app.include_router(documents_router)
app.include_router(validation_router)
app.include_router(alerts_router)
app.include_router(corrections_router)
app.include_router(uploads_router)
app.include_router(agents_router)
app.include_router(audit_router)
app.include_router(dashboard_router)
app.include_router(tools_router)

@app.on_event("startup")
def on_startup():
    """Ensure database tables and initial synthetic department data are initialized."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from backend.models.models import Patient
        from backend.synthetic_data.seed_data import seed_real_time_clinical_cases
        if db.query(Patient).count() == 0:
            print("[HOSPIQ Startup] Seeding initial database with synthetic multi-department data...")
            generate_department_files()
            seed_database(db)
            print("[HOSPIQ Startup] Seeding completed.")
        else:
            # Ensure real-time hospital diagnostic cases (P016 - P020) are integrated
            seed_real_time_clinical_cases(db)
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "HOSPIQ",
        "version": "1.0.0",
        "database": "SQLite Connected",
        "role_access_control": "Enforced"
    }


# Mount Frontend Built Static Files & Single-Port SPA Handler
dist_path = Path(__file__).resolve().parent.parent / "frontend" / "dist"
assets_path = dist_path / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

@app.get("/{full_path:path}")
def serve_frontend_spa(full_path: str):
    # Do not intercept API or docs routes
    if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="API endpoint not found")
    index_file = dist_path / "index.html"
    if index_file.exists():
        return FileResponse(
            str(index_file),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"message": "Frontend build files not found. Run 'npm run build' inside frontend."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=True)

