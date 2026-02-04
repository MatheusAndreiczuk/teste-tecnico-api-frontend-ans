from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import operadoras, estatisticas

app = FastAPI(
    title="ANS Operadoras API",
    description="API para consulta de operadoras de planos de saúde e suas despesas",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(operadoras.router, prefix="/api", tags=["Operadoras"])
app.include_router(estatisticas.router, prefix="/api", tags=["Estatísticas"])


@app.get("/")
def root():
    return {"message": "ANS Operadoras API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
