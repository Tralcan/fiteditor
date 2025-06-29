from flask import Flask, request, render_template, send_file
import os
from fitparse import FitFile
import fitencode
from io import BytesIO
import tempfile

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

    # Parsear el archivo FIT original con fitparse
    fitfile = FitFile(input_file)
    sport_found = False
    file_id_found = False
    
    # Crear un nuevo archivo FIT con fitencode
    fit_file = fitencode.FitFile()
    
    # Copiar todos los mensajes, modificando o añadiendo el mensaje file_id
    for record in fitfile.get_messages():
        if record.name == 'file_id':
            file_id_found = True
            fields = {field.name: field.value for field in record}
            if fields.get('sport') is not None:
                sport_found = True
                fields['sport'] = new_sport  # Modificar el campo sport
            else:
                fields['sport'] = new_sport  # Añadir el campo sport si no existe
            fit_file.add_message('file_id', **fields)
        else:
            # Copiar otros mensajes sin modificar
            fields = {field.name: field.value for field in record}
            fit_file.add_message(record.name, **fields)
    
    # Si no se encontró un mensaje file_id, crear uno nuevo
    if not file_id_found:
        fit_file.add_message('file_id', type='activity', sport=new_sport, time_created=fitencode.types.field_types.DateTime.now())
        sport_found = True

    if not sport_found:
        return None, "Advertencia: No se pudo modificar el campo 'sport'. Se devuelve el archivo original."

    # Generar el archivo FIT en memoria
    output = BytesIO()
    output.write(fit_file.to_bytes())
    output.seek(0)
    return output, None

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
                
                if modified_file is None:
                    # Devolver el archivo original si no se pudo modificar
                    input_file = BytesIO(file.stream.read())
                    input_file.seek(0)
                    return send_file(
                        input_file,
                        download_name=f'modified_{file.filename}',
                        as_attachment=True,
                        mimetype='application/octet-stream'
                    ), render_template('index.html', warning=warning)
                
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
                return render_template('index.html', error=f'Error al procesar el archivo: {str(e)}')
        else:
            return render_template('index.html', error='Archivo no válido. Por favor, sube un archivo .fit')
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
