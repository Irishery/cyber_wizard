# speech_recognition.py
import speech_recognition as sr
from display import Display
from camera import FaceRecognition
import requests
from threading import Thread
import pygame
import pygame._sdl2.audio as sdl2_audio
import time

supported_emotions = ["neutral", "happy",
                      "angry", "sad", "thinking", "surprised"]


def get_devices(capture_devices: bool = False):
    init_by_me = not pygame.mixer.get_init()
    if init_by_me:
        pygame.mixer.init()
    devices = tuple(sdl2_audio.get_audio_device_names(capture_devices))
    if init_by_me:
        pygame.mixer.quit()
    return devices


class SpeechRecognition:
    def __init__(self, api_key, keyword, promt, audio_server, display: Display, face: FaceRecognition):
        self.recognizer = sr.Recognizer()
        self.api_key = api_key  # OpenRouter API key
        # OpenRouter API endpoint
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.keyword = keyword
        self.stop_listening = False
        self.promt = promt
        self.audio_server = audio_server
        self.display = display
        self.face = face

    def run_audio(self, speech):
        # audio = requests.get(self.audio_server + "/audio", params={
        #                      "text": speech})

        response = requests.get(
            self.audio_server + "/govori",
            json={"text": speech, "language": "ru"}
        )

        with open("audio/test_output.wav", "wb") as f:
            f.write(response.content)
        print("Тест завершен, файл сохранен")

        pygame.mixer.init(
            devicename="Family 17h/19h HD Audio Controller Speaker + Headphones")

        pygame.mixer.music.load("audio/test_output.wav")
        pygame.mixer.music.play()

        # Ждём окончания воспроизведения
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        return True

    def listen_keyword(self):
        print(get_devices())
        print("asd")
        self.display.set_action("neutral")
        if self.face.current_face_name == "Misha":
            self.display.set_action("suprised")
            self.run_audio("АФИГЕТЬ КАК ТЫ ПОХОЖ НА МЕНЯ")
        with sr.Microphone(device_index=5) as source:
            print("Ожидание ключевого слова...")
            print(sr.Microphone.list_microphone_names())
            while not self.stop_listening:
                audio = self.recognizer.listen(source, phrase_time_limit=2)
                try:
                    print("FLAGFLAG")
                    self.display.set_action("neutral")
                    if self.face.current_face_name == "Misha":
                        print("FLAG")
                        self.display.set_action("surprised")
                        time.sleep(2)
                        self.run_audio("АФИГЕТЬ КАК ТЫ ПОХОЖ НА МЕНЯ")
                        self.face.current_face_name = "Unknown"
                        time.sleep(2)
                    print("flag1")
                    # Локальное распознавание ключевого слова через Google
                    text = self.recognizer.recognize_google(
                        audio, language='ru-RU')
                    print("flag2")
                    if self.keyword in text.lower():
                        self.display.set_action("thinking")
                        print(f"Ключевое слово '{self.keyword}' обнаружено!")
                        self.on_keyword_detected()
                    print("flag3")
                except sr.UnknownValueError:
                    next
                except sr.RequestError as e:
                    print(f"Ошибка сервиса распознавания речи: {e}")

    def on_keyword_detected(self):
        # if self.face.current_face_name == "Misha":
        #     self.display.set_action("suprised")
        #     self.run_audio("АФИГЕТЬ КАК ТЫ ПОХОЖ НА МЕНЯ")

        self.display.set_action("thinking")
        time.sleep(1)
        with sr.Microphone() as source:
            print("Слушаю...")
            audio = self.recognizer.listen(source, phrase_time_limit=10)
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
                    print(response_text)
                    print("--------")
                    print(response_text.split("text: ")
                          [1].split("emotion: ")[0])
                    print(response_text.split("emotion: ")[1])
                    print("--------")
                    try:
                        emotion = response_text.split("emotion: ")[1]
                        speech = response_text.split(
                            "text: ")[1].split("emotion: ")[0]
                        print(speech)
                        # print(response_text.split("text: "))
                        print("EMOTION ", emotion)
                        if emotion not in supported_emotions:
                            emotion = "neutral"
                        self.display.set_action(emotion)
                        time.sleep(2)
                        # if self.face.current_face_name == "Misha":
                        #     print("POHOZH")
                        #     self.display.set_action("surprised")
                        #     self.run_audio(
                        #         "*Говорящий очень похож на тебя* " + speech)

                        self.run_audio(speech)
                    except IndexError:
                        self.run_audio("Повтори пожалуйста")
                    self.display.set_action("neutral")
            except sr.UnknownValueError:
                print("Не удалось распознать речь")
                self.display.set_action("neutral")
            except sr.RequestError as e:
                print(f"Ошибка сервиса распознавания речи: {e}")
                self.display.set_action("neutral")

    def send_to_deepseek(self, text):
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            "model": "deepseek/deepseek-chat-v3-0324",  # DeepSeek model on OpenRouter
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
