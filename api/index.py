from flask import Flask, request, render_template, send_file
import os
from fitparse import FitFile
import fitencode
from io import BytesIO
import tempfile
import shutil
import logging

app = Flask(__name__, template_folder="../templates")

# Configurar logging para depuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directorio para almacenar archivos temporales
UPLOAD_FOLDER = "/tmp"
ALLOWED_EXTENSIONS = {'fit'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def modify_fit_sport(input_file, new_sport):
    # Lista de deportes válidos según la especificación FIT
    valid_sports = {'running', 'cycling', 'swimming', 'generic', 'hiking', 'walking', 'trail_running'}
    
    if new_sport not in valid_sports:
        logger.error(f"Deporte no válido: {new_sport}")
        raise ValueError(f"Deporte '{new_sport}' no es válido. Debe ser uno de {valid_sports}")

    # Reiniciar el puntero del archivo
    input_file.seek(0)
    
    # Verificar si el archivo FIT es válido con fitparse
    try:
        fitfile = FitFile(input_file)
        file_id_found = False
        sport_found = False
        file_id_fields = {}
        
        # Leer mensajes para verificar file_id y sport
        for record in fitfile.get_messages('file_id'):
            file_id_found = True
            file_id_fields = {field.name: field.value for field in record if field.value is not None}
            if 'sport' in file_id_fields:
                sport_found = True
            break
        
        # Reiniciar el puntero para fitencode
        input_file.seek(0)
        
        # Crear un nuevo archivo FIT con fitencode
        fit_file = fitencode.FitFile()
        
        # Si no hay file_id, crear uno nuevo
        if not file_id_found:
            logger.info("No se encontró mensaje file_id, creando uno nuevo")
            fit_file.add_message('file_id', type='activity', sport=new_sport, time_created=fitencode.types.field_types.DateTime.now())
        else:
            # Modificar o añadir el campo sport
            file_id_fields['sport'] = new_sport
            fit_file.add_message('file_id', **file_id_fields)
        
        # Copiar otros mensajes del archivo original
        for record in fitfile.get_messages():
            if record.name != 'file_id':
                fields = {field.name: field.value for field in record if field.value is not None}
                try:
                    fit_file.add_message(record.name, **fields)
                except Exception as e:
                    logger.warning(f"No se pudo añadir mensaje {record.name}: {str(e)}")
                    continue
        
        # Generar el archivo FIT en memoria
        output = BytesIO()
        try:
            output.write(fit_file.to_bytes())
            output.seek(0)
            logger.info("Archivo FIT generado exitosamente")
            return output, None
        except Exception as e:
            logger.error(f"Error al generar archivo FIT: {str(e)}")
            raise ValueError(f"No se pudo generar el archivo FIT: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error al procesar el archivo FIT: {str(e)}")
        # Devolver el archivo original como fallback
        input_file.seek(0)
        output = BytesIO()
        shutil.copyfileobj(input_file, output)
        output.seek(0)
        return output, f"Advertencia: No se pudo modificar el campo 'sport' debido a un error: {str(e)}. Se devuelve el archivo original."

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
                response = send_file(
                    modified_file,
                    download_name=f'modified_{file.filename}',
                    as_attachment=True,
                    mimetype='application/octet-stream'
                )
                if warning:
                    return render_template('index.html', warning=warning)
                return response
            except Exception as e:
                logger.error(f"Error en la ruta /: {str(e)}")
                return render_template('index.html', error=f'Error al procesar el archivo: {str(e)}')
        else:
            return render_template('index.html', error='Archivo no válido. Por favor, sube un archivo .fit')
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
