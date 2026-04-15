from fastapi import FastAPI, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from fastapi.middleware.cors import CORSMiddleware

# Banco de dados de Produção (Supabase)
DATABASE_URL = "postgresql://postgres.wtwgxjxshhfacztnlduy:shaukan191099@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"
engine = create_engine(DATABASE_URL) # Tiramos o connect_args
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ConsultaHistorico(Base):
    __tablename__ = "historico_consultas"
    id = Column(Integer, primary_key=True, index=True)
    ip_usuario = Column(String(50), index=True)
    tipo_cliente = Column(String(20))
    valor_compra = Column(Float)
    cashback_gerado = Column(Float)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompraRequest(BaseModel):
    valor_original: float
    desconto_percentual: float
    is_vip: bool

def calcular_cashback(valor_original, desconto_percentual, is_vip):
    valor_final = valor_original * (1 - (desconto_percentual / 100))
    cashback_base = valor_final * 0.05
    cashback_bonus_vip = cashback_base * 0.10 if is_vip else 0
    cashback_total = cashback_base + cashback_bonus_vip
    if valor_final > 500:
        cashback_total *= 2
    return round(cashback_total, 2)

@app.post("/calcular")
def calcular(request: Request, compra: CompraRequest):
    user_ip = request.client.host 
    cashback_final = calcular_cashback(compra.valor_original, compra.desconto_percentual, compra.is_vip)
    tipo = "VIP" if compra.is_vip else "Padrão"
    
    db = SessionLocal()
    nova_consulta = ConsultaHistorico(
        ip_usuario=user_ip, tipo_cliente=tipo, valor_compra=compra.valor_original, cashback_gerado=cashback_final
    )
    db.add(nova_consulta)
    db.commit()
    db.refresh(nova_consulta)
    db.close()
    
    return {"cashback": cashback_final}

@app.get("/historico")
def obter_historico(request: Request):
    user_ip = request.client.host
    db = SessionLocal()
    historico = db.query(ConsultaHistorico).filter(ConsultaHistorico.ip_usuario == user_ip).all()
    db.close()
    return historico