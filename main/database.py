import psycopg2
import os
from main.ui.login import DB_USER, DB_PASSWORD
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv('DB_NAME')
ROOT_DB_USER = os.getenv('DB_USER')
ROOT_DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')


def create_database(db_name, sql_file="create_database.sql"):
    """Создает базу данных и настраивает пользователя с ограниченными правами."""

    # Подключение от имени root-пользователя
    root_conn = psycopg2.connect(dbname="postgres", user=ROOT_DB_USER, password=ROOT_DB_PASSWORD, host=DB_HOST)
    root_conn.autocommit = True
    root_cursor = root_conn.cursor()

    root_cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    exists = root_cursor.fetchone()

    if not exists:
        root_cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"База данных {db_name} создана успешно.")

    root_conn.close()

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    root_conn = psycopg2.connect(dbname=db_name, user=ROOT_DB_USER, password=ROOT_DB_PASSWORD, host=DB_HOST)
    root_cursor = root_conn.cursor()

    try:
        root_cursor.execute(sql_script)
        root_conn.commit()
        print(f"SQL-скрипт {sql_file} выполнен успешно.")
    except Exception as e:
        print(f"Ошибка при выполнении SQL-скрипта: {e}")
    finally:
        root_cursor.close()
        root_conn.close()

    # Подключение от имени нового пользователя
    app_conn = psycopg2.connect(dbname=db_name, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
    app_cursor = app_conn.cursor()

    try:
        app_cursor.execute("SELECT current_user;")
        print(f"Подключение к базе данных выполнено от имени пользователя: {app_cursor.fetchone()[0]}")
    except Exception as e:
        print(f"Ошибка при подключении новым пользователем: {e}")
    finally:
        app_cursor.close()
        app_conn.close()


if __name__ == "__main__":
    create_database(DB_NAME)
