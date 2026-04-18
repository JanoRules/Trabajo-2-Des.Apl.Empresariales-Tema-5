# app.py
import streamlit as st
from datetime import datetime
import crud
import auth

# ─────────────────────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────────

st.set_page_config(page_title="Seguimiento de Pedidos", page_icon="📦", layout="wide")

ESTADOS = ["Pendiente", "En Proceso", "Entregado"]
ICONOS  = {"Pendiente": "🟡", "En Proceso": "🔵", "Entregado": "🟢"}


# ─────────────────────────────────────────────
# HELPERS DE VISUALIZACIÓN
# ─────────────────────────────────────────────

def _mostrar_pedido_cliente(pedido) -> None:
    """Tarjeta de lectura para el cliente (sin opciones de edición)."""
    icono = ICONOS.get(pedido.estado, "⚪")
    st.markdown("---")

    # Barra de progreso visual
    paso = ESTADOS.index(pedido.estado) if pedido.estado in ESTADOS else 0
    cols_prog = st.columns(3)
    for i, (estado, col) in enumerate(zip(ESTADOS, cols_prog)):
        ico = ICONOS[estado]
        with col:
            if i < paso:
                st.success(f"{ico} {estado} ✔")
            elif i == paso:
                st.info(f"{ico} **{estado}** ← actual")
            else:
                st.markdown(
                    f"<div style='color:gray'>{ico} {estado}</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**ID Pedido:** {pedido.id_pedido}")
        st.write(f"**Producto:** {pedido.producto} (x{pedido.cantidad})")
    with col2:
        st.write(f"**Estado actual:** {icono} {pedido.estado}")
        st.write(f"**Última actualización:** {pedido.fecha.strftime('%Y-%m-%d %H:%M')}")
    if pedido.notas:
        st.info(f"📝 **Nota:** {pedido.notas}")


def _mostrar_historial(id_pedido: str) -> None:
    """Muestra el historial de cambios de un pedido en una tabla expandible."""
    historial = crud.obtener_historial(id_pedido)
    if not historial:
        st.caption("Sin cambios registrados aún.")
        return
    with st.expander(f"📜 Historial de cambios ({len(historial)} registro(s))", expanded=False):
        filas = [
            {
                "Fecha":         h["fecha"].strftime("%Y-%m-%d %H:%M:%S"),
                "Campo":         h["campo"],
                "Valor anterior": h["valor_antes"],
                "Valor nuevo":   h["valor_despues"],
                "Modificado por": h["usuario"],
            }
            for h in historial
        ]
        st.dataframe(filas, use_container_width=True)


# ─────────────────────────────────────────────
# TABS REUTILIZABLES
# ─────────────────────────────────────────────

def _tab_seguimiento_cliente() -> None:
    """Tab público de consulta para clientes mediante código de acceso."""
    st.header("📦 Seguimiento de Mi Pedido")
    st.markdown(
        "Introduce el **código de acceso** que recibiste al realizar tu pedido "
        "para consultar su estado en tiempo real."
    )

    codigo = st.text_input(
        "Código de acceso",
        placeholder="Ej: A3BK-9ZT2",
        key="pub_codigo",
    ).strip().upper()

    if st.button("🔍 Consultar Estado", type="primary", key="pub_btn"):
        if not codigo:
            st.warning("⚠️ Ingresa tu código de acceso.")
        else:
            pedido = crud.buscar_por_codigo(codigo)
            if pedido:
                st.success(f"✅ Pedido encontrado para **{pedido.cliente}**")
                _mostrar_pedido_cliente(pedido)
            else:
                st.error("❌ Código no encontrado. Verifica que esté escrito correctamente.")

    st.markdown("---")
    st.caption("¿No tienes tu código? Contáctate con quien gestionó tu pedido.")


