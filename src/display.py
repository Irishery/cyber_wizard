import cv2
from flask import Flask, Response
import time
import threading
import queue


class Display:
    def __init__(self, fps=20):
        self.app = Flask(__name__)
        self.image_queue = queue.Queue(maxsize=1)  # Очередь для безопасной передачи изображений
        self.current_image = None
        self.sleep_time = 1.0 / fps
        self.lock = threading.Lock()
        self.running = True

        # Запускаем поток для обновления изображений
        self.update_thread = threading.Thread(target=self._update_image_loop, daemon=True)
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

    def set_image(self, image_path: str):
        img = cv2.imread(image_path)
        if img is not None:
            try:
                # Неблокирующая попытка добавить изображение в очередь
                self.image_queue.put_nowait(img)
            except queue.Full:
                # Если очередь полна, заменяем изображение
                with self.image_queue.mutex:
                    self.image_queue.queue.clear()
                self.image_queue.put_nowait(img)

    def run(self):
        @self.app.route('/video_feed')
        def video_feed():
            return Response(self.generate_frames(),
                            mimetype='multipart/x-mixed-replace; boundary=frame')

        self.app.run(host='0.0.0.0', port=5000)

    def stop(self):
        self.running = False
        self.update_thread.join()


if __name__ == '__main__':
    display = Display(fps=20)

    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=display.run, daemon=True)
    server_thread.start()

    try:
        # Устанавливаем первое изображение
        display.set_image("data/test.jpg")
        time.sleep(5)  # Ждем 5 секунд

        # Меняем изображение
        display.set_image("data/test2.jpg")

        # Держим программу активной
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        display.stop()
