import psycopg2


def create_database(db_name):
    conn = psycopg2.connect(dbname='postgres', user='postgres', password='4339', host='localhost')
    conn.autocommit = True  # Включаем автокоммит для создания базы данных
    cursor = conn.cursor()

    # Проверяем, существует ли база данных
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute(f"CREATE DATABASE {db_name}")
        print("База данных создана.")

        # Закрываем соединение с текущей базой данных
        cursor.close()
        conn.close()

        # Подключаемся к новой базе данных
        conn = psycopg2.connect(dbname=db_name, user='postgres', password='4339', host='localhost')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                password VARCHAR(100) NOT NULL,
                position VARCHAR(50)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups_name (
            id SERIAL PRIMARY KEY,
            group_name VARCHAR(50)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                middle_name VARCHAR(50) 
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                middle_name VARCHAR(50),
                group_id INTEGER REFERENCES groups_name(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50),
            teacher_id INTEGER REFERENCES teachers(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id),
                subject_id INTEGER REFERENCES subjects(id),
                teacher_id INTEGER REFERENCES teachers(id),
                grade INTEGER CHECK (grade >= 0 AND grade <= 10)
            )
        ''')

        conn.commit()
        conn.close()
    else:
        print("База данных уже существует.")