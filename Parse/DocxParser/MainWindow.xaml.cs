using Microsoft.Win32;
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Windows;

namespace DocxParser
{
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            StatusText.Text = "Выберите файл спецификации (.docx) для обработки";
        }

        private void BrowseButton_Click(object sender, RoutedEventArgs e)
        {
            var openFileDialog = new OpenFileDialog
            {
                Filter = "Word Documents|*.docx|All Files|*.*",
                Title = "Выберите файл спецификации"
            };

            if (openFileDialog.ShowDialog() == true)
            {
                FilePathTextBox.Text = openFileDialog.FileName;
                StatusText.Text = $"Выбран файл: {Path.GetFileName(openFileDialog.FileName)}";
            }
        }

        private void ProcessButton_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(FilePathTextBox.Text) || !File.Exists(FilePathTextBox.Text))
            {
                MessageBox.Show("Выберите существующий файл спецификации!", "Ошибка", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            string docxPath = FilePathTextBox.Text;
            string outputDir = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                "SpecParserOutput_" + DateTime.Now.ToString("yyyyMMdd_HHmmss"));

            StatusText.Text = "Обработка начата...";

            try
            {
                ProcessWithPython(docxPath, outputDir);
                StatusText.Text = $"Успешно обработано!\nРезультаты сохранены в:\n{outputDir}";
                
                // Открываем папку с результатами
                Process.Start("explorer.exe", outputDir);
            }
            catch (Exception ex)
            {
                StatusText.Text = $"Ошибка при обработке: {ex.Message}";
                MessageBox.Show(ex.ToString(), "Критическая ошибка", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void ProcessWithPython(string docxPath, string outputDir)
        {
            // Найдем python.exe
            string pythonExe = FindPythonExe();
            if (pythonExe == null)
            {
                throw new FileNotFoundException("python.exe не найден. Убедитесь, что Python 3.9+ установлен и добавлен в PATH.");
            }

            // Путь к скрипту в директории приложения
            string scriptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "spec_parser.py");
            
            if (!File.Exists(scriptPath))
            {
                throw new FileNotFoundException($"Python-скрипт не найден: {scriptPath}");
            }

            var processInfo = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = $"\"{scriptPath}\" \"{docxPath}\" \"{outputDir}\"",
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                WindowStyle = ProcessWindowStyle.Hidden,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            using (var process = new Process { StartInfo = processInfo })
            {
                StringBuilder outputBuilder = new StringBuilder();
                StringBuilder errorBuilder = new StringBuilder();

                process.OutputDataReceived += (sender, e) => 
                {
                    if (!string.IsNullOrEmpty(e.Data)) 
                        outputBuilder.AppendLine(e.Data);
                };
                
                process.ErrorDataReceived += (sender, e) => 
                {
                    if (!string.IsNullOrEmpty(e.Data)) 
                        errorBuilder.AppendLine(e.Data);
                };

                process.Start();
                
                // Начинаем асинхронное чтение вывода
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                
                process.WaitForExit(60000); // Таймаут 60 секунд

                if (process.ExitCode != 0)
                {
                    string errorDetails = errorBuilder.ToString();
                    if (string.IsNullOrEmpty(errorDetails))
                        errorDetails = outputBuilder.ToString();
                    
                    throw new Exception($"Ошибка выполнения скрипта (код {process.ExitCode}):\n{errorDetails}");
                }
            }
        }

        private string FindPythonExe()
        {
            // Проверим стандартные пути установки Python
            string[] possiblePaths = 
            {
                @"C:\Program Files\Python39\python.exe",
                @"C:\Users\" + Environment.UserName + @"\AppData\Local\Programs\Python\Python39\python.exe",
                @"C:\Program Files\Python310\python.exe",
                @"C:\Users\" + Environment.UserName + @"\AppData\Local\Programs\Python\Python310\python.exe",
                @"C:\Program Files\Python311\python.exe",
                @"C:\Users\" + Environment.UserName + @"\AppData\Local\Programs\Python\Python311\python.exe",
                @"C:\Program Files\Python312\python.exe",
                @"C:\Users\" + Environment.UserName + @"\AppData\Local\Programs\Python\Python312\python.exe"
            };
            
            foreach (var path in possiblePaths)
            {
                if (File.Exists(path)) 
                    return path;
            }
            
            // Проверим переменную PATH
            var pathDirs = Environment.GetEnvironmentVariable("PATH")?.Split(';') ?? Array.Empty<string>();
            foreach (var dir in pathDirs)
            {
                try
                {
                    string pythonPath = Path.Combine(dir, "python.exe");
                    if (File.Exists(pythonPath))
                        return pythonPath;
                }
                catch (Exception)
                {
                    // Пропустим невалидные пути
                }
            }
            
            return null;
        }
    }
}