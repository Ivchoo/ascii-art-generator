import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from redis import Redis
from pyfiglet import Figlet

app = Flask(__name__)
# Разрешаваме CORS, за да може браузърът свободно да комуникира с Flask
CORS(app)

# Свързване с Redis контейнера (използваме името на услугата от compose.yml - 'redis-cache')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-cache')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

try:
    cache = Redis(host=REDIS_HOST, port=REDIS_PORT, socket_timeout=2)
except Exception as e:
    print(f"Initial Redis connection setup warning: {e}")
    cache = None


@app.route('/generate', methods=['GET', 'POST'])
def generate_ascii():
    text = None
    
    if request.method == 'GET':
        text = request.args.get('text', '')
        
    elif request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            if data:
                text = data.get('text', '')
        else:
            text = request.form.get('text', '')

    if not text or text.strip() == '':
        return jsonify({"error": "Моля, въведете текст за генериране!"}), 400

    text = text.strip()

    if cache:
        try:
            cached_result = cache.get(text)
            if cached_result:
                print(f"[CACHE HIT] Намерен кеширан арт за: '{text}'")
                return jsonify({
                    "ascii": cached_result.decode('utf-8'),
                    "cached": True
                })
        except Exception as e:
            print(f"[REDIS ERROR] Грешка при четене от кеша: {e}")

    print(f"[CACHE MISS] Генериране на нов арт за: '{text}'")
    try:
        f = Figlet(font='standard')
        ascii_art = f.renderText(text)
    except Exception as e:
        return jsonify({"error": f"Грешка при генериране на арта: {str(e)}"}), 500

    if cache:
        try:
            cache.set(text, ascii_art, ex=60)
            print(f"[CACHE SAVE] Успешно кеширан арт за 60 секунди.")
        except Exception as e:
            print(f"[REDIS ERROR] Грешка при запис в кеша: {e}")

    return jsonify({
        "ascii": ascii_art,
        "cached": False
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Проверка дали бекендът е жив и дали вижда Redis"""
    redis_status = "Disconnected"
    if cache:
        try:
            if cache.ping():
                redis_status = "Connected"
        except Exception:
            pass
            
    return jsonify({
        "status": "healthy",
        "redis": redis_status
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)