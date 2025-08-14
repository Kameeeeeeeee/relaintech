from docx import Document
import os
import re
import sys
import traceback
import psycopg2
import uuid
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def clean_filename(name):
    """Удаляет запрещенные символы из имени файла"""
    if not name:
        return "unnamed"
        
    name = re.sub(r'\s+', ' ', name)
    forbidden_chars = r'[\\/*?:"<>|]'
    return re.sub(forbidden_chars, '', name).strip()

def parse_docx_to_postgres(docx_path, db_params):
    """Основная функция для обработки DOCX файла и записи в PostgreSQL"""
    try:
        # Подключение к базе данных
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        logger.info("Успешное подключение к базе данных PostgreSQL!")
    except Exception as e:
        logger.error(f"Ошибка подключения к PostgreSQL: {str(e)}")
        raise
    
    try:
        # Открываем документ
        doc = Document(docx_path)
        logger.info(f"Файл {docx_path} успешно открыт")
    except Exception as e:
        conn.close()
        logger.error(f"Ошибка открытия DOCX файла: {str(e)}")
        raise
    
    table_data = []
    
    # Обрабатываем все таблицы в документе
    logger.info(f"Начата обработка таблиц в документе")
    for table in doc.tables:
        current_table = []
        for row in table.rows:
            # Обработка ячеек с очисткой текста
            current_row = []
            for cell in row.cells:
                text = cell.text.strip()
                text = re.sub(r'\s+', ' ', text)  # Замена множественных пробелов
                text = text.replace(" ,", ",")     # Исправление запятых
                current_row.append(text)
                
            # Специфическая логика обработки строк
            if len(current_row) > 10:
                current_row = current_row[1:2] + current_row[3::2]
            else:
                current_row = current_row[1:]
                
            current_table.append(current_row)
        table_data.append(current_table)
    
    total_inserted = 0
    total_sections = 0
    
    # Обрабатываем каждую таблицу
    for table_idx, table in enumerate(table_data):
        headers_ind = []
        
        # Находим строки с заголовками разделов
        for row_idx in range(len(table)):
            if len(table[row_idx]) > 2:
                # Проверяем, что все ячейки после 2-й пустые
                if all(cell == '' for cell in table[row_idx][2:]):
                    headers_ind.append(row_idx)
        
        logger.info(f"Таблица {table_idx+1}: найдено {len(headers_ind)} разделов")
        
        # Обрабатываем каждый раздел таблицы
        for idx, header_idx in enumerate(headers_ind):
            if header_idx >= len(table) or len(table[header_idx]) < 2:
                continue
                
            # Формируем имя раздела (для логирования)
            clean_name = clean_filename(table[header_idx][1])
            if not clean_name:
                clean_name = f"Table_{table_idx+1}_Section_{idx+1}"
            
            # Определяем границы раздела
            start_row = header_idx + 1
            end_row = headers_ind[idx + 1] if idx + 1 < len(headers_ind) else len(table)
            
            if start_row >= end_row:
                continue
                
            rows = table[start_row:end_row]
            total_sections += 1
            
            # Вставляем данные раздела в базу данных
            try:
                inserted_count = 0
                for row in rows:
                    # Дополняем строку до нужного количества столбцов
                    padded_row = (row + [''] * 9)[:9]
                    
                    # Пропускаем пустые строки
                    if not any(padded_row[1:8]):  # Проверка основных полей
                        continue
                    
                    # Подготовка данных
                    equipment_id = str(uuid.uuid4())
                    
                    # Преобразование числовых полей
                    try:
                        quantity = int(padded_row[6]) if padded_row[6].strip() else None
                    except:
                        quantity = None
                        
                    try:
                        unit_mass = float(padded_row[7]) if padded_row[7].strip() else None
                    except:
                        unit_mass = None
                    
                    # Формируем запрос
                    insert_query = """
                    INSERT INTO "Equipment" (
                        "ID_equipment",
                        "Equipment_identification",
                        "Name_equipment",
                        "Type_equipment",
                        "Code_product",
                        "Supplier",
                        "Units",
                        "Quantity",
                        "Unit_mass",
                        "Note"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    # Параметры для запроса
                    data = (
                        equipment_id,           # ID_equipment
                        padded_row[0] or None,  # Equipment_identification
                        padded_row[1] or None,  # Name_equipment
                        padded_row[2] or None,  # Type_equipment
                        padded_row[3] or None,  # Code_product
                        padded_row[4] or None,  # Supplier
                        padded_row[5] or None,  # Units
                        quantity,               # Quantity
                        unit_mass,              # Unit_mass
                        padded_row[8] or None   # Note
                    )
                    
                    # Выполняем запрос
                    cursor.execute(insert_query, data)
                    inserted_count += 1
                
                # Фиксируем изменения для раздела
                conn.commit()
                total_inserted += inserted_count
                logger.info(f"Раздел '{clean_name}': добавлено {inserted_count} записей")
                
            except Exception as e:
                logger.error(f"Ошибка при вставке раздела '{clean_name}': {str(e)}")
                conn.rollback()
                traceback.print_exc()
                
    # Закрываем соединение с базой
    cursor.close()
    conn.close()
    logger.info(f"Соединение с PostgreSQL закрыто. Всего обработано: {total_sections} разделов, {total_inserted} записей")
    return total_inserted

# Точка входа для вызова через командную строку
if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: python spec_parser.py <docx_path> <db_host> <db_port> <db_name> <db_user> <db_password>")
        sys.exit(1)
        
    docx_file_path = sys.argv[1]
    
    # Параметры подключения к БД
    db_params = {
        "host": sys.argv[2],
        "port": sys.argv[3],
        "database": sys.argv[4],
        "user": sys.argv[5],
        "password": sys.argv[6]
    }
    
    logger.info(f"Начата обработка файла: {docx_file_path}")
    logger.info(f"Параметры БД: {db_params['user']}@{db_params['host']}:{db_params['port']}/{db_params['database']}")
    
    try:
        record_count = parse_docx_to_postgres(docx_file_path, db_params)
        print(f"Обработка успешно завершена! Добавлено записей: {record_count}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        traceback.print_exc()
        sys.exit(2)