import psycopg2
from psycopg2 import sql

# Параметры подключения
db_params = {
    "host": "localhost",
    "database": "cable_db",  # имя вашей БД
    "user": "postgres",
    "password": "test1",
    "port": "5432"  # стандартный порт PostgreSQL
}

try:
    # Установка соединения
    connection = psycopg2.connect(**db_params)
    print("Успешное подключение к базе данных!")
    
    # Создание курсора
    cursor = connection.cursor()
    
    # Пример выполнения запроса (выборка данных)
    cursor.execute('SELECT * FROM "Equipmet" LIMIT 5')
    
    # Получение результатов
    records = cursor.fetchall()
    print("\nПервые 5 записей из таблицы Cable:")
    for row in records:
        print(row)
        
except (Exception, psycopg2.Error) as error:
    print("Ошибка при работе с PostgreSQL:", error)
    
finally:
    # Закрытие соединения
    if connection:
        cursor.close()
        connection.close()
        print("Соединение с PostgreSQL закрыто")