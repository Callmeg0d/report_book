from PyQt5 import QtWidgets, QtCore

import psycopg2
import os

from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')


class StudentProfile(QtWidgets.QWidget):
    """
    Интерфейс студента с правами только просмотра
    """
    def __init__(self, first_name, last_name, middle_name):
        super().__init__()
        self.setWindowTitle("Профиль студента")
        self.setGeometry(600, 400, 500, 350)

        layout = QtWidgets.QVBoxLayout()

        layout.addStretch(1)

        self.name_label = QtWidgets.QLabel(f"Пользователь: {first_name} {last_name} {middle_name}")
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_label)
        layout.addStretch(7)

        self.setLayout(layout)


class TeacherProfile(QtWidgets.QWidget):
    """
    Интерфес преподавателя с правами вносить оценку студентам
    """
    def __init__(self, first_name, last_name, middle_name, teacher_id):
        super().__init__()
        self.setWindowTitle("Профиль преподавателя")
        self.setGeometry(750, 400, 500, 350)

        layout = QtWidgets.QVBoxLayout()

        layout.addStretch(1)

        self.name_label = QtWidgets.QLabel(f"Пользователь: {first_name} {last_name} {middle_name}")
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_label)

        self.grade_button = QtWidgets.QPushButton("Выставить оценку", self)
        self.grade_button.clicked.connect(lambda: self.open_grade_form(teacher_id))
        layout.addWidget(self.grade_button)

        layout.addStretch(7)

        self.setLayout(layout)

    def open_grade_form(self, teacher_id):
        self.grade_form = GradeForm(teacher_id)
        self.grade_form.show()

class GradeForm(QtWidgets.QWidget):
    """
    Форма, содержащая поля для внесения данных студента и оценки
    """
    def __init__(self, teacher_id):
        super().__init__()
        self.teacher_id = teacher_id  # ID преподавателя, который авторизован
        self.setWindowTitle("Выставление оценки")
        self.setGeometry(750, 400, 500, 350)
        layout = QtWidgets.QVBoxLayout()

        self.first_name_input = QtWidgets.QLineEdit(self)
        self.first_name_input.setPlaceholderText("Имя студента")
        layout.addWidget(self.first_name_input)

        self.last_name_input = QtWidgets.QLineEdit(self)
        self.last_name_input.setPlaceholderText("Фамилия студента")
        layout.addWidget(self.last_name_input)

        self.group_input = QtWidgets.QLineEdit(self)
        self.group_input.setPlaceholderText("Группа студента")
        layout.addWidget(self.group_input)

        self.subject_input = QtWidgets.QLineEdit(self)
        self.subject_input.setPlaceholderText("Название предмета")
        layout.addWidget(self.subject_input)

        self.grade_input = QtWidgets.QLineEdit(self)
        self.grade_input.setPlaceholderText("Оценка")
        layout.addWidget(self.grade_input)

        self.submit_button = QtWidgets.QPushButton("Выставить оценку", self)
        self.submit_button.clicked.connect(self.submit_grade)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def submit_grade(self):
        first_name = self.first_name_input.text()
        last_name = self.last_name_input.text()
        group_name = self.group_input.text()
        subject_name = self.subject_input.text()
        grade = self.grade_input.text()

        try:
            conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
                                    host=DB_HOST)
            cursor = conn.cursor()

            # Получаем id студента
            cursor.execute(
                "SELECT id FROM students WHERE first_name=%s AND last_name=%s AND group_id=(SELECT id FROM groups_name WHERE group_name=%s)",
                (first_name, last_name, group_name))
            student_id_result = cursor.fetchone()
            if student_id_result:
                student_id = student_id_result[0]

                # Проверяем наличие предмета
                cursor.execute("SELECT id FROM subjects WHERE name=%s", (subject_name,))
                subject_id_result = cursor.fetchone()

                if subject_id_result:
                    subject_id = subject_id_result[0]
                else:
                    cursor.execute("INSERT INTO subjects (name) VALUES (%s) RETURNING id", (subject_name,))
                    subject_id = cursor.fetchone()[0]
                    conn.commit()

                cursor.execute("INSERT INTO grades (student_id, subject_id, teacher_id, grade) VALUES (%s, %s, %s, %s)",
                               (student_id, subject_id, self.teacher_id, grade))
                conn.commit()
                QtWidgets.QMessageBox.information(self, "Успех", "Оценка успешно выставлена!")
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            else:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Студент не найден.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
