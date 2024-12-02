from PyQt5 import QtWidgets, QtCore


class StudentProfile(QtWidgets.QWidget):
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
    def __init__(self, first_name, last_name, middle_name):
        super().__init__()
        self.setWindowTitle("Профиль преподавателя")
        self.setGeometry(600, 400, 500, 350)

        layout = QtWidgets.QVBoxLayout()

        layout.addStretch(1)

        self.name_label = QtWidgets.QLabel(f"Пользователь: {first_name} {last_name} {middle_name}")
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.name_label)
        layout.addStretch(7)

        self.setLayout(layout)
