import cv2
import face_recognition
import numpy as np
import os


class FaceRecognition:
    def __init__(self, known_person_folder="data", tolerance=0.5):
        """
        Инициализация класса FaceRecognition.

        :param known_person_folder: Путь к папке с эталонными фото одного человека.
        :param tolerance: Порог схожести (значение от 0 до 1).
        """
        self.known_face_encodings = []
        self.known_face_name = "Misha"  # По умолчанию имя неизвестно
        self.tolerance = tolerance
        self.load_known_faces(known_person_folder)

    def load_known_faces(self, folder_path):
        """
        Загрузка всех эталонных фото одного человека из указанной папки и вычисление средней кодировки.

        :param folder_path: Путь к папке с эталонными фото одного человека.
        """
        encodings = []

        for file in os.listdir(folder_path):
            # Поддерживаемые форматы файлов
            if file.endswith(".jpg") or file.endswith(".png"):
                image_path = os.path.join(folder_path, file)
                try:
                    known_image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(
                        known_image)

                    if len(face_encodings) > 0:
                        encodings.append(face_encodings[0])
                        # Имя человека берется из названия первой фотографии (без расширения)
                        if not self.known_face_name:
                            self.known_face_name = os.path.splitext(file)[0]
                    else:
                        print(
                            f"Не удалось найти лицо на изображении: {image_path}")
                except Exception as e:
                    print(f"Ошибка при загрузке изображения {image_path}: {e}")

        if encodings:
            # Вычисляем среднюю кодировку для всех фото одного человека
            self.known_face_encodings = [np.mean(encodings, axis=0)]
        else:
            print("Нет ни одного эталонного лица для распознавания!")

    def recognize_faces(self, frame):
        """
        Распознавание лиц на кадре.

        :param frame: Кадр с камеры (BGR формат OpenCV).
        :return: Измененный кадр с нарисованными прямоугольниками и текстом.
        """
        # Преобразуем BGR в RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Находим все лица в кадре
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(
            rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Сравниваем текущее лицо с эталонным
            matches = face_recognition.compare_faces(
                self.known_face_encodings, face_encoding, tolerance=self.tolerance)

            # Вычисляем "расстояние" между лицами
            face_distances = face_recognition.face_distance(
                self.known_face_encodings, face_encoding)

            name = "Unknown"
            color = (0, 0, 255)  # Красный цвет по умолчанию

            if face_distances.size > 0:
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    name = self.known_face_name
                    color = (0, 255, 0)  # Зеленый цвет для известных лиц

            # Рисуем прямоугольник вокруг лица
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Подписываем имя
            cv2.rectangle(frame, (left, bottom - 30),
                          (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Выводим процент схожести
            similarity = round(
                (1 - face_distances[best_match_index]) * 100, 2) if face_distances.size > 0 else 0
            cv2.putText(frame, f"{similarity}%", (right + 10, top + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 1)

        return frame

    def run(self):
        """
        Запуск системы распознавания лиц через веб-камеру.
        """
        video_capture = cv2.VideoCapture(0)  # 0 — стандартная камера

        while True:
            # Получаем кадр с камеры
            ret, frame = video_capture.read()

            if not ret:
                print("Не удалось получить кадр с камеры.")
                break

            # Распознаем лица на кадре
            processed_frame = self.recognize_faces(frame)

            # Показываем кадр
            cv2.imshow("Face Recognition", processed_frame)

            # Выход по нажатию 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Освобождаем камеру и закрываем окна
        video_capture.release()
        cv2.destroyAllWindows()
