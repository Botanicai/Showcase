import os
import json
import logging
from flask import Flask, request, jsonify

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# Конфигурация
MAX_API_TOKEN = os.getenv('MAX_API_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Путь к файлу состояний
STATES_FILE = 'data/states.json'

# ---------- РАБОТА С СОСТОЯНИЯМИ (FSM) ----------
def load_states():
    """Загружает состояния пользователей из JSON"""
    try:
        with open(STATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_states(states):
    """Сохраняет состояния пользователей в JSON"""
    with open(STATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(states, f, ensure_ascii=False, indent=2)

def get_user_state(user_id):
    """Возвращает текущее состояние пользователя"""
    states = load_states()
    return states.get(str(user_id), {'step': 'main_menu'})

def set_user_state(user_id, state_data):
    """Устанавливает состояние пользователя"""
    states = load_states()
    states[str(user_id)] = state_data
    save_states(states)

# ---------- ТЕКСТЫ СООБЩЕНИЙ ----------
WELCOME_TEXT = """
🤖 Добро пожаловать в BotanicAI — интерактивную витрину AI-ассистентов для бизнеса!

Здесь вы можете протестировать, как боты могут работать в вашей компании.

📋 Выберите сценарий, который вас интересует:

1️⃣ Сбор заявок
2️⃣ Запись на услуги
3️⃣ Языковая школа
4️⃣ Карта покупателя
5️⃣ Проверка поставщиков
6️⃣ Недвижимость
7️⃣ Персональная консультация

Просто отправьте номер пункта меню.
"""

# ---------- ОБРАБОТЧИК СООБЩЕНИЙ ----------
def handle_message(user_id, text):
    """Основная логика обработки сообщений"""
    state = get_user_state(user_id)
    current_step = state.get('step', 'main_menu')
    
    # Если пользователь в главном меню
    if current_step == 'main_menu':
        return handle_main_menu(user_id, text)
    
    # Если пользователь в одном из сценариев
    elif current_step == 'language_school':
        from scenarios.language_school import handle
        return handle(user_id, text, state)
    
    elif current_step == 'customer_card':
        from scenarios.customer_card import handle
        return handle(user_id, text, state)
    
    elif current_step == 'consultation':
        from scenarios.consultation import handle
        return handle(user_id, text, state)
    
    elif current_step == 'lead_collection':
        from scenarios.lead_collection import handle
        return handle(user_id, text, state)
    
    # ... другие сценарии
    
    else:
        # Сброс в главное меню
        set_user_state(user_id, {'step': 'main_menu'})
        return WELCOME_TEXT

def handle_main_menu(user_id, text):
    """Обработка выбора пункта меню"""
    if text == '1':
        set_user_state(user_id, {'step': 'lead_collection'})
        return "📩 Вы выбрали сценарий «Сбор заявок». Давайте посмотрим, как это работает..."
    
    elif text == '2':
        set_user_state(user_id, {'step': 'appointment'})
        return "📅 Вы выбрали сценарий «Запись на услуги». Давайте посмотрим, как это работает..."
    
    elif text == '3':
        set_user_state(user_id, {'step': 'language_school'})
        return "📚 Вы выбрали сценарий «Языковая школа». Давайте посмотрим, как это работает..."
    
    elif text == '4':
        set_user_state(user_id, {'step': 'customer_card'})
        return "💳 Вы выбрали сценарий «Карта покупателя». Давайте посмотрим, как это работает..."
    
    elif text == '5':
        set_user_state(user_id, {'step': 'supplier_check'})
        return "🔍 Вы выбрали сценарий «Проверка поставщиков». Давайте посмотрим, как это работает..."
    
    elif text == '6':
        set_user_state(user_id, {'step': 'realty'})
        return "🏠 Вы выбрали сценарий «Недвижимость». Давайте посмотрим, как это работает..."
    
    elif text == '7':
        set_user_state(user_id, {'step': 'consultation'})
        return "📞 Вы выбрали сценарий «Персональная консультация». Давайте посмотрим, как это работает..."
    
    elif text.lower() in ['назад', 'menu']:
        set_user_state(user_id, {'step': 'main_menu'})
        return WELCOME_TEXT
    
    else:
        return "⚠️ Пожалуйста, выберите пункт меню от 1 до 7 или напишите «назад»."

# ---------- ОБРАБОТЧИК WEBHOOK (для MAX) ----------
@app.route('/webhook', methods=['POST'])
def webhook():
    """Точка входа для сообщений из MAX"""
    data = request.json
    logger.info(f"Получено сообщение: {data}")
    
    # Извлекаем user_id и текст
    user_id = data.get('user_id')
    text = data.get('message', {}).get('text', '')
    
    if not user_id:
        return jsonify({'status': 'error', 'message': 'No user_id'}), 400
    
    # Генерируем ответ
    response_text = handle_message(user_id, text)
    
    # Отправляем ответ в MAX (здесь нужна интеграция с API MAX)
    # Пока возвращаем текст для отладки
    return jsonify({
        'status': 'ok',
        'response': response_text
    })

# ---------- ЗАПУСК ----------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)