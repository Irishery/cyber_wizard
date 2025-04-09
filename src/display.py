import cv2
from flask import Flask, Response
import time
import threading
import queue


# Словарь действий, где ключ — название действия, а значение — путь к картинке
ACTIONS = {
    "neutral": "data/test.jpg",      # Спокойный
    "happy": "data/download.jpeg",          # Радостный
    "angry": "data/test.jpg",          # Злой
    "surprised": "data/test.jpg",  # Удивлённый
    "sad": "data/test.jpg",              # Грустный
    "talking": "data/test.jpg",      # Говорит
    "thinking": "data/test.jpg",    # Думает
}


class Display:
    def __init__(self, fps=20):
        self.app = Flask(__name__)
        # Очередь для безопасной передачи изображений
        self.image_queue = queue.Queue(maxsize=1)
        self.current_image = None
        self.current_action = None  # Текущее действие (название)
        self.sleep_time = 1.0 / fps
        self.lock = threading.Lock()
        self.running = True

        # Запускаем поток для обновления изображений
        self.update_thread = threading.Thread(
            target=self._update_image_loop, daemon=True)
        self.update_thread.start()

    def _update_image_loop(self):
        while self.running:
            try:
                # Блокируем получение нового изображения с таймаутом
                new_image = self.image_queue.get(timeout=0.1)
                with self.lock:
                    self.current_image = new_image
            except queue.Empty:
                continue

    def generate_frames(self):
        while True:
            with self.lock:
                if self.current_image is not None:
                    _, jpeg = cv2.imencode('.jpg', self.current_image)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(self.sleep_time)

    def set_action(self, action: str):
        """Устанавливает изображение на основе действия"""
        if action in ACTIONS:
            img = cv2.imread(ACTIONS[action])
            if img is not None:
                try:
                    self.image_queue.put_nowait(img)
                    self.current_action = action
                except queue.Full:
                    with self.image_queue.mutex:
                        self.image_queue.queue.clear()
                    self.image_queue.put_nowait(img)
        else:
            print(f"Действие '{action}' не найдено!")

    def run(self):
        @self.app.route('/video_feed')
        def video_feed():
            return Response(self.generate_frames(),
                            mimetype='multipart/x-mixed-replace; boundary=frame')

        self.app.run(host='0.0.0.0', port=5000)

    def stop(self):
        self.running = False
        self.update_thread.join()
