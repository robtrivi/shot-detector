# Sentinel Model

Este repositorio contiene el modelo de detección de disparos desarrollado para la materia de Inteligencia Artificial. Además del modelo, se incluye la configuración completa para levantar un servidor local que permita interactuar con la aplicación.

---

## Requisitos Previos

- **Python 3.12.7** instalado en tu sistema.
- **MySQL** configurado y corriendo.
- Acceso a Internet para instalar dependencias.

---

## Instalación y Configuración del Entorno

### 1. Clona el Repositorio

```bash
git clone https://github.com/robtrivi/shot-detector
cd shot-detector
```

### 2. Crea y Activa un Entorno Virtual

Es recomendable usar un entorno virtual para aislar las dependencias del proyecto.

```bash
# Crear el entorno virtual con Python 3.12.7
python3.12 -m venv venv

# Activar el entorno virtual
# En Linux / macOS:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

Verifica que estés usando la versión correcta de Python:

```bash
python --version
# Debería mostrar Python 3.12.7
```

### 3. Instala las Dependencias del Proyecto

Con el entorno virtual activado, instala todos los paquetes necesarios:

```bash
pip install -r requirements.txt
```

### 4. Configura las Variables de Entorno

Crea un archivo llamado `.env` en la ruta `shot_detector` el siguiente contenido:

```env
DJANGO_KEY='django-insecure-611wch&ywj&m3b^!%+*7!+(^$d#kgk30$g_b%uvk9g(bzoi4^i'

DB_USER='username_de_mysql'
DB_PASSWORD='clave_de_username'
DB_HOST='localhost'
DB_PORT='5432'
```
### 5. Realiza las Migraciones de la Base de Datos

Ejecuta las migraciones para configurar la base de datos:

```bash
python manage.py migrate
```

Sigue las indicaciones para configurar el superusuario.

---

## Ejecución del Servidor Local

Con todas las configuraciones listas, levanta el servidor de desarrollo con:

```bash
python manage.py runserver
```

Por defecto, el servidor se inicia en `http://127.0.0.1:8000/`. Abre esta URL en tu navegador para ver el proyecto en funcionamiento.

---

## Notas Adicionales

- **Base de Datos MySQL**: Verifica que tu servidor MySQL esté corriendo y que las credenciales en el archivo `.env` coincidan con las de tu base de datos. Si tu configuración es diferente (por ejemplo, un puerto distinto), actualiza las variables en el archivo `.env` y en el archivo de configuración de Django.
- **Cambios en el Archivo .env**: Si necesitas modificar alguna variable de entorno, edita el archivo `.env` y reinicia el servidor para que los cambios tomen efecto.
- **Desactivación del Entorno Virtual**: Cuando termines de trabajar, puedes salir del entorno virtual con:
  
  ```bash
  deactivate
  ```

---

Con estos pasos, deberías poder levantar el servidor localmente y comenzar a revisar el proyecto.