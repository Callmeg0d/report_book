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

    def __init__(self, first_name, last_name, middle_name, student_id):
        super().__init__()

        self.setWindowTitle("Профиль студента")
        self.setGeometry(500, 200, 1000, 700)

        layout = QtWidgets.QVBoxLayout()

        central_widget = QtWidgets.QWidget()
        central_layout = QtWidgets.QVBoxLayout(central_widget)

        central_layout.addStretch(1)

        self.name_label = QtWidgets.QLabel(f"Пользователь: {first_name} {last_name} {middle_name}")
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        central_layout.addWidget(self.name_label)

        group_name, average_grade, subjects_info = self.get_student_info(student_id)

        self.group_label = QtWidgets.QLabel(f"Группа: {group_name}")
        self.group_label.setAlignment(QtCore.Qt.AlignCenter)
        central_layout.addWidget(self.group_label)

        self.grade_label = QtWidgets.QLabel(f"Средний балл: {average_grade:.2f}")
        self.grade_label.setAlignment(QtCore.Qt.AlignCenter)
        central_layout.addWidget(self.grade_label)

        central_layout.addStretch(1)

        # Создаем таблицу для отображения оценок
        self.table_widget = QtWidgets.QTableWidget()

        num_rows = len(subjects_info)
        self.table_widget.setRowCount(num_rows)
        self.table_widget.setColumnCount(3)

        self.table_widget.setHorizontalHeaderLabels(["Предмет", "Оценка", "Преподаватель"])

        for row_index, (subject_name, grade, teacher_full_name) in enumerate(subjects_info):
            subject_item = QtWidgets.QTableWidgetItem(subject_name)
            subject_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table_widget.setItem(row_index, 0, subject_item)

            grade_item = QtWidgets.QTableWidgetItem(str(grade))
            grade_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table_widget.setItem(row_index, 1, grade_item)

            teacher_item = QtWidgets.QTableWidgetItem(teacher_full_name)
            teacher_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table_widget.setItem(row_index, 2, teacher_item)

        self.table_widget.setColumnWidth(0, 300)
        self.table_widget.setColumnWidth(1, 100)
        self.table_widget.setColumnWidth(2, 150)

        # Центрируем таблицу
        self.table_widget.horizontalHeader().setStretchLastSection(True)

        # Устанавливаем размер таблицы
        self.table_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Запрет редактирования ячеек
        self.table_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # Устанавливаем фиксированную высоту таблицы
        row_height = self.table_widget.rowHeight(0)  # Получаем высоту первой строки
        self.table_widget.setFixedHeight(row_height * min(num_rows, 10))

        central_layout.addWidget(self.table_widget)

        central_layout.addStretch(6)

        layout.addWidget(central_widget)
        self.setLayout(layout)

    def get_student_info(self, student_id):
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST
            )
            cursor = conn.cursor()

            query = """
                SELECT g.group_name, s.average_grade, sub.name AS subject_name, 
                       gr.grade, t.first_name, t.last_name, t.middle_name
                FROM students s
                JOIN groups_name g ON s.group_id = g.id
                LEFT JOIN grades gr ON s.id = gr.student_id
                LEFT JOIN subjects sub ON gr.subject_id = sub.id
                LEFT JOIN teachers t ON gr.teacher_id = t.id
                WHERE s.id = %s
            """

            cursor.execute(query, (student_id,))
            results = cursor.fetchall()
            cursor.close()

        except Exception as e:
            print("Ошибка при подключении к базе данных:", e)
            return ("Неизвестная группа", 0.0, [])

        finally:
            if conn:
                conn.close()

        if results:
            group_name = results[0][0]
            average_grade = results[0][1]
            subjects_info = [(row[2], row[3], f"{row[4]} {row[5]} {row[6]}") for row in results]
            return group_name, average_grade, subjects_info
        else:
            return ("Неизвестная группа", 0.0, [])


class TeacherProfile(QtWidgets.QWidget):
    """
    Интерфес преподавателя с правами вносить оценку студентам
    """

    def __init__(self, first_name, last_name, middle_name, teacher_id):
        super().__init__()

        self.setWindowTitle("Профиль преподавателя")
        self.setGeometry(500, 200, 1000, 700)

        layout = QtWidgets.QVBoxLayout()

        layout.addStretch(1)

        self.name_label = QtWidgets.QLabel(f"Пользователь: {first_name} {last_name} {middle_name}")
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_label)

        self.grade_button = QtWidgets.QPushButton("Выставить оценку", self)
        self.grade_button.clicked.connect(lambda: self.open_grade_form(teacher_id))
        layout.addWidget(self.grade_button)

        layout.addStretch(1)

        self.table_widget = QtWidgets.QTableWidget()

        grades_info = self.get_grades_for_teacher(teacher_id)  # Получаем оценки для преподавателя

        num_rows = len(grades_info)
        self.table_widget.setRowCount(num_rows)
        self.table_widget.setColumnCount(3)

        self.table_widget.setHorizontalHeaderLabels(["Предмет", "Оценка", "Cтудент"])

        for row_index, (subject_name, grade, student_full_name) in enumerate(grades_info):
            subject_item = QtWidgets.QTableWidgetItem(subject_name)
            subject_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table_widget.setItem(row_index, 0, subject_item)

            grade_item = QtWidgets.QTableWidgetItem(str(grade))
            grade_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table_widget.setItem(row_index, 1, grade_item)

            student_item = QtWidgets.QTableWidgetItem(student_full_name)
            student_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.table_widget.setItem(row_index, 2, student_item)

        self.table_widget.setColumnWidth(0, 300)
        self.table_widget.setColumnWidth(1, 100)
        self.table_widget.setColumnWidth(2, 150)

        self.table_widget.horizontalHeader().setStretchLastSection(True)

        self.table_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        #self.table_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        row_height = self.table_widget.rowHeight(0)
        self.table_widget.setFixedHeight(row_height * min(num_rows, 10))

        layout.addWidget(self.table_widget)

        layout.addStretch(6)

        self.setLayout(layout)

    def open_grade_form(self, teacher_id):
        self.grade_form = GradeForm(teacher_id)
        self.grade_form.show()

    def get_grades_for_teacher(self, teacher_id):
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST
            )
            cursor = conn.cursor()

            query = """
                SELECT sub.name AS subject_name, gr.grade, 
                       s.first_name, s.last_name, s.middle_name
                FROM grades gr
                JOIN subjects sub ON gr.subject_id = sub.id
                JOIN students s ON gr.student_id = s.id
                WHERE gr.teacher_id = %s
            """

            cursor.execute(query, (teacher_id,))
            results = cursor.fetchall()
            cursor.close()

        except Exception as e:
            print("Ошибка при подключении к базе данных:", e)
            return [], []

        finally:
            if conn:
                conn.close()

        if results:
            subjects_info = [(row[0], row[1], f"{row[2]} {row[3]} {row[4]}") for row in results]
            return subjects_info
        else:
            return []


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
                cursor.execute("SELECT id FROM subjects WHERE name=%s AND teacher_id=%s",
                               (subject_name, self.teacher_id))
                subject_id_result = cursor.fetchone()

                if subject_id_result:
                    subject_id = subject_id_result[0]
                else:
                    cursor.execute("INSERT INTO subjects (name, teacher_id) VALUES (%s, %s) RETURNING id",
                                   (subject_name, self.teacher_id))
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

