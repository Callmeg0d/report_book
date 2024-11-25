from PyQt5 import QtWidgets
from psycopg2 import sql
import psycopg2

import bcrypt
from dotenv import load_dotenv
import os


load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')


def connect_db():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )
    return conn


class RegistrationPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Register')
        self.setGeometry(600, 400, 500, 400)

        self.layout = QtWidgets.QVBoxLayout()

        self.username_input = QtWidgets.QLineEdit(self)
        self.username_input.setMinimumSize(700, 40)
        self.username_input.setMaximumSize(2100, 40)
        self.username_input.setPlaceholderText('Логин')
        self.layout.addWidget(self.username_input)

        self.password_input = QtWidgets.QLineEdit(self)
        self.password_input.setMinimumSize(700, 40)
        self.password_input.setMaximumSize(2100, 40)
        self.password_input.setPlaceholderText('Пароль')
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.layout.addWidget(self.password_input)

        self.last_name_input = QtWidgets.QLineEdit(self)
        self.last_name_input.setMinimumSize(700, 40)
        self.last_name_input.setMaximumSize(2100, 40)
        self.last_name_input.setPlaceholderText('Фамилия')
        self.layout.addWidget(self.last_name_input)

        self.first_name_input = QtWidgets.QLineEdit(self)
        self.first_name_input.setMinimumSize(700, 40)
        self.first_name_input.setMaximumSize(2100, 40)
        self.first_name_input.setPlaceholderText('Имя')
        self.layout.addWidget(self.first_name_input)

        self.middle_name_input = QtWidgets.QLineEdit(self)
        self.middle_name_input.setMinimumSize(700, 40)
        self.middle_name_input.setMaximumSize(2100, 40)
        self.middle_name_input.setPlaceholderText('Отчество')
        self.layout.addWidget(self.middle_name_input)

        # Добавляем выпадающий список для выбора должности
        self.position_combo = QtWidgets.QComboBox(self)
        self.position_combo.addItems([" ", "Студент", "Преподаватель"])
        self.position_combo.currentIndexChanged.connect(self.update_group_field)
        self.layout.addWidget(self.position_combo)

        self.group_input = QtWidgets.QLineEdit(self)
        self.group_input.setMinimumSize(700, 40)
        self.group_input.setMaximumSize(2100, 40)
        self.group_input.setPlaceholderText('Группа')
        self.group_input.setVisible(False)
        self.layout.addWidget(self.group_input)

        self.register_button = QtWidgets.QPushButton('Регистрация', self)
        self.register_button.clicked.connect(self.handle_register)
        self.layout.addWidget(self.register_button)

        self.setLayout(self.layout)

    def update_group_field(self):
        if self.position_combo.currentText() == "Студент":
            self.group_input.setVisible(True)
        else:
            self.group_input.setVisible(False)

    def handle_register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        last_name = self.last_name_input.text()
        first_name = self.first_name_input.text()
        middle_name = self.middle_name_input.text()
        position = self.position_combo.currentText()
        group = self.group_input.text() if position == "Студент" else None

        if len(password) < 4:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Пароль должен содержать не менее 4 символов!")
            return

        if position == " ":
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Пожалуйста, укажите должность!")
            return

        if position == "Студент" and not group:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Пожалуйста, укажите группу!")
            return

        if self.register_user(username, password, first_name, last_name, middle_name, position, group):
            QtWidgets.QMessageBox.information(self, "Успех", "Регистрация прошла успешно!")
            self.close()  # Закрыть окно после успешной регистрации
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Регистрация не удалась или пользователь уже существует!")

    def register_user(self, username, password, first_name, last_name, middle_name, position, group):
        conn = connect_db()
        cursor = conn.cursor()

        # Проверяем, существует ли пользователь
        query = sql.SQL("SELECT * FROM users WHERE username = %s")
        cursor.execute(query, (username,))

        if cursor.fetchone() is not None:
            cursor.close()
            conn.close()
            return False  # Пользователь уже существует

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Регистрация нового пользователя
        insert_user_query = sql.SQL("INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id")
        cursor.execute(insert_user_query, (username, hashed_password))

        user_id = cursor.fetchone()[0]  # Получаем ID нового пользователя

        if position == "Студент":
            # Проверяем существует ли группа в таблице groups_name
            cursor.execute(sql.SQL("SELECT id FROM groups_name WHERE group_name = %s"), (group,))
            group_row = cursor.fetchone()

            if group_row is None:
                # Если группа не существует, добавляем её в таблицу groups_name
                cursor.execute(sql.SQL("INSERT INTO groups_name (group_name) VALUES (%s) RETURNING id"), (group,))
                group_id = cursor.fetchone()[0]  # Получаем ID новой группы
            else:
                group_id = group_row[0]  # Получаем ID существующей группы

            insert_student_query = sql.SQL(
                "INSERT INTO students (user_id, first_name, last_name, middle_name, group_id) VALUES (%s, %s, %s, %s, %s)")
            cursor.execute(insert_student_query, (user_id, first_name, last_name, middle_name, group_id))

            update_user_query = sql.SQL("UPDATE users SET position = %s WHERE id = %s")
            cursor.execute(update_user_query, ("Студент", user_id))

        elif position == "Преподаватель":
            insert_teacher_query = sql.SQL(
                "INSERT INTO teachers (user_id, first_name, last_name, middle_name) VALUES (%s, %s, %s, %s)")
            cursor.execute(insert_teacher_query, (user_id, first_name, last_name, middle_name))

            update_user_query = sql.SQL("UPDATE users SET position = %s WHERE id = %s")
            cursor.execute(update_user_query, ("Преподаватель", user_id))

        conn.commit()

        cursor.close()
        conn.close()

        return True


class LoginPage(QtWidgets.QWidget):
    """
    Вход в существующий профиль или переход на страницу регистрации.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Login')
        self.setGeometry(600, 400, 500, 350)

        self.layout = QtWidgets.QVBoxLayout()

        self.username_input = QtWidgets.QLineEdit(self)
        self.username_input.setMinimumSize(700, 40)
        self.username_input.setMaximumSize(2100, 40)
        self.username_input.setPlaceholderText('Логин')
        self.layout.addWidget(self.username_input)

        self.password_input = QtWidgets.QLineEdit(self)
        self.password_input.setMinimumSize(700, 40)
        self.password_input.setMaximumSize(2100, 40)
        self.password_input.setPlaceholderText('Пароль')
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.layout.addWidget(self.password_input)

        self.login_button = QtWidgets.QPushButton('Войти', self)
        self.login_button.clicked.connect(self.handle_login)
        self.layout.addWidget(self.login_button)

        self.register_button = QtWidgets.QPushButton('Регистрация', self)
        self.register_button.clicked.connect(self.open_registration_page)
        self.layout.addWidget(self.register_button)

        self.setLayout(self.layout)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if self.authenticate_user(username, password):
            QtWidgets.QMessageBox.information(self, "Успех", "Вход выполнен успешно!")
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Ошибка входа!")

    def open_registration_page(self):
        self.registration_page = RegistrationPage()
        self.registration_page.show()

    def authenticate_user(self, username, password):
        conn = connect_db()
        cursor = conn.cursor()

        query = sql.SQL("SELECT * FROM users WHERE username = %s AND password = %s")
        cursor.execute(query, (username, password))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        return user is not None
