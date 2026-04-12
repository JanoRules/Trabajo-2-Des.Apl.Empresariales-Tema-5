import streamlit as st
from datetime import datetime
import crud

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────

st.set_page_config(page_title="Seguimiento de Pedidos", page_icon="📦", layout="wide")
st.title("📦 Sistema de Seguimiento de Pedidos")
st.caption("Base de datos: SQLite  |  ORM: SQLAlchemy")

ESTADOS = ["Pendiente", "En Proceso", "Entregado"]
ICONOS  = {"Pendiente": "🟡", "En Proceso": "🔵", "Entregado": "🟢"}

tab1, tab2, tab3 = st.tabs(["➕ Registrar Pedido", "🔎 Consultar Estado", "📋 Todos los Pedidos"])

# ─────────────────────────────────────────────
# TAB 1: REGISTRAR
# ─────────────────────────────────────────────

with tab1:
    st.header("Registrar Nuevo Pedido")
    st.info("El ID del pedido se asignará automáticamente al guardar.", icon="🤖")

    col1, col2 = st.columns(2)
    with col1:
        cliente     = st.text_input("Nombre del Cliente", placeholder="Ej: Juan Pérez")
        producto    = st.text_input("Producto / Descripción", placeholder='Ej: Laptop Dell 15"')
        cantidad    = st.number_input("Cantidad", min_value=1, value=1)
    with col2:
        responsable = st.text_input("Responsable", placeholder="Ej: María González")
        estado_ini  = st.selectbox("Estado Inicial", ESTADOS)
        notas       = st.text_area("Notas adicionales", placeholder="Opcional...")

    if st.button("✅ Registrar Pedido", type="primary"):
        if cliente and producto and responsable:
            id_asignado = crud.registrar({
                "cliente":     cliente.strip(),
                "producto":    producto.strip(),
                "cantidad":    cantidad,
                "responsable": responsable.strip(),
                "estado":      estado_ini,
                "notas":       notas.strip(),
                "fecha":       datetime.now(),
            })
            st.success(f"✅ Pedido registrado exitosamente con el ID **{id_asignado}**.")
        else:
            st.error("⚠️ Complete los campos obligatorios: Cliente, Producto y Responsable.")

# ─────────────────────────────────────────────
# TAB 2: CONSULTAR Y ACTUALIZAR
# ─────────────────────────────────────────────

with tab2:
    st.header("Consultar y Actualizar Estado")

    id_buscar = st.text_input("Ingrese el ID del Pedido a consultar", placeholder="Ej: PED-001")

    if st.button("🔍 Buscar", type="primary"):
        if id_buscar.strip():
            pedido = crud.buscar_por_id(id_buscar.strip())
            if pedido:
                st.session_state["pedido_encontrado"] = id_buscar.strip()
            else:
                st.error("❌ No se encontró ningún pedido con ese ID.")
                st.session_state["pedido_encontrado"] = None
        else:
            st.warning("Ingrese un ID para buscar.")

    if st.session_state.get("pedido_encontrado"):
        pedido = crud.buscar_por_id(st.session_state["pedido_encontrado"])
        if pedido:
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

            st.markdown("---")
            st.subheader("Actualizar Estado")

            nuevo_estado = st.selectbox(
                "Nuevo estado", ESTADOS,
                index=ESTADOS.index(pedido.estado)
            )

            if st.button("💾 Guardar Cambio de Estado"):
                crud.actualizar_estado(pedido.id_pedido, nuevo_estado)
                st.success(f"✅ Estado actualizado a **{nuevo_estado}** en la base de datos.")
                st.rerun()

# ─────────────────────────────────────────────
# TAB 3: LISTADO COMPLETO
# ─────────────────────────────────────────────

with tab3:
    st.header("Listado Completo de Pedidos")

    todos = crud.obtener_todos()

    if todos:
        filtro  = st.selectbox("Filtrar por estado", ["Todos"] + ESTADOS)
        mostrar = todos if filtro == "Todos" else [p for p in todos if p.estado == filtro]

        st.write(f"**Total: {len(mostrar)} pedido(s)**")

        filas = [
            {
                "ID Pedido":   p.id_pedido,
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
        col1, col2, col3 = st.columns(3)
        col1.metric("🟡 Pendientes", conteo["Pendiente"])
        col2.metric("🔵 En Proceso", conteo["En Proceso"])
        col3.metric("🟢 Entregados", conteo["Entregado"])
    else:
        st.info("No hay pedidos registrados aún. Ve a la pestaña ➕ para agregar uno.")
