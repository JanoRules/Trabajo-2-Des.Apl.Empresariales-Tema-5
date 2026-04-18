# 📦 Sistema de Seguimiento de Pedidos

Una aplicación web robusta y segura diseñada para la gestión del ciclo de vida de pedidos. Este sistema separa la lógica de negocio, la seguridad y la interfaz de usuario, ofreciendo una solución profesional para el monitoreo de órdenes en tiempo real.

## 🚀 Características Principales

### 🔐 Seguridad y Control de Acceso
- **Autenticación Robusta:** Hashing de contraseñas mediante **PBKDF2-HMAC-SHA256** con salt aleatorio y 260,000 iteraciones.
- **Protección contra Fuerza Bruta:** Bloqueo automático de cuentas por 15 minutos tras 5 intentos fallidos, con persistencia en base de datos.
- **Roles Diferenciados:** - **Admin:** Gestión total de pedidos y administración de usuarios.
  - **Responsable:** Creación y gestión de pedidos propios.
  - **Cliente:** Acceso público de solo lectura mediante código único.

### 📋 Gestión de Pedidos
- **IDs Correlativos:** Generación automática de identificadores (ej: `PED-001`).
- **Códigos de Acceso:** Generación de códigos únicos criptográficamente seguros para seguimiento externo.
- **Historial de Auditoría:** Registro automático de quién modificó cada pedido y qué cambios se realizaron.
- **Soft Delete:** Sistema de borrado lógico para prevenir pérdida accidental de datos.

## 🏗️ Arquitectura del Proyecto (Diseño Propio)
El proyecto ha sido estructurado siguiendo el principio de **separación de responsabilidades** para facilitar el mantenimiento:

* **`app.py`**: Interfaz de usuario reactiva construida con Streamlit.
* **`auth.py`**: Motor de seguridad, gestión de sesiones y encriptación.
* **`crud.py`**: Capa de servicios para operaciones lógicas sobre los datos.
* **`models.py`**: Definición de esquemas y modelos mediante SQLAlchemy ORM.

## 🛠️ Tecnologías Utilizadas
- **Lenguaje:** Python 3.8+
- **Frontend:** [Streamlit](https://streamlit.io/)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/)
- **Base de Datos:** SQLite (Configurada para escalabilidad vía ORM)

## 📋 Requisitos e Instalación

1. **Instalar dependencias:**
   ```bash
   pip install streamlit sqlalchemy
   
# PARA EJECUTAR EL PROGRAMA:
python -m streamlit run app.py
