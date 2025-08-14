// MainWindow.xaml.cs
using Microsoft.Win32;
using Npgsql;
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Windows;

namespace DocxParser
{
    public partial class MainWindow : Window
    {
        // Фиксированные параметры подключения
        private const string Host = "localhost";
        private const string Port = "5432";
        private const string Database = "cable_db";
        private const string User = "postgres";
        private const string Password = "test1";

        public MainWindow()
        {
            InitializeComponent();
            StatusText.Text = "Выберите файл спецификации (.docx) для импорта в PostgreSQL";
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

        private async void ProcessButton_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(FilePathTextBox.Text) || !File.Exists(FilePathTextBox.Text))
            {
                MessageBox.Show("Выберите существующий файл спецификации!", "Ошибка", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            string docxPath = FilePathTextBox.Text;
            
            StatusText.Text = "Импорт данных начат...";
            ProcessButton.IsEnabled = false;
            
            try
            {
                // Передаем фиксированные параметры в фоновый поток
                await Task.Run(() => ProcessWithPython(
                    docxPath, 
                    Host, 
                    Port, 
                    Database, 
                    User, 
                    Password));
                    
                StatusText.Text = "Данные успешно импортированы в PostgreSQL!";
            }
            catch (Exception ex)
            {
                StatusText.Text = $"Ошибка при импорте данных: {ex.Message}";
                MessageBox.Show(ex.ToString(), "Ошибка импорта", 
                    MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                ProcessButton.IsEnabled = true;
            }
        }

        private void ProcessWithPython(
            string docxPath, 
            string host, 
            string port, 
            string database, 
            string user, 
            string password)
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

            // Формируем аргументы для Python
            string arguments = $"\"{scriptPath}\" \"{docxPath}\" " +
                              $"\"{host}\" " +
                              $"\"{port}\" " +
                              $"\"{database}\" " +
                              $"\"{user}\" " +
                              $"\"{password}\"";
            
            var processInfo = new ProcessStartInfo
            {
                FileName = pythonExe,
                Arguments = arguments,
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
                    {
                        outputBuilder.AppendLine(e.Data);
                        Dispatcher.Invoke(() => StatusText.Text += $"\n{e.Data}");
                    }
                };
                
                process.ErrorDataReceived += (sender, e) => 
                {
                    if (!string.IsNullOrEmpty(e.Data)) 
                    {
                        errorBuilder.AppendLine(e.Data);
                        Dispatcher.Invoke(() => StatusText.Text += $"\nОШИБКА: {e.Data}");
                    }
                };

                process.Start();
                
                // Начинаем асинхронное чтение вывода
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                
                process.WaitForExit(120000); // Таймаут 120 секунд

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