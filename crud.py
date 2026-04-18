# crud.py
import secrets
import string
from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import Session
from models import engine, Pedido, HistorialCambio

# ─────────────────────────────────────────────
# GENERADORES INTERNOS
# ─────────────────────────────────────────────

def _generar_id() -> str:
    """Genera un ID correlativo automático: PED-001, PED-002, ..."""
    with Session(engine) as session:
        ultimo = session.query(Pedido).order_by(Pedido.id.desc()).first()
        if ultimo:
            try:
                numero = int(ultimo.id_pedido.split("-")[-1]) + 1
            except ValueError:
                numero = ultimo.id + 1
        else:
            numero = 1
        return f"PED-{numero:03d}"


def _generar_codigo_acceso() -> str:
    """
    Genera un código de acceso único y criptográficamente seguro.
    Formato: XXXX-XXXX (letras mayúsculas + dígitos), ej: A3BK-9ZT2
    Usa `secrets` en lugar de `random` para mayor seguridad.
    """
    caracteres = string.ascii_uppercase + string.digits
    with Session(engine) as session:
        while True:
            codigo = (
                "".join(secrets.choice(caracteres) for _ in range(4))
                + "-"
                + "".join(secrets.choice(caracteres) for _ in range(4))
            )
            if not session.query(Pedido).filter_by(codigo_acceso=codigo).first():
                return codigo


def _registrar_cambio(
    session: Session,
    pedido: Pedido,
    campo: str,
    valor_antes,
    valor_despues,
    usuario_nombre: str,
) -> None:
    """Inserta una fila en historial_cambios si el valor realmente cambió."""
    if str(valor_antes) != str(valor_despues):
        session.add(HistorialCambio(
            pedido_id=pedido.id,
            campo=campo,
            valor_antes=str(valor_antes) if valor_antes is not None else "",
            valor_despues=str(valor_despues) if valor_despues is not None else "",
            usuario=usuario_nombre,
            fecha=datetime.now(),
        ))


# ─────────────────────────────────────────────
# LECTURA
# ─────────────────────────────────────────────

def obtener_todos(solo_activos: bool = True) -> list[Pedido]:
    """Devuelve todos los pedidos. Por defecto excluye los eliminados (soft delete)."""
    with Session(engine) as session:
        q = session.query(Pedido)
        if solo_activos:
            q = q.filter(Pedido.eliminado == 0)
        return q.order_by(Pedido.id.desc()).all()


def obtener_por_responsable(nombre_responsable: str) -> list[Pedido]:
    """Devuelve solo los pedidos cuyo responsable coincide (para vista de responsable)."""
    with Session(engine) as session:
        return (
            session.query(Pedido)
            .filter(Pedido.eliminado == 0, Pedido.responsable == nombre_responsable)
            .order_by(Pedido.id.desc())
            .all()
        )


def buscar_por_id(id_pedido: str) -> Pedido | None:
    with Session(engine) as session:
        return (
            session.query(Pedido)
            .filter_by(id_pedido=id_pedido, eliminado=0)
            .first()
        )


def buscar_por_codigo(codigo_acceso: str) -> Pedido | None:
    """Busca un pedido usando el código de acceso entregado al cliente."""
    with Session(engine) as session:
        return (
            session.query(Pedido)
            .filter_by(codigo_acceso=codigo_acceso.strip().upper(), eliminado=0)
            .first()
        )


def obtener_historial(id_pedido: str) -> list[dict]:
    """Devuelve el historial de cambios de un pedido ordenado del más reciente al más antiguo."""
    with Session(engine) as session:
        pedido = session.query(Pedido).filter_by(id_pedido=id_pedido).first()
        if not pedido:
            return []
        registros = (
            session.query(HistorialCambio)
            .filter_by(pedido_id=pedido.id)
            .order_by(HistorialCambio.fecha.desc())
            .all()
        )
        return [
            {
                "campo":         r.campo,
                "valor_antes":   r.valor_antes,
                "valor_despues": r.valor_despues,
                "usuario":       r.usuario,
                "fecha":         r.fecha,
            }
            for r in registros
        ]


# ─────────────────────────────────────────────
# ESCRITURA
# ─────────────────────────────────────────────

def registrar(datos: dict) -> tuple[str, str]:
    """
    Registra un pedido con ID y código de acceso generados automáticamente.
    Devuelve (id_pedido, codigo_acceso).
    """
    with Session(engine) as session:
        id_pedido     = _generar_id()
        codigo_acceso = _generar_codigo_acceso()
        datos["id_pedido"]     = id_pedido
        datos["codigo_acceso"] = codigo_acceso
        datos["eliminado"]     = 0
        nuevo = Pedido(**datos)
        session.add(nuevo)
        session.commit()
        return id_pedido, codigo_acceso


