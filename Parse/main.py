from docx import Document
import os
import csv
import re

def clean_filename(name):
    """Удаляет запрещенные символы из имени файла"""
    name = re.sub(r'\s+', ' ', name)
    forbidden_chars = r'[\\/*?:"<>|]'
    return re.sub(forbidden_chars, '', name).strip()

def parse_docx_table(docx_path):
    doc = Document(docx_path)
    table_data = []
    
    for table in doc.tables:
        current_table = []
        for row in table.rows:
            current_row = [cell.text.strip().replace("  ", " ").replace("  ", " ").replace(" ,", ",") for cell in row.cells]
            if len(current_row) > 10:
                current_row = current_row[1:2] + current_row[3::2]
            else:
                current_row = current_row[1:]
            print(current_row)
            current_table.append(current_row)
        table_data.append(current_table)
    
    return table_data

docx_file_path = '27_ДСиР-2022-864-Р-8.1.1_СО.docx'
parsed_tables = parse_docx_table(docx_file_path)

output_dir = 'csvf'

os.makedirs(output_dir, exist_ok=True)

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

for table in parsed_tables:
    headers_ind = []
    for row in range(len(table)):
        if table[row][2:] == ['', '', '', '', '', '', '']:
            headers_ind.append(row)
    print(headers_ind)
    for idx, header_idx in enumerate(headers_ind):
        clean_name = clean_filename(table[header_idx][1])
        
        start_row = header_idx + 1
        end_row = headers_ind[idx + 1] if idx + 1 < len(headers_ind) else len(table)
        if (start_row==end_row): continue
        rows = table[start_row:end_row]
        
        file_path = os.path.join(output_dir, f"{clean_name}.csv")
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(headers_csv)
            
            for row in rows:
                padded_row = (row + [''] * len(headers_csv))[:len(headers_csv)]
                writer.writerow(padded_row)