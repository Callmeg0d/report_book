import sys
from PyQt5 import QtWidgets
from ui.login import LoginPage
from database import create_database
from database import DB_NAME


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    create_database(DB_NAME)
    window = LoginPage()
    window.show()
    sys.exit(app.exec_())