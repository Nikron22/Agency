# check_postgres.py
import psycopg2

# Попробуем разные варианты подключения
configs = [
    {
        'name': 'Стандартный postgres',
        'dbname': 'agency1',
        'user': 'postgres',
        'password': 'Nikolai',
        'host': 'localhost',
        'port': '5432'
    },
    {
        'name': 'База kyrswork',
        'dbname': 'kyrswork',
        'user': 'postgres',
        'password': 'postgres',
        'host': 'localhost',
        'port': '5432'
    },
    {
        'name': 'Пользователь agent_user',
        'dbname': 'kyrswork',
        'user': 'agent_user',
        'password': 'agent123',
        'host': 'localhost',
        'port': '5432'
    }
]

for config in configs:
    print(f"\nПробуем подключиться: {config['name']}")
    try:
        conn = psycopg2.connect(**{k: v for k, v in config.items() if k != 'name'})
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Успешно! Версия: {version}")

        # Проверим базы данных
        cursor.execute("SELECT datname FROM pg_database;")
        databases = cursor.fetchall()
        print(f"Доступные базы данных: {', '.join([db[0] for db in databases])}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка: {e}")