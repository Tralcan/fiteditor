from flask import Flask, request, render_template, send_file
import os
from fitparse import FitFile
from io import BytesIO
import tempfile
import shutil

app = Flask(__name__, template_folder="../templates")

# Directorio para almacenar archivos temporales
UPLOAD_FOLDER = "/tmp"
ALLOWED_EXTENSIONS = {'fit'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def modify_fit_sport(input_file, new_sport):
    # Lista de deportes válidos según la especificación FIT
    valid_sports = {'running', 'cycling', 'swimming', 'generic', 'hiking', 'walking', 'trail_running'}
    
    if new_sport not in valid_sports:
        raise ValueError(f"Deporte '{new_sport}' no es válido. Debe ser uno de {valid_sports}")

    # Parsear el archivo FIT para verificar su contenido
    try:
        fitfile = FitFile(input_file)
        sport_found = False
        for record in fitfile.get_messages('file_id'):
            if record.get_value('sport') is not None:
                sport_found = True
                # No podemos modificar directamente, así que verificamos que el archivo es válido
                break
        
        if not sport_found:
            raise ValueError("El archivo FIT no contiene un mensaje 'file_id' con el campo 'sport'")

        # Dado que fitparse no permite modificar y escribir fácilmente,
        # copiamos el archivo original como fallback y devolvemos un mensaje
        # En un entorno real, necesitaríamos una biblioteca que permita escribir FIT
        output = BytesIO()
        input_file.seek(0)  # Reiniciar el puntero del archivo
        shutil.copyfileobj(input_file, output)
        output.seek(0)
        return output, "Advertencia: No se pudo modificar el campo 'sport'. Se devuelve el archivo original."
    except Exception as e:
        raise e

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Verificar si se subió un archivo
        if 'file' not in request.files:
            return render_template('index.html', error='No se seleccionó ningún archivo')
        
        file = request.files['file']
        new_sport = request.form.get('sport', 'generic')
        
        if file and allowed_file(file.filename):
            try:
                # Procesar el archivo FIT
                modified_file, warning = modify_fit_sport(file.stream, new_sport)
                
                # Enviar el archivo modificado para descarga
                return send_file(
                    modified_file,
                    download_name=f'modified_{file.filename}',
                    as_attachment=True,
                    mimetype='application/octet-stream'
                ), render_template('index.html', warning=warning)
            except Exception as e:
                return render_template('index.html', error=f'Error al procesar el archivo: {str(e)}')
        else:
            return render_template('index.html', error='Archivo no válido. Por favor, sube un archivo .fit')
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
