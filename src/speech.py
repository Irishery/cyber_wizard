# speech_recognition.py
import speech_recognition as sr
import requests
from threading import Thread


class SpeechRecognition:
    def __init__(self, api_key, keyword, promt):
        self.recognizer = sr.Recognizer()
        self.api_key = api_key  # OpenRouter API key
        # OpenRouter API endpoint
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.keyword = keyword
        self.stop_listening = False
        self.promt = promt

    def listen_keyword(self):
        with sr.Microphone() as source:
            print("Ожидание ключевого слова...")
            while not self.stop_listening:
                audio = self.recognizer.listen(source, phrase_time_limit=2)
                try:
                    # Локальное распознавание ключевого слова через Google
                    text = self.recognizer.recognize_google(
                        audio, language='ru-RU')
                    if self.keyword in text.lower():
                        print(f"Ключевое слово '{self.keyword}' обнаружено!")
                        self.on_keyword_detected()
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as e:
                    print(f"Ошибка сервиса распознавания речи: {e}")

    def on_keyword_detected(self):
        with sr.Microphone() as source:
            print("Слушаю...")
            audio = self.recognizer.listen(source)
            try:
                # Локальное распознавание текста через Google
                user_text = self.recognizer.recognize_google(
                    audio, language='ru-RU')
                print(f"Вы сказали: {user_text}")

                # Отправляем распознанный текст в OpenRouter API (DeepSeek)
                response_text = self.send_to_deepseek(user_text)

                # Обновляем интерфейс и управляем железом
                if response_text:
                    print(f"Ответ от DeepSeek: {response_text}")
            except sr.UnknownValueError:
                print("Не удалось распознать речь")
            except sr.RequestError as e:
                print(f"Ошибка сервиса распознавания речи: {e}")

    def send_to_deepseek(self, text):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            "model": "deepseek/deepseek-chat:free",  # DeepSeek model on OpenRouter
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{self.promt}, студент сказал: {text}"},
            ],
        }

        try:
            # Отправляем POST-запрос к OpenRouter API
            response = requests.post(self.api_url, json=data, headers=headers)
            if response.status_code == 200:
                # Извлекаем ответ из JSON
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(
                    f"Ошибка при запросе к OpenRouter API: {response.status_code}")
                return None
        except Exception as e:
            print(f"Ошибка при работе с OpenRouter API: {str(e)}")
            return None

    def start_listening(self):
        self.stop_listening = False
        self.thread = Thread(target=self.listen_keyword)
        self.thread.start()

    def stop_listening(self):
        self.stop_listening = True
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join()
