from docx import Document
import os
import csv
import re
import sys
import traceback

def clean_filename(name):
    """Удаляет запрещенные символы из имени файла"""
    if not name:
        return "unnamed"
        
    name = re.sub(r'\s+', ' ', name)
    forbidden_chars = r'[\\/*?:"<>|]'
    return re.sub(forbidden_chars, '', name).strip()

def parse_docx_table(docx_path, output_dir='csvf'):
    """Основная функция для обработки DOCX файла"""
    try:
        # Открываем документ
        doc = Document(docx_path)
    except Exception as e:
        raise Exception(f"Ошибка открытия DOCX файла: {str(e)}")
    
    table_data = []
    
    # Обрабатываем все таблицы в документе
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
    
    # Создаем директорию для результатов
    os.makedirs(output_dir, exist_ok=True)

    # Заголовки для CSV файлов
    headers_csv = [
        'Номер',
        'Наименование и техническая характеристика',
        'Тип, марка, обозначение документа, опросного листа',
        'Код продукции',
        'Поставщик',
        'Ед. измере-ния',
        'Кол.',
        'Масса 1 ед., кг',
        'Примечание'
    ]

    # Обрабатываем каждую таблицу
    for table_idx, table in enumerate(table_data):
        headers_ind = []
        
        # Находим строки с заголовками разделов
        for row_idx in range(len(table)):
            if len(table[row_idx]) > 2:
                # Проверяем, что все ячейки после 2-й пустые
                if all(cell == '' for cell in table[row_idx][2:]):
                    headers_ind.append(row_idx)
        
        # Создаем CSV файлы для каждого раздела
        for idx, header_idx in enumerate(headers_ind):
            if header_idx >= len(table) or len(table[header_idx]) < 2:
                continue
                
            # Формируем имя файла
            clean_name = clean_filename(table[header_idx][1])
            if not clean_name:
                clean_name = f"Table_{table_idx+1}_Section_{idx+1}"
            
            # Определяем границы раздела
            start_row = header_idx + 1
            end_row = headers_ind[idx + 1] if idx + 1 < len(headers_ind) else len(table)
            
            if start_row >= end_row:
                continue
                
            rows = table[start_row:end_row]
            
            # Создаем CSV файл
            file_path = os.path.join(output_dir, f"{clean_name}.csv")
            try:
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';')
                    writer.writerow(headers_csv)
                    
                    for row in rows:
                        # Дополняем строку до нужного количества столбцов
                        padded_row = (row + [''] * len(headers_csv))[:len(headers_csv)]
                        writer.writerow(padded_row)
            except Exception as e:
                print(f"Ошибка записи CSV: {str(e)}")

# Точка входа для вызова через Process
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python spec_parser.py <docx_path> [output_dir]")
        sys.exit(1)
        
    docx_file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'csvf'
    
    try:
        parse_docx_table(docx_file_path, output_dir)
        print("Обработка успешно завершена!")
    except Exception as e:
        print(f"Critical error: {str(e)}")
        traceback.print_exc()
        sys.exit(2)