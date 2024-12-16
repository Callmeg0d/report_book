from PyQt5 import QtWidgets
import psycopg2
from main.ui.profile import StudentProfile, TeacherProfile
from dotenv import load_dotenv
import os
import bcrypt

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('APP_DB_USER')
DB_PASSWORD = os.getenv('APP_DB_PASSWORD')
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
            self.close()
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Регистрация не удалась или пользователь уже существует!")

    def register_user(self, username, password, first_name, last_name, middle_name, position, group):
        conn = connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT register_user(%s, %s, %s, %s, %s, %s, %s)",
                (username, password, first_name, last_name, middle_name, position, group)
            )

            result = cursor.fetchone()[0]
            conn.commit()
            return result

        except Exception as e:
            print(f"Ошибка: {e}")
            return False

        finally:
            cursor.close()
            conn.close()


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

        user_info = self.authenticate_user(username, password)

        if user_info:
            first_name = user_info['first_name']
            last_name = user_info['last_name']
            middle_name = user_info['middle_name']
            position = user_info['position']
            if position == "Преподаватель":
                inner_id = user_info['teacher_id']
                self.open_teacher_profile(first_name, last_name, middle_name, inner_id)
            else:
                student_id = user_info['student_id']
                self.open_student_profile(first_name, last_name, middle_name, student_id)
        else:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Ошибка входа!")

    def open_student_profile(self, first_name, last_name, middle_name, student_id):
        self.profile_window = StudentProfile(first_name, last_name, middle_name, student_id)
        self.profile_window.show()
        self.close()

    def open_teacher_profile(self, first_name, last_name, middle_name, inner_id):
        self.profile_window = TeacherProfile(first_name, last_name, middle_name, inner_id)
        self.profile_window.show()
        self.close()

    def open_registration_page(self):
        self.registration_page = RegistrationPage()
        self.registration_page.show()

    def authenticate_user(self, username, password):
        conn = None
        cursor = None
        try:
            conn = connect_db()
            cursor = conn.cursor()

            user_query = "SELECT * FROM get_user_info(%s)"
            cursor.execute(user_query, (username,))
            user_info = cursor.fetchone()

            if user_info:
                user_id, position, stored_password = user_info
                if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    if position == 'Студент':
                        query = "SELECT * FROM get_student_info(%s)"
                        cursor.execute(query, (user_id,))
                        student_info = cursor.fetchone()
                        if student_info:
                            return {
                                'user_id': user_id,
                                'first_name': student_info[1],
                                'last_name': student_info[2],
                                'middle_name': student_info[3],
                                'position': position,
                                'student_id': student_info[4]
                            }
                        else:
                            print("Информация о студенте не найдена.")
                            return None

                    elif position == 'Преподаватель':
                        query = "SELECT * FROM get_teacher_info(%s)"
                        cursor.execute(query, (user_id,))
                        teacher_info = cursor.fetchone()
                        if teacher_info:
                            return {
                                'user_id': user_id,
                                'first_name': teacher_info[1],
                                'last_name': teacher_info[2],
                                'middle_name': teacher_info[3],
                                'position': position,
                                'teacher_id': teacher_info[4]
                            }
                        else:
                            print("Информация о преподавателе не найдена.")
                            return None
                else:
                    print("Неверный пароль!")
                    return None
            else:
                print("Пользователь не найден!")
                return None

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