def _registrar_pedido_form(usuario: dict, key_prefix: str) -> None:
    """Formulario reutilizable para registrar pedidos (admin y responsable)."""
    st.header("Registrar Nuevo Pedido")
    st.info("El ID y el código de acceso del cliente se generan automáticamente.", icon="🤖")

    col1, col2 = st.columns(2)
    with col1:
        cliente  = st.text_input("Nombre del Cliente",      placeholder="Ej: Juan Pérez",        key=f"{key_prefix}_cli")
        producto = st.text_input("Producto / Descripción",  placeholder='Ej: Laptop Dell 15"',   key=f"{key_prefix}_prod")
        cantidad = st.number_input("Cantidad", min_value=1, value=1,                              key=f"{key_prefix}_cant")
    with col2:
        responsable = st.text_input(
            "Responsable", value=usuario["nombre"],
            placeholder="Ej: María González",
            key=f"{key_prefix}_resp",
            # Los responsables no pueden cambiar el nombre de responsable
            disabled=(usuario["rol"] == "responsable"),
        )
        estado_ini = st.selectbox("Estado Inicial", ESTADOS,                                     key=f"{key_prefix}_est")
        notas      = st.text_area("Notas adicionales", placeholder="Opcional...",                key=f"{key_prefix}_notas")

    # Forzar responsable al nombre del usuario si rol = responsable
    nombre_responsable = usuario["nombre"] if usuario["rol"] == "responsable" else responsable.strip()

    if st.button("✅ Registrar Pedido", type="primary", key=f"{key_prefix}_btn_reg"):
        if cliente and producto and nombre_responsable:
            id_asignado, codigo_acceso = crud.registrar({
                "cliente":     cliente.strip(),
                "producto":    producto.strip(),
                "cantidad":    cantidad,
                "responsable": nombre_responsable,
                "estado":      estado_ini,
                "notas":       notas.strip(),
                "fecha":       datetime.now(),
            })
            st.success(f"✅ Pedido registrado con el ID **{id_asignado}**.")
            st.markdown("#### 🔑 Código de acceso para el cliente")
            st.markdown(
                f"""
                <div style="
                    background:#f0f4ff;border:2px solid #4a7cf7;
                    border-radius:10px;padding:18px 24px;text-align:center;">
                    <p style="margin:0;font-size:14px;color:#555;">
                        Comparte este código con <strong>{cliente.strip()}</strong>
                        para que pueda rastrear su pedido:
                    </p>
                    <p style="margin:10px 0 0;font-size:36px;font-weight:bold;
                              letter-spacing:6px;color:#1a1a2e;">
                        {codigo_acceso}
                    </p>
                    <p style="margin:6px 0 0;font-size:12px;color:#888;">
                        El cliente puede ingresar este código en la pestaña
                        <em>📦 Seguimiento de Mi Pedido</em>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.error("⚠️ Complete los campos obligatorios: Cliente, Producto y Responsable.")


def _tab_consultar_actualizar(usuario: dict, key_prefix: str) -> None:
    """Tab de consulta, edición completa, cambio de estado y eliminación de pedidos."""
    st.header("Consultar / Actualizar Pedido")
    id_key    = f"{key_prefix}_buscar"
    found_key = f"{key_prefix}_pedido_encontrado"

    id_buscar = st.text_input("ID del Pedido", placeholder="Ej: PED-001", key=id_key)

    if st.button("🔍 Buscar", type="primary", key=f"{key_prefix}_btn_bus"):
        if id_buscar.strip():
            pedido = crud.buscar_por_id(id_buscar.strip().upper())
            if pedido:
                st.session_state[found_key] = id_buscar.strip().upper()
            else:
                st.error("❌ No se encontró ningún pedido con ese ID.")
                st.session_state[found_key] = None
        else:
            st.warning("Ingrese un ID para buscar.")

    if st.session_state.get(found_key):
        pedido = crud.buscar_por_id(st.session_state[found_key])
        if not pedido:
            st.session_state[found_key] = None
            st.rerun()
            return

        # Verificar permiso de responsable
        es_admin = usuario["rol"] == "admin"
        es_propio = pedido.responsable == usuario["nombre"]
        puede_editar = es_admin or es_propio

        st.markdown("---")
        icono = ICONOS.get(pedido.estado, "⚪")
        col_a, col_b = st.columns(2)
        with col_a:
            st.write(f"**ID Pedido:** {pedido.id_pedido}")
            st.write(f"**Cliente:** {pedido.cliente}")
            st.write(f"**Producto:** {pedido.producto} (x{pedido.cantidad})")
        with col_b:
            st.write(f"**Responsable:** {pedido.responsable}")
            st.write(f"**Fecha registro:** {pedido.fecha.strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"**Estado actual:** {icono} {pedido.estado}")
        if pedido.notas:
            st.write(f"**Notas:** {pedido.notas}")
        if pedido.codigo_acceso:
            st.info(f"🔑 **Código de acceso del cliente:** `{pedido.codigo_acceso}`")

        # ── Historial de cambios ──
        _mostrar_historial(pedido.id_pedido)

        if not puede_editar:
            st.warning("⚠️ Solo puedes editar pedidos asignados a ti.")
            return

        st.markdown("---")

        # ── Cambio rápido de estado ──
        st.subheader("Actualizar Estado")
        nuevo_estado = st.selectbox(
            "Nuevo estado", ESTADOS,
            index=ESTADOS.index(pedido.estado),
            key=f"{key_prefix}_new_est",
        )
        if st.button("💾 Guardar Estado", key=f"{key_prefix}_btn_est"):
            ok, msg = crud.actualizar_estado(
                pedido.id_pedido, nuevo_estado,
                usuario_nombre=usuario["nombre"],
                rol_usuario=usuario["rol"],
                nombre_responsable=usuario["nombre"],
            )
            if ok:
                st.success(f"✅ Estado actualizado a **{nuevo_estado}**.")
                st.rerun()
            else:
                st.error(f"⚠️ {msg}")

        st.markdown("---")

        # ── Edición completa ──
        with st.expander("✏️ Editar datos del pedido", expanded=False):
            e_producto  = st.text_input("Producto",  value=pedido.producto,  key=f"{key_prefix}_e_prod")
            e_cantidad  = st.number_input("Cantidad", min_value=1, value=pedido.cantidad, key=f"{key_prefix}_e_cant")
            e_notas     = st.text_area("Notas", value=pedido.notas or "", key=f"{key_prefix}_e_notas")
            if es_admin:
                e_responsable = st.text_input("Responsable", value=pedido.responsable, key=f"{key_prefix}_e_resp")
                e_cliente     = st.text_input("Cliente",     value=pedido.cliente,     key=f"{key_prefix}_e_cli")
            else:
                e_responsable = pedido.responsable
                e_cliente     = pedido.cliente

            if st.button("💾 Guardar Cambios", key=f"{key_prefix}_btn_edit"):
                datos_nuevos = {
                    "producto":  e_producto.strip(),
                    "cantidad":  e_cantidad,
                    "notas":     e_notas.strip(),
                }
                if es_admin:
                    datos_nuevos["responsable"] = e_responsable.strip()
                    datos_nuevos["cliente"]     = e_cliente.strip()

                ok, msg = crud.editar_pedido(
                    pedido.id_pedido, datos_nuevos,
                    usuario_nombre=usuario["nombre"],
                    rol_usuario=usuario["rol"],
                    nombre_responsable=usuario["nombre"],
                )
                if ok:
                    st.success("✅ Pedido actualizado correctamente.")
                    st.rerun()
                else:
                    st.error(f"⚠️ {msg}")

        st.markdown("---")

        # ── Eliminación ──
        with st.expander("🗑️ Eliminar pedido", expanded=False):
            st.warning("Esta acción marca el pedido como eliminado (no se borra permanentemente).")

            confirmar = st.checkbox(
                f"Confirmo que deseo eliminar el pedido **{pedido.id_pedido}**",
                key=f"{key_prefix}_confirm_del",
            )

            col_del1, col_del2 = st.columns(2)
            with col_del1:
                if st.button("🗑️ Eliminar (soft)", disabled=not confirmar, key=f"{key_prefix}_btn_soft"):
                    ok, msg = crud.eliminar_pedido(
                        pedido.id_pedido,
                        usuario_nombre=usuario["nombre"],
                        rol_usuario=usuario["rol"],
                        nombre_responsable=usuario["nombre"],
                        fisico=False,
                    )
                    if ok:
                        st.success("✅ Pedido eliminado correctamente.")
                        st.session_state[found_key] = None
                        st.rerun()
                    else:
                        st.error(f"⚠️ {msg}")

            if es_admin:
                with col_del2:
                    if st.button("⚠️ Eliminar PERMANENTE", disabled=not confirmar, key=f"{key_prefix}_btn_hard"):
                        ok, msg = crud.eliminar_pedido(
                            pedido.id_pedido,
                            usuario_nombre=usuario["nombre"],
                            rol_usuario=usuario["rol"],
                            nombre_responsable=usuario["nombre"],
                            fisico=True,
                        )
                        if ok:
                            st.success("✅ Pedido eliminado permanentemente.")
                            st.session_state[found_key] = None
                            st.rerun()
                        else:
                            st.error(f"⚠️ {msg}")


def _tab_todos_los_pedidos(usuario: dict, key_prefix: str) -> None:
    """Tab con listado completo, filtros y resumen estadístico."""
    st.header("Listado Completo de Pedidos")

    # Los responsables solo ven sus propios pedidos
    if usuario["rol"] == "responsable":
        todos = crud.obtener_por_responsable(usuario["nombre"])
        st.info(f"👤 Mostrando solo los pedidos asignados a **{usuario['nombre']}**.")
    else:
        todos = crud.obtener_todos()

    if todos:
        filtro  = st.selectbox("Filtrar por estado", ["Todos"] + ESTADOS, key=f"{key_prefix}_filtro")
        mostrar = todos if filtro == "Todos" else [p for p in todos if p.estado == filtro]
        st.write(f"**Total: {len(mostrar)} pedido(s)**")
        filas = [
            {
                "ID Pedido":   p.id_pedido,
                "Cód. Acceso": p.codigo_acceso or "—",
                "Cliente":     p.cliente,
                "Producto":    p.producto,
                "Cantidad":    p.cantidad,
                "Responsable": p.responsable,
                "Estado":      f"{ICONOS.get(p.estado, '')} {p.estado}",
                "Fecha":       p.fecha.strftime("%Y-%m-%d %H:%M:%S"),
                "Notas":       p.notas or "—",
            }
            for p in mostrar
        ]
        st.dataframe(filas, use_container_width=True)
        st.markdown("---")
        st.subheader("Resumen")
        conteo = crud.conteo_por_estado()
        c1, c2, c3 = st.columns(3)
        c1.metric("🟡 Pendientes", conteo["Pendiente"])
        c2.metric("🔵 En Proceso", conteo["En Proceso"])
        c3.metric("🟢 Entregados",  conteo["Entregado"])
    else:
        st.info("No hay pedidos registrados aún.")


# ─────────────────────────────────────────────
# SIDEBAR: LOGIN / LOGOUT
# ─────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/box.png", width=64)
    st.title("📦 Pedidos")
    st.divider()

    usuario = st.session_state.get("usuario")

    if usuario:
        rol_label = "Administrador 🛡️" if usuario["rol"] == "admin" else "Responsable 👤"
        st.success(f"**{usuario['nombre']}**")
        st.caption(f"Rol: {rol_label}")
        st.divider()
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    else:
        st.subheader("🔐 Acceso Personal")
        uname = st.text_input("Usuario", key="login_user")
        pwd   = st.text_input("Contraseña", type="password", key="login_pwd")

        if st.button("Ingresar", type="primary", use_container_width=True):
            resultado, mensaje = auth.verificar_credenciales(uname, pwd)
            if resultado:
                st.session_state["usuario"] = resultado
                st.rerun()
            else:
                st.error(mensaje)

        st.divider()
        st.caption("¿Solo consultas? Usa la pestaña **📦 Seguimiento de Mi Pedido**.")


# ─────────────────────────────────────────────
# CUERPO PRINCIPAL
# ─────────────────────────────────────────────

st.title("📦 Sistema de Seguimiento de Pedidos")
st.caption("Base de datos: SQLite  |  ORM: SQLAlchemy  |  Auth: PBKDF2 + salt  |  Control de acceso por rol")

usuario = st.session_state.get("usuario")

# ── VISTA SIN SESIÓN ─────────────────────────────────────────────────────────
if not usuario:
    (tab_pub,) = st.tabs(["📦 Seguimiento de Mi Pedido"])
    with tab_pub:
        _tab_seguimiento_cliente()

# ── VISTA RESPONSABLE ────────────────────────────────────────────────────────
elif usuario["rol"] == "responsable":
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Seguimiento de Mi Pedido",
        "➕ Registrar Pedido",
        "🔎 Consultar / Actualizar",
        "📋 Mis Pedidos",
    ])
    with tab1:
        _tab_seguimiento_cliente()
    with tab2:
        _registrar_pedido_form(usuario, key_prefix="resp")
    with tab3:
        _tab_consultar_actualizar(usuario, key_prefix="resp")
    with tab4:
        _tab_todos_los_pedidos(usuario, key_prefix="resp")

# ── VISTA ADMINISTRADOR ──────────────────────────────────────────────────────
elif usuario["rol"] == "admin":
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📦 Seguimiento de Mi Pedido",
        "➕ Registrar Pedido",
        "🔎 Consultar / Actualizar",
        "📋 Todos los Pedidos",
        "👥 Gestión de Usuarios",
    ])

    with tab1:
        _tab_seguimiento_cliente()

    with tab2:
        _registrar_pedido_form(usuario, key_prefix="adm")

    with tab3:
        _tab_consultar_actualizar(usuario, key_prefix="adm")

    with tab4:
        _tab_todos_los_pedidos(usuario, key_prefix="adm")

    with tab5:
        st.header("👥 Gestión de Usuarios del Sistema")
        st.markdown("Solo los **administradores** tienen acceso a este panel.")

        # ── Listado actual ──
        st.subheader("Usuarios registrados")
        lista = auth.listar_usuarios()
        for u in lista:
            estado_icon = "✅" if u["activo"] else "🚫"
            rol_badge   = "🛡️ Admin" if u["rol"] == "admin" else "👤 Responsable"
            col_u, col_r, col_btn = st.columns([3, 2, 2])
            with col_u:
                st.write(f"{estado_icon} **{u['nombre']}** · `{u['username']}`")
            with col_r:
                st.caption(rol_badge)
            with col_btn:
                label_btn = "Deshabilitar" if u["activo"] else "Activar"
                if st.button(label_btn, key=f"toggle_{u['id']}"):
                    ok, msg = auth.toggle_activo(u["id"], usuario["id"])
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()

        st.markdown("---")

        # ── Crear usuario ──
        st.subheader("Crear Nuevo Usuario")
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            new_username = st.text_input("Nombre de usuario", placeholder="Ej: mgonzalez", key="nu_user")
            new_nombre   = st.text_input("Nombre completo",   placeholder="Ej: María González", key="nu_nombre")
        with col_n2:
            new_password = st.text_input("Contraseña (mín. 6 caracteres)", type="password", key="nu_pwd")
            new_rol      = st.selectbox(
                "Rol", ["responsable", "admin"], key="nu_rol",
                format_func=lambda r: "👤 Responsable" if r == "responsable" else "🛡️ Administrador",
            )

        if st.button("➕ Crear Usuario", type="primary", key="btn_crear_user"):
            ok, msg = auth.crear_usuario(new_username, new_password, new_nombre, new_rol)
            if ok:
                st.success(f"✅ Usuario '{new_username}' creado exitosamente.")
                st.rerun()
            else:
                st.error(f"⚠️ {msg}")

        st.markdown("---")

        # ── Cambiar contraseña ──
        st.subheader("Cambiar Contraseña")
        opciones = {u["username"]: u["id"] for u in lista}
        sel_user  = st.selectbox("Seleccionar usuario", list(opciones.keys()), key="cp_sel")
        nueva_pwd = st.text_input("Nueva contraseña", type="password", key="cp_pwd")

        if st.button("🔑 Actualizar Contraseña", key="btn_cp"):
            ok, msg = auth.cambiar_password(opciones[sel_user], nueva_pwd)
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"⚠️ {msg}")
