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
        self.setGeometry(470, 200, 1000, 700)

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

        group_name, average_grade, subjects_info = self.get_student_info(student_id)

        num_rows = len(subjects_info)
        self.table_widget.setRowCount(num_rows if num_rows > 0 else 1)  # Устанавливаем 1 строку, если нет оценок
        self.table_widget.setColumnCount(3)

        # Устанавливаем заголовки таблицы
        self.table_widget.setHorizontalHeaderLabels(["Предмет", "Оценка", "Преподаватель"])

        if subjects_info:
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
        else:  # Если нет оценок, оставляем первую строку пустой
            self.table_widget.setItem(0, 0, QtWidgets.QTableWidgetItem(""))
            self.table_widget.setItem(0, 1, QtWidgets.QTableWidgetItem(""))
            self.table_widget.setItem(0, 2, QtWidgets.QTableWidgetItem(""))

        self.table_widget.setColumnWidth(0, 300)
        self.table_widget.setColumnWidth(1, 100)
        self.table_widget.setColumnWidth(2, 150)

        # Центрируем таблицу
        self.table_widget.horizontalHeader().setStretchLastSection(True)

        # Устанавливаем размер таблицы
        self.table_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # Запрет редактирования ячеек
        self.table_widget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

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

            query = "SELECT * FROM get_student_info_for_grades(%s)"

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
            group_name = results[0][0] if results[0][0] is not None else "Неизвестная группа"
            average_grade = results[0][1] if results[0][1] is not None else 0.0

            # Проверяем, содержатся ли оценки
            subjects_info = []
            for row in results:
                if row[2] is not None:
                    grade = row[3] if row[3] is not None else "Неизвестная"
                    teacher_full_name = f"{row[4] or ''} {row[5] or ''} {row[6] or ''}".strip()
                    subjects_info.append((row[2], grade, teacher_full_name))
            return group_name, average_grade, subjects_info
        else:
            return "Неизвестная группа", 0.0, []


class TeacherProfile(QtWidgets.QWidget):
    """
    Интерфейс преподавателя с правами вносить оценку студентам
    """

    def __init__(self, first_name, last_name, middle_name, teacher_id):
        super().__init__()
        self.teacher_id = teacher_id
        self.setWindowTitle("Профиль преподавателя")
        self.setGeometry(470, 200, 1000, 700)

        layout = QtWidgets.QVBoxLayout()

        layout.addStretch(1)

        self.name_label = QtWidgets.QLabel(f"Пользователь: {first_name} {last_name} {middle_name}")
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_label)

        layout.addStretch(1)

        self.grade_button = QtWidgets.QPushButton("Выставить оценку", self)
        self.grade_button.clicked.connect(lambda: self.open_grade_form(teacher_id))
        layout.addWidget(self.grade_button)

        layout.addStretch(1)

        self.name_label = QtWidgets.QLabel(f"Поиск студентов по фамилии")
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_label)

        self.search_input = QtWidgets.QLineEdit(self)
        self.search_input.setPlaceholderText("Введите фамилию студента")
        layout.addWidget(self.search_input)

        self.search_button = QtWidgets.QPushButton("Поиск", self)
        self.search_button.clicked.connect(self.search_student)
        layout.addWidget(self.search_button)

        # Таблица для отображения оценок
        self.table_widget = QtWidgets.QTableWidget()

        self.grades_info = self.get_grades_for_teacher(teacher_id)  # Получаем оценки для преподавателя
        self.insert_data_in_table(self.grades_info)  # Заполняем таблицу начальными данными

        layout.addStretch(1)
        self.save_button = QtWidgets.QPushButton("Обновить оценки", self)
        self.save_button.clicked.connect(self.save_grades)
        layout.addWidget(self.save_button)

        layout.addWidget(self.table_widget)

        self.name_label = QtWidgets.QLabel(
            "Для удаление записи выберите её, кликнув на её номер в первом столбце, и нажмите кнопку ниже")
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_label)

        # Установка режима выбора для таблицы
        self.table_widget.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        self.delete_button = QtWidgets.QPushButton("Удалить выбранные строки")
        self.delete_button.clicked.connect(self.delete_selected_rows)
        layout.addWidget(self.delete_button)

        layout.addStretch(6)

        self.setLayout(layout)

    def delete_selected_rows(self):
        selected_rows = sorted(
            set(index.row() for index in self.table_widget.selectedIndexes()))
        if selected_rows:
            student_full_name_col = 2
            for row in reversed(selected_rows):
                full_name = self.table_widget.item(row, student_full_name_col).text()
                first_name, last_name, middle_name = self.parse_full_name(full_name)
                subject_name = self.table_widget.item(row, 0).text()
                self.table_widget.removeRow(row)

                # Выполняем удаление из БД
                self.delete_grade_from_database(first_name, last_name, middle_name, self.teacher_id, subject_name)
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Выберите строки для удаления.")

    def insert_data_in_table(self, grades_info):
        """Заполняет таблицу данными оценок."""
        num_rows = len(grades_info)
        self.table_widget.setRowCount(num_rows)
        self.table_widget.setColumnCount(3)

        self.table_widget.setHorizontalHeaderLabels(["Предмет", "Оценка", "Студент"])

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

        # Растягиваем последний столбец
        header = self.table_widget.horizontalHeader()
        header.setStretchLastSection(True)

    def search_student(self):
        """Ищет студентов по фамилии и обновляет таблицу."""
        surname = self.search_input.text().strip()

        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        cursor = conn.cursor()
        query = "SELECT * FROM get_student_grades(%s)"

        cursor.execute(query, (surname,))
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        if results:
            self.insert_data_in_table(results)
        else:
            QtWidgets.QMessageBox.information(self, "Результат поиска", "Студент не найден.")

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

            query = "SELECT * FROM get_student_grades_by_teacher(%s)"

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

    def save_grades(self):
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST
            )
            cursor = conn.cursor()

            for row_index in range(self.table_widget.rowCount()):
                subject_name = self.table_widget.item(row_index, 0).text()
                new_grade = int(self.table_widget.item(row_index, 1).text())
                student_full_name = self.table_widget.item(row_index, 2).text()

                student_id_query = "SELECT * FROM get_student_id_by_full_name(%s)"
                cursor.execute(student_id_query, (student_full_name,))
                student_id_result = cursor.fetchone()

                if student_id_result is not None:
                    student_id = student_id_result[0]

                    update_query = "SELECT * FROM update_student_grade(%s, %s, %s)"
                    cursor.execute(update_query, (subject_name, student_id, new_grade))

            conn.commit()
            print("Оценки успешно обновлены.")

        except Exception as e:
            print("Ошибка при обновлении оценок:", e)

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def delete_grade_from_database(self, first_name, last_name, middle_name, teacher_id, subject_name):
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST
            )
            cursor = conn.cursor()
            # Получаем student_id на основе ФИО
            query_student_id = "SELECT get_student_id_by_name(%s, %s, %s)"
            cursor.execute(query_student_id, (first_name, last_name, middle_name))
            student_id = cursor.fetchone()

            query_subject_id = "SELECT get_subject_id_by_name(%s)"
            cursor.execute(query_subject_id, (subject_name,))
            subject_id = cursor.fetchone()

            if student_id:
                student_id = student_id[0]

                delete_query = " SELECT delete_grade(%s, %s, %s)"
                cursor.execute(delete_query, (student_id, teacher_id, subject_id))

            conn.commit()

        except Exception as e:
            print("Ошибка при удалении записи из базы данных:", e)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def parse_full_name(self, full_name):
        """Разделяет полное имя на отдельные компоненты."""
        parts = full_name.split()
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        return parts[0], parts[1], ""  # Если middle_name отсутствует


