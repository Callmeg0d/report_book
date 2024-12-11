import psycopg2
from main.ui.login import DB_HOST, DB_USER, DB_PASSWORD

def create_database(db_name, sql_file="create_database.sql"):
    """Создает базу данных, если она не существует, выполняя скрипт SQL."""

    # Подключение к существующей базе данных
    conn = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
    conn.autocommit = True
    cursor = conn.cursor()

    # Проверка существования базы данных
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f"База данных {db_name} создана успешно.")
        conn.close()

        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        new_conn = psycopg2.connect(dbname=db_name, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
        new_cursor = new_conn.cursor()

        try:
            new_cursor.execute(sql_script)
            new_conn.commit()
            print(f"SQL-скрипт {sql_file} выполнен успешно.")
        except Exception as e:
            print(f"Ошибка при выполнении SQL-скрипта: {e}")
        finally:
            new_cursor.close()
            new_conn.close()
