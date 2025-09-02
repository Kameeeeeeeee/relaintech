import xml.etree.ElementTree as ET
import zipfile
import os
import shutil

def find_id(docx_path, output_folder='TestDocToXml'):
    """
    Обрабатывает DOCX файл для поиска информации в футерах.
    Возвращает найденное слово или None, если ничего не найдено.
    """
    # Проверяем существование файла перед обработкой
    if not os.path.exists(docx_path):
        print(f"Файл не найден: {docx_path}")
        return None

    # Создаём уникальную подпапку для каждого DOCX-файла
    file_id = os.path.splitext(os.path.basename(docx_path))[0]
    extract_path = os.path.join(output_folder, file_id)
    os.makedirs(extract_path, exist_ok=True)

    try:
        # Извлекаем содержимое DOCX
        with zipfile.ZipFile(docx_path, 'r') as docx_zip:
            docx_zip.extractall(extract_path)
    except Exception as e:
        print(f"Ошибка при обработке файла {docx_path}: {e}")
        shutil.rmtree(extract_path, ignore_errors=True)
        return None

    found_word = None
    
    # Проверяем футеры по порядку
    for footer_num in range(1, 4):  # Проверяем footer1.xml, footer2.xml, footer3.xml
        xml_path = os.path.join(extract_path, 'word', f'footer{footer_num}.xml')
        
        if not os.path.exists(xml_path):
            continue  # Если файла нет, переходим к следующему футеру
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            elements = root.findall('.//w:t', namespaces)
            
            # Ищем "ДСиР" в элементах футера
            for i, elem in enumerate(elements):
                text = elem.text if elem.text else ''
                if 'ДСиР' in text:
                    word = text
                    
                    # Выводим следующие элементы после найденного
                    for j in range(i+1, len(elements)):
                        next_text = elements[j].text if elements[j].text else ''
                        if next_text.strip():  # Пропускаем пустые строки
                            word += next_text
                            # Проверяем, содержит ли слово нужные ключевые слова
                            if ("ВР" in word and "СВР" not in word) or ("СО" in word) or ("КЖ" in word):
                                found_word = word
                                #print(f"======================================")
                                #print(f"Найдено в {os.path.basename(docx_path)}, footer{footer_num}.xml:")
                                #print(found_word)
                                #print(f"======================================")
                                break
                    
                    if found_word:
                        break  # Прерываем цикл проверки элементов
            
            if found_word:
                break  # Прерываем цикл проверки футеров
                
        except ET.ParseError:
            print(f"Ошибка парсинга {xml_path}")
            continue
    
    if not found_word:
        print(f"ДСиР не найден в файле \"{os.path.basename(docx_path)}\"")
    
    # Очищаем временные файлы
    shutil.rmtree(extract_path, ignore_errors=True)
    return found_word

#print(find_id('15_ДСиР-2022-864-Р-8.1.2-СО.docx', output_folder='TestDocToXml'))