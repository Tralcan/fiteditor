from flask import Flask, request, render_template, send_file
import os
from fitparse import FitFile
from io import BytesIO
import tempfile

app = Flask(__name__, template_folder="../templates")

# Directorio para almacenar archivos temporales
UPLOAD_FOLDER = "/tmp"
ALLOWED_EXTENSIONS = {'fit'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def modify_fit_sport(input_file, new_sport):
    # Parsear el archivo FIT
    fitfile = FitFile(input_file)
    
    # Crear un nuevo archivo FIT en memoria
    output = BytesIO()
    
    # Copiar todos los mensajes del archivo original
    for record in fitfile.get_messages():
        # Modificar el mensaje 'file_id' si contiene el campo 'sport'
        if record.name == 'file_id':
            if record.get_value('sport') is not None:
                record.set_value('sport', new_sport)
        
        # Escribir el mensaje en el nuevo archivo
        for data in record.get_values():
            output.write(data)
    
    output.seek(0)
    return output

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
                modified_file = modify_fit_sport(file.stream, new_sport)
                
                # Enviar el archivo modificado para descarga
                return send_file(
                    modified_file,
                    download_name=f'modified_{file.filename}',
                    as_attachment=True,
                    mimetype='application/octet-stream'
                )
            except Exception as e:
                return render_template('index.html', error=f'Error al procesar el archivo: {str(e)}')
        else:
            return render_template('index.html', error='Archivo no válido. Por favor, sube un archivo .fit')
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run()