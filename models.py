from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Session
from datetime import datetime

# ─────────────────────────────────────────────
# BASE Y MODELO ORM
# ─────────────────────────────────────────────

class Base(DeclarativeBase):
    pass

class Pedido(Base):
    __tablename__ = "pedidos"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    id_pedido   = Column(String(50), unique=True, nullable=False)
    cliente     = Column(String(100), nullable=False)
    producto    = Column(String(100), nullable=False)
    cantidad    = Column(Integer, nullable=False, default=1)
    responsable = Column(String(100), nullable=False)
    estado      = Column(String(20), nullable=False, default="Pendiente")
    notas       = Column(String(300), nullable=True)
    fecha       = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# ─────────────────────────────────────────────
# CONEXIÓN Y CREACIÓN DE TABLAS
# ─────────────────────────────────────────────

engine = create_engine("sqlite:///pedidos.db", echo=False)
Base.metadata.create_all(engine)