def actualizar_estado(
    id_pedido: str,
    nuevo_estado: str,
    usuario_nombre: str,
    rol_usuario: str = "responsable",
    nombre_responsable: str = "",
) -> tuple[bool, str]:
    """
    Actualiza el estado de un pedido.
    - Un responsable solo puede modificar sus propios pedidos.
    - Un admin puede modificar cualquier pedido.
    Devuelve (True, '') o (False, mensaje_error).
    """
    with Session(engine) as session:
        pedido = session.query(Pedido).filter_by(id_pedido=id_pedido, eliminado=0).first()
        if not pedido:
            return False, "Pedido no encontrado."

        # Control de acceso: responsable solo edita sus propios pedidos
        if rol_usuario == "responsable" and pedido.responsable != nombre_responsable:
            return False, "No tienes permiso para modificar este pedido."

        _registrar_cambio(session, pedido, "estado", pedido.estado, nuevo_estado, usuario_nombre)
        pedido.estado = nuevo_estado
        pedido.fecha  = datetime.now()
        session.commit()
        return True, ""


def editar_pedido(
    id_pedido: str,
    datos: dict,
    usuario_nombre: str,
    rol_usuario: str = "responsable",
    nombre_responsable: str = "",
) -> tuple[bool, str]:
    """
    Edita campos de un pedido: producto, cantidad, notas, responsable, estado.
    - Un responsable solo puede editar sus propios pedidos.
    - Un admin puede editar cualquier pedido, incluido el campo responsable.
    Devuelve (True, '') o (False, mensaje_error).
    """
    campos_permitidos_responsable = {"producto", "cantidad", "notas", "estado"}
    campos_permitidos_admin       = campos_permitidos_responsable | {"responsable", "cliente"}

    with Session(engine) as session:
        pedido = session.query(Pedido).filter_by(id_pedido=id_pedido, eliminado=0).first()
        if not pedido:
            return False, "Pedido no encontrado."

        # Control de acceso
        if rol_usuario == "responsable":
            if pedido.responsable != nombre_responsable:
                return False, "No tienes permiso para editar este pedido."
            campos_invalidos = set(datos.keys()) - campos_permitidos_responsable
            if campos_invalidos:
                return False, f"No puedes editar los campos: {', '.join(campos_invalidos)}."
        else:
            campos_invalidos = set(datos.keys()) - campos_permitidos_admin
            if campos_invalidos:
                return False, f"Campo(s) no válido(s): {', '.join(campos_invalidos)}."

        # Aplicar cambios registrando historial por cada campo modificado
        for campo, valor_nuevo in datos.items():
            valor_actual = getattr(pedido, campo, None)
            _registrar_cambio(session, pedido, campo, valor_actual, valor_nuevo, usuario_nombre)
            setattr(pedido, campo, valor_nuevo)

        pedido.fecha = datetime.now()
        session.commit()
        return True, ""


def eliminar_pedido(
    id_pedido: str,
    usuario_nombre: str,
    rol_usuario: str = "responsable",
    nombre_responsable: str = "",
    fisico: bool = False,
) -> tuple[bool, str]:
    """
    Elimina un pedido.
    - Por defecto realiza un soft delete (marca eliminado=1).
    - Con fisico=True elimina la fila de la BD (solo admin).
    - Un responsable solo puede eliminar sus propios pedidos.
    Devuelve (True, '') o (False, mensaje_error).
    """
    with Session(engine) as session:
        pedido = session.query(Pedido).filter_by(id_pedido=id_pedido).first()
        if not pedido or pedido.eliminado:
            return False, "Pedido no encontrado."

        # Control de acceso
        if rol_usuario == "responsable" and pedido.responsable != nombre_responsable:
            return False, "No tienes permiso para eliminar este pedido."

        if fisico and rol_usuario != "admin":
            return False, "Solo un administrador puede eliminar pedidos permanentemente."

        if fisico:
            session.delete(pedido)
        else:
            _registrar_cambio(session, pedido, "eliminado", "0", "1", usuario_nombre)
            pedido.eliminado = 1
            pedido.fecha     = datetime.now()

        session.commit()
        return True, ""


# ─────────────────────────────────────────────
# ESTADÍSTICAS (usando COUNT en SQL)
# ─────────────────────────────────────────────

def conteo_por_estado() -> dict:
    """Calcula el conteo usando COUNT en la base de datos, sin cargar todos los registros."""
    with Session(engine) as session:
        resultados = (
            session.query(Pedido.estado, func.count(Pedido.id))
            .filter(Pedido.eliminado == 0)
            .group_by(Pedido.estado)
            .all()
        )
        conteo = {"Pendiente": 0, "En Proceso": 0, "Entregado": 0}
        for estado, cantidad in resultados:
            if estado in conteo:
                conteo[estado] = cantidad
        return conteo
