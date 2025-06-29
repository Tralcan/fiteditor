# FIT Sport Editor

Una aplicación web simple para modificar el campo `sport` en archivos FIT (usados por dispositivos de fitness como Garmin). Construida con Flask y `fitparse`, desplegada en Vercel.

## Características
- Subir un archivo FIT.
- Seleccionar un nuevo valor para el campo `sport`.
- Descargar el archivo FIT modificado.
- Interfaz web amigable con Tailwind CSS.

## Requisitos
- Python 3.8+
- Dependencias listadas en `requirements.txt`
- Cuenta en Vercel y GitHub

## Estructura del Proyecto
```
fit-sport-editor/
├── api/
│   └── index.py
├── templates/
│   └── index.html
├── requirements.txt
├── vercel.json
└── README.md
```

## Instalación Local
1. Clona el repositorio:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd fit-sport-editor
   ```

2. Crea un entorno virtual e instala las dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación:
   ```bash
   python api/index.py
   ```

4. Abre tu navegador y visita `http://127.0.0.1:5000`.

## Despliegue en Vercel
1. **Crea un repositorio en GitHub**:
   - Sube todos los archivos al repositorio.
   - Asegúrate de que la estructura incluya `api/index.py`, `templates/index.html`, `requirements.txt` y `vercel.json`.

2. **Configura Vercel**:
   - Ve a [Vercel](https://vercel.com) y crea una cuenta si no la tienes.
   - En el panel de Vercel, selecciona "Add New > Project".
   - Conecta tu cuenta de GitHub y selecciona el repositorio `fit-sport-editor`.
   - En la configuración del proyecto:
     - **Framework Preset**: Selecciona "Other".
     - **Build Command**: Deja en blanco (Vercel usará `requirements.txt`).
     - **Output Directory**: Deja en blanco.
     - **Node.js Version**: Asegúrate de que esté configurado en 18.x (en Settings > General si es necesario).[](https://www.genelify.com/blog/deploy-a-python-flask-app-to-vercel)
   - Haz clic en "Deploy".

3. **Verifica el Despliegue**:
   - Una vez completado, Vercel te proporcionará una URL (por ejemplo, `https://fit-sport-editor.vercel.app`).
   - Visita la URL para usar la aplicación.

## Notas
- Los archivos subidos se procesan en `/tmp`, que es compatible con el plan gratuito de Vercel.
- Los valores para el campo `スポーツ` son predefinidos, pero puedes modificar la lista en `templates/index.html`.
- Si encuentras errores como "Unable to find any supported Python versions", verifica que la versión de Node.js sea 18.x en la configuración del proyecto.[](https://www.genelify.com/blog/deploy-a-python-flask-app-to-vercel)
- Para actualizaciones, simplemente haz `git push` al repositorio, y Vercel redeployará automáticamente.

## Licencia
MIT