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
                group_id INTEGER REFERENCES groups_name(id),
                average_grade NUMERIC
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

        cursor.execute('''
            CREATE OR REPLACE FUNCTION get_user_info(
                p_username VARCHAR
            )
            RETURNS TABLE(id INT, "position" VARCHAR, password VARCHAR) AS $$
            BEGIN
                RETURN QUERY
                SELECT id, u."position", password
                FROM users
                WHERE username = p_username;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION get_student_info(
                p_user_id INT
            )
            RETURNS TABLE(id INT, first_name VARCHAR, last_name VARCHAR, middle_name VARCHAR, student_id INT) AS $$
            BEGIN
                RETURN QUERY
                SELECT u.id, s.first_name, s.last_name, s.middle_name, s.id
                FROM users u
                JOIN students s ON u.id = s.user_id
                WHERE u.id = p_user_id;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION get_teacher_info(
                p_user_id INT
            )
            RETURNS TABLE(id INT, first_name VARCHAR, last_name VARCHAR, middle_name VARCHAR, teacher_id INT) AS $$
            BEGIN
                RETURN QUERY
                SELECT u.id, t.first_name, t.last_name, t.middle_name, t.id 
                FROM users u
                JOIN teachers t ON u.id = t.user_id
                WHERE u.id = p_user_id;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION get_student_info_for_grades(
                p_student_id INT
            )
            RETURNS TABLE(
                group_name VARCHAR,
                average_grade NUMERIC,
                subject_name VARCHAR,
                grade NUMERIC,
                first_name VARCHAR,
                last_name VARCHAR,
                middle_name VARCHAR
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT g.group_name, 
                       s.average_grade, 
                       sub.name AS subject_name, 
                       gr.grade, 
                       t.first_name, 
                       t.last_name, 
                       t.middle_name
                FROM students s
                JOIN groups_name g ON s.group_id = g.id
                LEFT JOIN grades gr ON s.id = gr.student_id
                LEFT JOIN subjects sub ON gr.subject_id = sub.id
                LEFT JOIN teachers t ON gr.teacher_id = t.id
                WHERE s.id = p_student_id;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION get_student_grades_by_teacher(teacher_id INT)
            RETURNS TABLE(subject_name VARCHAR(50), grade INT, first_name VARCHAR(50), last_name VARCHAR(50), middle_name VARCHAR(50)) AS $$
            BEGIN
                RETURN QUERY
                SELECT sub.name::VARCHAR(50) AS subject_name, gr.grade, 
                       s.first_name, s.last_name, s.middle_name
                FROM grades gr
                JOIN subjects sub ON gr.subject_id = sub.id
                JOIN students s ON gr.student_id = s.id
                WHERE gr.teacher_id = $1;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION get_student_id_by_full_name(full_name TEXT)
            RETURNS INT AS $$
            DECLARE
                student_id INT;
            BEGIN
                SELECT id INTO student_id
                FROM students
                WHERE CONCAT(first_name, ' ', last_name, ' ', middle_name) = full_name;
            
                RETURN student_id;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION update_student_grade(
            subject_name TEXT,
            student_id_param INT,
            new_grade INT
        ) RETURNS VOID AS $$
        BEGIN
            UPDATE grades
            SET grade = new_grade
            WHERE subject_id = (SELECT id FROM subjects WHERE name = subject_name)
              AND student_id = student_id_param;
        END;
        $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            -- Создание функции для обновления средней оценки
            CREATE OR REPLACE FUNCTION update_average_grade() 
            RETURNS TRIGGER AS $$
            BEGIN
                UPDATE students 
                SET average_grade = (
                    SELECT AVG(grade) 
                    FROM grades 
                    WHERE student_id = NEW.student_id
                )
                WHERE id = NEW.student_id;

                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            -- Создание триггера на добавление записей в grades
            CREATE TRIGGER trigger_update_average_grade
            AFTER INSERT ON grades
            FOR EACH ROW
            EXECUTE FUNCTION update_average_grade();
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION get_student_id(
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                group_name VARCHAR(50)
            ) RETURNS INT AS $$
            DECLARE
                student_id INT;
            BEGIN
                SELECT id INTO student_id
                FROM students
                WHERE first_name = first_name
                  AND last_name = last_name
                  AND group_id = (SELECT id FROM groups_name WHERE group_name = group_name);
            
                RETURN student_id;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION insert_subject(
                p_name TEXT,
                p_teacher_id INT
            ) RETURNS INT AS $$
            DECLARE
                new_subject_id INT;
            BEGIN
                INSERT INTO subjects (name, teacher_id)
                VALUES (p_name, p_teacher_id)
                RETURNING id INTO new_subject_id;
            
                RETURN new_subject_id;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION insert_grade(
                p_student_id INT,
                p_subject_id INT,
                p_teacher_id INT,
                p_grade INT
            ) RETURNS INT AS $$
            DECLARE
                new_grade_id INT;
            BEGIN
                INSERT INTO grades (student_id, subject_id, teacher_id, grade)
                VALUES (p_student_id, p_subject_id, p_teacher_id, p_grade)
                RETURNING id INTO new_grade_id;
            
                RETURN new_grade_id;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION get_subject_id(
                p_subject_name TEXT,
                p_teacher_id INT
            ) RETURNS INT AS $$
            DECLARE
                subject_id INT;
            BEGIN
                SELECT id INTO subject_id
                FROM subjects
                WHERE name = p_subject_name AND teacher_id = p_teacher_id;
            
                RETURN subject_id;
            END;
            $$ LANGUAGE plpgsql;
        ''')

        cursor.execute('''
            CREATE OR REPLACE FUNCTION get_student_grades(last_name_pattern TEXT)
            RETURNS TABLE(subject_name VARCHAR(50), grade INT, student_full_name TEXT) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    sub.name AS subject_name,
                    g.grade,
                    s.first_name || ' ' || s.last_name || ' ' || s.middle_name AS student_full_name
                FROM 
                    grades g
                JOIN 
                    students s ON g.student_id = s.id
                JOIN 
                    subjects sub ON g.subject_id = sub.id
                WHERE 
                    LOWER(s.last_name) LIKE LOWER('%' || last_name_pattern || '%');
            END;
            $$ LANGUAGE plpgsql;
        ''')

        conn.commit()
        conn.close()
    else:
        print("База данных уже существует.")
