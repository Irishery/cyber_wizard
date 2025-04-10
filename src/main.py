from speech import SpeechRecognition
from display import Display
from dotenv import load_dotenv
import threading
import os
import time
# Импортируем наш класс FaceRecognition
from camera import FaceRecognition

load_dotenv()

AIPROMT = """Ты — Михаил Тарачков, преподаватель программирования и робототехники БФУ им. Канта, но сегодня ты в роли робота-гадалки. Твоя задача — давать студентам шуточные предсказания на основе их запроса. Ты можешь:

Шутить про отчисления, дедлайны и бессонные ночи.

Давать абсурдные или обнадёживающие прогнозы.

Импровизировать в академическо-студенческой тематике.

Твой ответ должен быть только текстом для речи, без описаний действий или эмоций. После ответа укажи эмоцию из списка ("neutral", "happy", "angry", "surprised", "sad"), которую нужно изобразить.

Формат ответа:
text: текст для речи
emotion: эмоция"""


def main():
    # Инициализация Display в фоновом режиме
    display = Display(fps=20)
    display_thread = threading.Thread(target=display.run, daemon=True)
    display_thread.start()

    # Устанавливаем начальное состояние
    display.set_action("neutral")

    # Инициализация FaceRecognition для распознавания конкретного человека
    face_recognition = FaceRecognition(
        known_person_folder="tarachkov_camera", tolerance=0.5)
    face_recognition_thread = threading.Thread(
        target=face_recognition.run, daemon=True)
    face_recognition_thread.start()

    # Инициализация и запуск распознавания речи
    speech = SpeechRecognition(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        keyword="привет",
        promt=AIPROMT,
        audio_server="XXXXXXXXXXXXXXXXXXXXX",
        display=display
    )
    speech_thread = threading.Thread(
        target=speech.start_listening, daemon=True)
    speech_thread.start()  # Запускаем распознавание речи сразу

    try:
        # Основной цикл главного потока
        while True:
            # Проверяем, распозналось ли лицо
            if face_recognition.known_face_name != "Неизвестный":
                print(f"Лицо распознано: {face_recognition.known_face_name}")
                display.set_action("happy")  # Изменяем состояние Display

            # Здесь можно добавлять логику взаимодействия между модулями
            # Например, менять состояние Display в зависимости от событий SpeechRecognition
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nЗавершение работы...")
        # Корректное завершение (хотя daemon-потоки завершатся автоматически)
        display.stop()
        speech.stop()  # Предполагая, что такой метод есть в SpeechRecognition


if __name__ == "__main__":
    main()
