from flask import Flask, request, jsonify, render_template
import requests
from requests.auth import HTTPBasicAuth
from googletrans import Translator
import subprocess
import os

app = Flask(__name__)

# Configuración de credenciales y URLs de IBM Watson
apikey_speech_to_text = 'pa91z_uM34C4vBWw4_iWgNpKmi-kddkBgPT--_TSrLvT'
speech_to_text_url = 'https://api.us-south.speech-to-text.watson.cloud.ibm.com/instances/6a7db253-4b33-4a64-9b82-a4e10311c4ee/v1/recognize'

apikey_text_to_speech = 'C2SnxIM9Fd4dpsvBirKbUv7K6frc4gx7Qf_rD660Pcve'
text_to_speech_url = 'https://api.au-syd.text-to-speech.watson.cloud.ibm.com/instances/6fbe14a8-30f3-4267-b7ca-754680a399ee/v1/synthesize'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        # Imprimir detalles de la solicitud
        print("Archivos recibidos:", request.files)
        print("Campos de formulario recibidos:", request.form)

        # Obtener el archivo de audio
        audio_file = request.files.get('audio')
        if not audio_file:
            print("No se recibió el archivo de audio.")
            return jsonify({'error': 'No se recibió el archivo de audio.'}), 400

        lang = request.form.get('language', 'es-ES')  # Idioma por defecto en español
        model = f'{lang}_NarrowbandModel'

        headers = {
            'Content-Type': audio_file.content_type
        }
        auth = ('apikey', apikey_speech_to_text)

        # Enviar la solicitud a IBM Watson
        response = requests.post(
            f'{speech_to_text_url}?model={model}',
            headers=headers,
            auth=auth,
            data=audio_file
        )

        # Imprimir la respuesta del servicio
        print("Respuesta del servicio de transcripción:", response.text)

        if response.status_code == 200:
            result = response.json()
            transcript = result['results'][0]['alternatives'][0]['transcript']
            return jsonify({'transcript': transcript})
        else:
            print(f"Error al transcribir el audio: {response.status_code} - {response.text}")
            return jsonify({'error': 'Error al transcribir el audio.'}), response.status_code

    except Exception as e:
        print("Error en la transcripción:", str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text')
        source_lang = data.get('sourceLang', 'es')
        target_lang = data.get('targetLang', 'en')

        # Crear un objeto traductor
        translator = Translator()

        # Traducir el texto
        translation = translator.translate(text, src=source_lang, dest=target_lang)
        translated_text = translation.text

        # Llamar al servicio de texto a voz
        voice = 'es-LA_DanielaExpressive' if target_lang == 'es' else 'en-US_MichaelExpressive'
        text_to_speech_response = requests.post(
            f'{text_to_speech_url}?voice={voice}',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'audio/wav'
            },
            json={'text': translated_text},
            auth=HTTPBasicAuth('apikey', apikey_text_to_speech)
        )

        if text_to_speech_response.status_code == 200:
            audio_path = 'static/voice.wav'
            with open(audio_path, 'wb') as f:
                f.write(text_to_speech_response.content)
        else:
            return jsonify({'error': 'Error al convertir el texto a voz.'}), text_to_speech_response.status_code

        return jsonify({
            'translation': translated_text,
            'audio_url': '/static/voice.wav'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/run-sign-language', methods=['POST'])
def run_sign_language():
    try:
        # Ejecuta el script de Python
        subprocess.Popen(['python', 'señas.py'])
        return jsonify({"status": "Script started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)