class GradeForm(QtWidgets.QWidget):
    """
    Форма, содержащая поля для внесения данных студента и оценки
    """

    def __init__(self, teacher_id):
        super().__init__()
        self.teacher_id = teacher_id  # ID преподавателя, который авторизован
        self.setWindowTitle("Выставление оценки")
        self.setGeometry(675, 300, 600, 450)
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

        if len(first_name) == 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Заполните имя студента!")
            return
        if len(last_name) == 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Заполните фамилию студента!")
            return
        if len(group_name) == 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Заполните группу студента!")
            return
        if len(subject_name) == 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Заполните название предмета!")
            return
        if len(grade) == 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Заполните поле с оценкой!")
            return
        try:
            grade = int(grade)
            if grade < 0 or grade > 10:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Оценка должна быть от 0 до 10!")
                return

        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Пожалуйста, введите корректное число для оценки!")
            return

        try:
            conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
            cursor = conn.cursor()

            # Получаем id студента
            cursor.execute("SELECT * FROM get_student_id(%s, %s, %s)", (first_name, last_name, group_name))
            student_id_result = cursor.fetchone()

            if student_id_result != (None,):
                student_id = student_id_result[0]

                # Проверяем наличие предмета
                cursor.execute("SELECT * FROM get_subject_id(%s, %s)", (subject_name, self.teacher_id))
                subject_id_result = cursor.fetchone()

                if subject_id_result and subject_id_result[0] is not None:
                    subject_id = subject_id_result[0]
                else:
                    cursor.execute("SELECT insert_subject(%s, %s)", (subject_name, self.teacher_id))
                    subject_id = cursor.fetchone()[0]
                    conn.commit()

                # Проверяем, существует ли оценка для данного студента и предмета
                cursor.execute("SELECT * FROM grades WHERE student_id = %s AND subject_id = %s",
                               (student_id, subject_id))
                existing_grade = cursor.fetchone()

                if existing_grade:
                    QtWidgets.QMessageBox.warning(self, "Ошибка",
                                                  'Оценка за предмет уже выставлена. Вы можете её изменить.')
                else:
                    # Вставляем новую оценку
                    cursor.execute("SELECT insert_grade(%s, %s, %s, %s)",
                                   (student_id, subject_id, self.teacher_id, grade))
                    conn.commit()
                    QtWidgets.QMessageBox.information(self, "Успех", "Оценка успешно выставлена!")

            else:
                QtWidgets.QMessageBox.warning(self, "Ошибка", "Студент не найден.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка", str(e))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
