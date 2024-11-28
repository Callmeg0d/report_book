import psycopg2
from ui.login import DB_HOST, DB_USER, DB_PASSWORD


def create_database(db_name):
    #Подключаемся к стандартной БД postgres на случай, если создаём новую БД, тк надо сначала подключиться к какой-то
    conn = psycopg2.connect(dbname='postgres', user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
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
        conn = psycopg2.connect(dbname=db_name, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)
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

        cursor.execute('''
                    CREATE EXTENSION IF NOT EXISTS pgcrypto;
                ''')

        cursor.execute('''
                    CREATE OR REPLACE FUNCTION authenticate_user(
                        p_username VARCHAR,
                        p_password VARCHAR
                    )
                    RETURNS BOOLEAN AS $$
                    DECLARE
                        user_count INT;
                    BEGIN
                        SELECT COUNT(*) INTO user_count 
                        FROM users 
                        WHERE username = p_username AND password = crypt(p_password, password);

                        RETURN user_count > 0;
                    END;
                    $$ LANGUAGE plpgsql;
                ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION register_user(
                p_username VARCHAR,
                p_password VARCHAR,
                p_first_name VARCHAR,
                p_last_name VARCHAR,
                p_middle_name VARCHAR,
                p_position VARCHAR,
                p_group VARCHAR
            )
            RETURNS BOOLEAN AS $$
            DECLARE
                user_id INT;
                group_id INT;
            BEGIN
                -- Проверяем, существует ли пользователь
                IF check_user_exists(p_username) THEN
                    RETURN FALSE;
                END IF;

                INSERT INTO users (username, password) VALUES (p_username, crypt(p_password, gen_salt('bf')))
                RETURNING id INTO user_id;

                IF p_position = 'Студент' THEN
                    -- Проверяем, существует ли группа
                    SELECT id INTO group_id FROM groups_name WHERE group_name = p_group;

                    IF group_id IS NULL THEN
                        INSERT INTO groups_name (group_name) VALUES (p_group)
                        RETURNING id INTO group_id;  -- Получаем ID новой группы
                    END IF;

                    -- Вставка студента с использованием ID группы
                    INSERT INTO students (user_id, first_name, last_name, middle_name, group_id)
                    VALUES (user_id, p_first_name, p_last_name, p_middle_name, group_id);

                    UPDATE users SET position = 'Студент' WHERE id = user_id;

                ELSIF p_position = 'Преподаватель' THEN
                    INSERT INTO teachers (user_id, first_name, last_name, middle_name)
                    VALUES (user_id, p_first_name, p_last_name, p_middle_name);

                    UPDATE users SET position = 'Преподаватель' WHERE id = user_id;
                END IF;

                RETURN TRUE;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION check_user_exists(
                p_username VARCHAR
            )
            RETURNS BOOLEAN AS $$
            DECLARE
                user_count INT;
            BEGIN
                SELECT COUNT(*) INTO user_count 
                FROM users 
                WHERE username = p_username;

                RETURN user_count > 0;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        conn.commit()
        conn.close()
    else:
        print("База данных уже существует.")