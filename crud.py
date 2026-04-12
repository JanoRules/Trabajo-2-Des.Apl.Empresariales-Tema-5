from sqlalchemy.orm import Session
from datetime import datetime
from models import engine, Pedido

# ─────────────────────────────────────────────
# FUNCIONES CRUD (LÓGICA DE NEGOCIO)
# ─────────────────────────────────────────────

def _generar_id() -> str:
    """Genera un ID correlativo automático: PED-001, PED-002, ..."""
    with Session(engine) as session:
        ultimo = session.query(Pedido).order_by(Pedido.id.desc()).first()
        if ultimo:
            # Extraer el número del último ID y sumarle 1
            try:
                numero = int(ultimo.id_pedido.split("-")[-1]) + 1
            except ValueError:
                numero = ultimo.id + 1
        else:
            numero = 1
        return f"PED-{numero:03d}"


def obtener_todos() -> list[Pedido]:
    with Session(engine) as session:
        return session.query(Pedido).order_by(Pedido.id.desc()).all()

def buscar_por_id(id_pedido: str) -> Pedido | None:
    with Session(engine) as session:
        return session.query(Pedido).filter_by(id_pedido=id_pedido).first()

def registrar(datos: dict) -> str:
    """
    Registra un pedido con ID generado automáticamente.
    Devuelve el ID asignado, o None si ocurrió un error.
    """
    with Session(engine) as session:
        id_pedido = _generar_id()
        datos["id_pedido"] = id_pedido
        nuevo = Pedido(**datos)
        session.add(nuevo)
        session.commit()
        return id_pedido

def actualizar_estado(id_pedido: str, nuevo_estado: str) -> None:
    with Session(engine) as session:
        pedido = session.query(Pedido).filter_by(id_pedido=id_pedido).first()
        if pedido:
            pedido.estado = nuevo_estado
            pedido.fecha  = datetime.now()
            session.commit()

def conteo_por_estado() -> dict:
    todos = obtener_todos()
    return {
        "Pendiente":  sum(1 for p in todos if p.estado == "Pendiente"),
        "En Proceso": sum(1 for p in todos if p.estado == "En Proceso"),
        "Entregado":  sum(1 for p in todos if p.estado == "Entregado"),
    }
