# 📦 Sistema de Seguimiento de Pedidos

Una aplicación web robusta y ligera construida con **Streamlit** para la gestión y monitoreo de pedidos en tiempo real, utilizando **SQLAlchemy** como ORM y **SQLite** como motor de base de datos.

## 🚀 Características
- **Registro Automatizado:** Generación de IDs correlativos (ej. `PED-001`).
- **Gestión de Estados:** Seguimiento dinámico (Pendiente, En Proceso, Entregado) con indicadores visuales (emojis).
- **Consulta Rápida:** Buscador por ID para actualizaciones inmediatas.
- **Panel de Control:** Visualización de métricas generales y filtrado de pedidos.

## 🛠️ Tecnologías Utilizadas
- **Frontend:** [Streamlit](https://streamlit.io/)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/)
- **Base de Datos:** SQLite (Local)

## 📋 Requisitos Previos
Asegúrate de tener instalado Python 3.8 o superior.

## 🔧 Instalación y Configuración

1. **Clonar el repositorio o descargar los archivos:**
   Asegúrate de tener `app.py`, `crud.py` y `models.py` en la misma carpeta.

2. **Crear un entorno virtual (Recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   
# PARA EJECUTAR EL PROGRAMA:
python -m streamlit run app.py