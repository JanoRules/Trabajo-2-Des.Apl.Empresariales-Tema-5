# models.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Session, relationship
from datetime import datetime
import hashlib
import os

# ─────────────────────────────────────────────
# BASE Y MODELOS ORM
# ─────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class Pedido(Base):
    __tablename__ = "pedidos"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    id_pedido      = Column(String(50), unique=True, nullable=False)
    codigo_acceso  = Column(String(20), unique=True, nullable=True)
    cliente        = Column(String(100), nullable=False)
    producto       = Column(String(100), nullable=False)
    cantidad       = Column(Integer, nullable=False, default=1)
    responsable    = Column(String(100), nullable=False)
    estado         = Column(String(20), nullable=False, default="Pendiente")
    notas          = Column(String(300), nullable=True)
    fecha          = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    eliminado      = Column(Integer, default=0)  # 0 = activo, 1 = eliminado (soft delete)

    # Relación con historial
    historial = relationship("HistorialCambio", back_populates="pedido", cascade="all, delete-orphan")


class HistorialCambio(Base):
    """
    Registra cada modificación realizada a un pedido.
    Permite auditar quién cambió qué y cuándo.
    """
    __tablename__ = "historial_cambios"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id   = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    campo       = Column(String(50), nullable=False)   # ej: "estado", "producto", "notas"
    valor_antes = Column(Text, nullable=True)
    valor_despues = Column(Text, nullable=True)
    usuario     = Column(String(100), nullable=False)  # nombre del usuario que hizo el cambio
    fecha       = Column(DateTime, default=datetime.now)

    pedido = relationship("Pedido", back_populates="historial")


class Usuario(Base):
    """
    Roles disponibles:
      - admin        → acceso total + gestión de usuarios
      - responsable  → registrar pedidos, consultar y cambiar estados de sus propios pedidos
    """
    __tablename__ = "usuarios"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    username      = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)  # salt:hash (pbkdf2)
    nombre        = Column(String(100), nullable=False)
    rol           = Column(String(20), nullable=False, default="responsable")
    activo        = Column(Integer, default=1)          # 1 = activo, 0 = deshabilitado
    intentos_fallidos = Column(Integer, default=0)      # contador de intentos de login fallidos
    bloqueado_hasta   = Column(DateTime, nullable=True) # bloqueo temporal tras múltiples fallos


# ─────────────────────────────────────────────
# CONEXIÓN Y CREACIÓN DE TABLAS
# ─────────────────────────────────────────────

engine = create_engine("sqlite:///pedidos.db", echo=False)
Base.metadata.create_all(engine)


def _hash_password(password: str, salt: bytes = None) -> str:
    """
    Genera un hash seguro con PBKDF2-HMAC-SHA256 + salt aleatorio.
    Formato almacenado: '<salt_hex>:<key_hex>'
    """
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return salt.hex() + ":" + key.hex()


def _seed() -> None:
    """Crea el usuario administrador por defecto si la tabla está vacía."""
    with Session(engine) as session:
        if session.query(Usuario).count() == 0:
            admin = Usuario(
                username="admin",
                password_hash=_hash_password("admin123"),
                nombre="Administrador",
                rol="admin",
                activo=1,
            )
            session.add(admin)
            session.commit()


_seed()
