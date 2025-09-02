import os
import sys
import subprocess
from id_xml_parser import find_id

def find_files_in_directory(directory):
    """Поиск файлов по типам СО, КЖ, ВР в указанной директории"""
    found_files = {}
    all_docx_files = []
    
    # Собираем все docx файлы, исключая временные
    for item in os.listdir(directory):
        if (os.path.isfile(os.path.join(directory, item)) and 
            item.lower().endswith('.docx') and 
            not item.startswith('~$')):
            all_docx_files.append(item)
    
    # Сначала ищем по имени файла
    for filename in all_docx_files:
        filepath = os.path.join(directory, filename)
        
        if "КЖ" in filename and "КЖ" not in found_files:
            found_files["КЖ"] = filepath
        elif "СО" in filename and "СО" not in found_files:
            found_files["СО"] = filepath
        elif "ВР" in filename and "СВР" not in filename and "ВР" not in found_files:
            found_files["ВР"] = filepath
    
    # Если не все типы найдены, ищем по содержимому
    missing_types = [t for t in ["КЖ", "СО", "ВР"] if t not in found_files]
    
    if missing_types:
        for filename in all_docx_files:
            if len(missing_types) == 0:
                break
                
            filepath = os.path.join(directory, filename)
            
            # Пропускаем уже найденные файлы
            if filepath in found_files.values():
                continue
                
            try:
                designation = find_id(filepath)
                if designation:
                    for doc_type in missing_types[:]:
                        if doc_type == "ВР":
                            # Для ВР проверяем, что это не СВР
                            if "ВР" in designation and "СВР" not in designation:
                                found_files["ВР"] = filepath
                                missing_types.remove("ВР")
                                break
                        elif doc_type in designation:
                            found_files[doc_type] = filepath
                            missing_types.remove(doc_type)
                            break
            except Exception as e:
                print(f"Ошибка при анализе файла {filename}: {e}")
                continue
    
    return found_files

def main():
    if len(sys.argv) != 2:
        print("Использование: python find_files.py <путь_к_папке>")
        sys.exit(1)
    
    path = sys.argv[1]
    if not os.path.isdir(path):
        print("Указанный путь не существует или не является папкой")
        sys.exit(1)
    
    folder_name = os.path.basename(path.rstrip('/\\'))
    
    if folder_name.startswith("Книга"):
        found_files = find_files_in_directory(path)
        print(f"Найдены файлы в папке {folder_name}: {found_files}")
        
        # Запускаем обработку найденных файлов
        for doc_type, file_path in found_files.items():
            try:
                if doc_type == "КЖ":
                    subprocess.run([sys.executable, "cable_parser.py", file_path], check=True)
                elif doc_type == "СО":
                    subprocess.run([sys.executable, "spec_parser.py", file_path], check=True)
                elif doc_type == "ВР":
                    subprocess.run([sys.executable, "SpecifiedWork_parser.py", file_path], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Ошибка при обработке файла {file_path}: {e}")
    else:
        # Обрабатываем все подпапки, начинающиеся с "Книга"
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and item.startswith("Книга"):
                found_files = find_files_in_directory(item_path)
                print(f"Найдены файлы в папке {item}: {found_files}")
                
                # Запускаем обработку найденных файлов
                for doc_type, file_path in found_files.items():
                    try:
                        if doc_type == "КЖ":
                            subprocess.run([sys.executable, "cable_parser.py", file_path], check=True)
                        elif doc_type == "СО":
                            subprocess.run([sys.executable, "spec_parser.py", file_path], check=True)
                        elif doc_type == "ВР":
                            subprocess.run([sys.executable, "SpecifiedWork_parser.py", file_path], check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"Ошибка при обработке файла {file_path}: {e}")

if __name__ == "__main__":
    main()