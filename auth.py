# auth.py
import hashlib
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import engine, Usuario

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE SEGURIDAD
# ─────────────────────────────────────────────

MAX_INTENTOS   = 5          # intentos fallidos antes de bloquear
BLOQUEO_MINUTOS = 15        # minutos de bloqueo tras exceder intentos


# ─────────────────────────────────────────────
# UTILIDADES DE HASH (PBKDF2 + salt)
# ─────────────────────────────────────────────

def _hash_password(password: str, salt: bytes = None) -> str:
    """
    Genera hash seguro: PBKDF2-HMAC-SHA256 con salt de 16 bytes.
    Formato: '<salt_hex>:<key_hex>'
    """
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return salt.hex() + ":" + key.hex()


def _verificar_hash(password: str, stored: str) -> bool:
    """
    Compara una contraseña en texto plano contra el hash almacenado.
    Soporta el formato nuevo (salt:key) y el antiguo SHA-256 puro
    para no romper cuentas existentes.
    """
    if ":" in stored:
        # Formato nuevo: pbkdf2 con salt
        try:
            salt_hex, key_hex = stored.split(":", 1)
            salt = bytes.fromhex(salt_hex)
            key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
            return key.hex() == key_hex
        except Exception:
            return False
    else:
        # Formato legacy: SHA-256 sin salt (migración transparente)
        return stored == hashlib.sha256(password.encode()).hexdigest()


# ─────────────────────────────────────────────
# AUTENTICACIÓN CON LÍMITE DE INTENTOS
# ─────────────────────────────────────────────

def verificar_credenciales(username: str, password: str) -> tuple[dict | None, str]:
    """
    Valida usuario y contraseña con protección contra fuerza bruta.
    Devuelve (dict_usuario, '') si es exitoso.
    Devuelve (None, mensaje_error) si falla.
    """
    if not username or not password:
        return None, "Usuario y contraseña son obligatorios."

    with Session(engine) as session:
        user = session.query(Usuario).filter_by(username=username.strip()).first()

        if not user:
            return None, "Usuario o contraseña incorrectos."

        if not user.activo:
            return None, "Tu cuenta está deshabilitada. Contacta al administrador."

        # Verificar bloqueo temporal
        if user.bloqueado_hasta and datetime.now() < user.bloqueado_hasta:
            minutos_restantes = int((user.bloqueado_hasta - datetime.now()).seconds / 60) + 1
            return None, f"Cuenta bloqueada temporalmente. Intenta en {minutos_restantes} minuto(s)."

        # Verificar contraseña
        if _verificar_hash(password, user.password_hash):
            # Éxito: resetear contadores y migrar hash si es legacy
            user.intentos_fallidos = 0
            user.bloqueado_hasta   = None

            # Migración automática de hash legacy → pbkdf2
            if ":" not in user.password_hash:
                user.password_hash = _hash_password(password)

            session.commit()
            return {
                "id":       user.id,
                "username": user.username,
                "nombre":   user.nombre,
                "rol":      user.rol,
            }, ""
        else:
            # Fallo: incrementar contador
            user.intentos_fallidos = (user.intentos_fallidos or 0) + 1

            if user.intentos_fallidos >= MAX_INTENTOS:
                user.bloqueado_hasta   = datetime.now() + timedelta(minutes=BLOQUEO_MINUTOS)
                user.intentos_fallidos = 0
                session.commit()
                return None, (
                    f"Demasiados intentos fallidos. "
                    f"Cuenta bloqueada por {BLOQUEO_MINUTOS} minutos."
                )

            restantes = MAX_INTENTOS - user.intentos_fallidos
            session.commit()
            return None, f"Contraseña incorrecta. Te quedan {restantes} intento(s)."


# ─────────────────────────────────────────────
# GESTIÓN DE USUARIOS (solo admin)
# ─────────────────────────────────────────────

def crear_usuario(
    username: str, password: str, nombre: str, rol: str = "responsable"
) -> tuple[bool, str]:
    """Crea un nuevo usuario con hash seguro."""
    if not username or not password or not nombre:
        return False, "Todos los campos son obligatorios."
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    if rol not in ("admin", "responsable"):
        return False, "Rol inválido."

    with Session(engine) as session:
        if session.query(Usuario).filter_by(username=username.strip()).first():
            return False, f"El nombre de usuario '{username}' ya existe."
        user = Usuario(
            username=username.strip(),
            password_hash=_hash_password(password),
            nombre=nombre.strip(),
            rol=rol,
            activo=1,
        )
        session.add(user)
        session.commit()
        return True, ""


def listar_usuarios() -> list[dict]:
    with Session(engine) as session:
        usuarios = session.query(Usuario).order_by(Usuario.id).all()
        return [
            {
                "id":       u.id,
                "username": u.username,
                "nombre":   u.nombre,
                "rol":      u.rol,
                "activo":   u.activo,
            }
            for u in usuarios
        ]


def toggle_activo(user_id: int, current_admin_id: int) -> tuple[bool, str]:
    """Activa o desactiva un usuario. No permite deshabilitar al propio admin."""
    if user_id == current_admin_id:
        return False, "No puedes deshabilitar tu propia cuenta."
    with Session(engine) as session:
        user = session.query(Usuario).filter_by(id=user_id).first()
        if not user:
            return False, "Usuario no encontrado."
        user.activo = 0 if user.activo else 1
        session.commit()
        estado = "activado" if user.activo else "deshabilitado"
        return True, f"Usuario '{user.username}' {estado}."


def cambiar_password(user_id: int, nueva_password: str) -> tuple[bool, str]:
    if len(nueva_password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."
    with Session(engine) as session:
        user = session.query(Usuario).filter_by(id=user_id).first()
        if not user:
            return False, "Usuario no encontrado."
        user.password_hash     = _hash_password(nueva_password)
        user.intentos_fallidos = 0        # resetear bloqueos al cambiar contraseña
        user.bloqueado_hasta   = None
        session.commit()
        return True, f"Contraseña de '{user.username}' actualizada."