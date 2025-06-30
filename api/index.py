from flask import Flask, request, render_template, send_file
import os
from fitparse import FitFile
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.profile_type import Sport, SubSport
import datetime
from io import BytesIO
import shutil
import logging
import inspect

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
    # Mapeo de deportes a valores de Sport y SubSport de fit-tool
    sport_mapping = {
        'running': (Sport.RUNNING, None),
        'cycling': (Sport.CYCLING, None),
        'swimming': (Sport.SWIMMING, None),
        'generic': (Sport.GENERIC, None),
        'hiking': (Sport.HIKING, None),
        'walking': (Sport.WALKING, None),
        'trail_running': (Sport.RUNNING, getattr(SubSport, 'TRAIL', SubSport.GENERIC))
    }
    
    if new_sport not in sport_mapping:
        logger.error(f"Deporte no válido: {new_sport}")
        raise ValueError(f"Deporte '{new_sport}' no es válido. Debe ser uno de {list(sport_mapping.keys())}")

    # Obtener el valor de Sport y SubSport
    sport_value, subsport_value = sport_mapping[new_sport]
    
    # Loggear información de depuración
    logger.info(f"Valores disponibles de Sport: {[attr for attr in dir(Sport) if not attr.startswith('_')]}")
    logger.info(f"Valores disponibles de SubSport: {[attr for attr in dir(SubSport) if not attr.startswith('_')]}")
    logger.info(f"Parámetros aceptados por FileIdMessage: {inspect.signature(FileIdMessage.__init__)}")
    
    # Reiniciar el puntero del archivo
    input_file.seek(0)
    
    try:
        # Verificar el archivo FIT con fitparse
        fitfile = FitFile(input_file)
        file_id_found = False
        file_id_fields = {}
        
        # Leer mensajes file_id
        for record in fitfile.get_messages('file_id'):
            file_id_found = True
            file_id_fields = {field.name: field.value for field in record if field.value is not None}
            logger.info(f"Mensaje file_id encontrado con campos: {file_id_fields}")
            break
        
        # Reiniciar el puntero para procesar de nuevo
        input_file.seek(0)
        
        # Crear un nuevo archivo FIT con fit-tool
        builder = FitFileBuilder(auto_define=True)
        
        # Añadir o modificar el mensaje file_id
        if file_id_found:
            # Intentar diferentes nombres para el campo sport
            field_attempts = [
                {'sport': sport_value},
                {'sport_type': sport_value},
                {'activity_type': sport_value}
            ]
            if subsport_value:
                for attempt in field_attempts:
                    attempt['sub_sport'] = subsport_value
            field_attempts.append({'time_created': file_id_fields.get('time_created', round(datetime.datetime.now().timestamp() * 1000))})
            
            success = False
            for attempt in field_attempts:
                try:
                    builder.add(FileIdMessage(**attempt))
                    logger.info(f"Éxito al añadir file_id con campos: {attempt}")
                    success = True
                    break
                except Exception as e:
                    logger.warning(f"Fallo al intentar file_id con campos {attempt}: {str(e)}")
                    continue
            
            if not success:
                logger.error("No se pudo añadir file_id con ningún conjunto de campos")
                raise ValueError("No se pudo añadir el mensaje file_id: ningún conjunto de campos fue aceptado")
        else:
            # Crear un nuevo mensaje file_id si no existe
            logger.info("No se encontró mensaje file_id, creando uno nuevo")
            field_attempts = [
                {'sport': sport_value},
                {'sport_type': sport_value},
                {'activity_type': sport_value}
            ]
            if subsport_value:
                for attempt in field_attempts:
                    attempt['sub_sport'] = subsport_value
            field_attempts.append({'time_created': round(datetime.datetime.now().timestamp() * 1000)})
            
            success = False
            for attempt in field_attempts:
                try:
                    builder.add(FileIdMessage(**attempt))
                    logger.info(f"Éxito al crear file_id con campos: {attempt}")
                    success = True
                    break
                except Exception as e:
                    logger.warning(f"Fallo al intentar crear file_id con campos {attempt}: {str(e)}")
                    continue
            
            if not success:
                logger.error("No se pudo crear file_id con ningún conjunto de campos")
                raise ValueError("No se pudo crear el mensaje file_id: ningún conjunto de campos fue aceptado")
        
        # Copiar otros mensajes del archivo original
        input_file.seek(0)
        fitfile = FitFile(input_file)
        for record in fitfile.get_messages():
            if record.name != 'file_id':
                fields = {field.name: field.value for field in record if field.value is not None}
                try:
                    builder.add_message(record.name, **fields)
                except Exception as e:
                    logger.warning(f"No se pudo añadir mensaje {record.name}: {str(e)}")
                    continue
        
        # Generar el archivo FIT en memoria
        try:
            fit_file = builder.build()
            output = BytesIO()
            fit_file.to_bytes(output)
            output.seek(0)
            logger.info("Archivo FIT generado exitosamente")
            return output, None
        except Exception as e:
            logger.error(f"Error al generar archivo FIT con fit-tool: {str(e)}")
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
