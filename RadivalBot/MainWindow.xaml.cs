using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using Python.Runtime;
using static System.Formats.Asn1.AsnWriter;

namespace RadicalAIBot
{
    public partial class MainWindow : Window, INotifyPropertyChanged
    {
        private bool _isRunning = false;
        private int _passwordLength;

        public event PropertyChangedEventHandler PropertyChanged;

        public int PasswordLength
        {
            get => _passwordLength;
            set
            {
                if (_passwordLength != value)
                {
                    _passwordLength = value;
                    OnPropertyChanged(nameof(PasswordLength));
                }
            }
        }

        public MainWindow()
        {
            InitializeComponent();
            DataContext = this;
        }

        private async void StartButton_Click(object sender, RoutedEventArgs e)
        {
            var server = ServerAddressTextBox.Text;
            var username = UsernameTextBox.Text;
            var password = PasswordBox.Password;

            if (string.IsNullOrEmpty(server) || string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
            {
                MessageBox.Show("Please enter all login details.");
                return;
            }

            ExecutePythonScript("C:\\Users\\Asus\\source\\repos\\RadivalBot\\RadivalBot\\AnalysisPy.py", server, username, password);
            _isRunning = true;
            LogTextBox.AppendText("Bot started.\n");
            await StartBot(server, username, password);
        }

        private void ExecutePythonScript(string scriptName, string server, string username, string password)
        {
            try
            {
                string pythonPath = @"C:\Users\Asus\AppData\Local\Programs\Python\Python312\python.exe";
                string scriptPath = scriptName;

                ProcessStartInfo start = new ProcessStartInfo
                {
                    FileName = pythonPath,
                    Arguments = $"{scriptPath} {server} {username} {password}",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };

                using (Process process = Process.Start(start))
                {
                    using (StreamReader reader = process.StandardOutput)
                    {
                        string line;
                        while ((line = reader.ReadLine()) != null)
                        {
                            LogResult(line);
                        }
                    }

                    using (StreamReader reader = process.StandardError)
                    {
                        string error;
                        while ((error = reader.ReadLine()) != null)
                        {
                            LogResult(error);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error executing Python script: {ex.Message}");
            }
        }

        private async Task StartBot(string server, string username, string password)
        {
            try
            {
                // Set Python environment variables and initialize PythonEngine
                Environment.SetEnvironmentVariable("PYTHONNET_PYDLL", @"C:\Users\Asus\AppData\Local\Programs\Python\Python312\python312.dll");
                PythonEngine.PythonHome = @"C:\Users\Asus\AppData\Local\Programs\Python\Python312";
                PythonEngine.PythonPath = string.Join(
                    Path.PathSeparator.ToString(),
                    new string[] {
                @"C:\Users\Asus\AppData\Local\Programs\Python\Python312",
                @"C:\Users\Asus\AppData\Local\Programs\Python\Python312\Lib",
                @"C:\Users\Asus\AppData\Local\Programs\Python\Python312\DLLs",
                @"C:\Users\Asus\AppData\Local\Programs\Python\Python312\Lib\site-packages",
                @"C:\Users\Asus\source\repos\RadivalBot\RadivalBot" // Include the directory where AnalysisPy.py is located
                    }
                );

                PythonEngine.Initialize();

                // Import the AnalysisPy module
                dynamic analysisPy = Py.Import("AnalysisPy");

                // Continuously execute Python script while the bot is running
                while (_isRunning)
                {
                    using (Py.GIL())
                    {
                        try
                        {
                            // Execute Python script line by line
                            using (PyScope scope = Py.CreateScope())
                            {
                                // Access and instantiate classes from AnalysisPy
                                dynamic mt5Integration = analysisPy.MT5Integration();

                                // Initialize MT5 integration
                                LogResult("Initializing MT5...");
                                string mt5InitResult = await ExecutePythonLine(mt5Integration, "initialize_mt5()");
                                LogResult(mt5InitResult);

                                // Login to MT5 account
                                LogResult("Logging into MT5...");
                                string loginResult = await ExecutePythonLine(mt5Integration, $"login_mt5('{username}', '{password}', '{server}')");
                                LogResult(loginResult);

                                if (!loginResult.Contains("successfully"))
                                {
                                    LogTextBox.AppendText("Login failed. Stopping the bot.\n");
                                    _isRunning = false;
                                    break;
                                }

                                // Get account info
                                LogResult("Fetching account info...");
                                string accountInfoResult = await ExecutePythonLine(mt5Integration, "get_account_info()");
                                LogResult(accountInfoResult);

                                // Shutdown MT5
                                LogResult("Shutting down MT5...");
                                string shutdownResult = await ExecutePythonLine(mt5Integration, "shutdown_mt5()");
                                LogResult(shutdownResult);
                            }
                        }
                        catch (Exception ex)
                        {
                            LogResult($"Error: {ex.Message}");
                        }
                    }

                    // Wait for a specified duration before executing the next iteration
                    await Task.Delay(5000); // Adjust delay time as needed
                }
            }
            finally
            {
                // Shutdown PythonEngine when the bot stops running
                PythonEngine.Shutdown();
            }
        }

        private async Task<string> ExecutePythonLine(dynamic obj, string pythonLine)
        {
            // Execute Python script line and return the result
            return await Task.Run(() => obj.Execute(pythonLine).ToString());
        }


        private void StopButton_Click(object sender, RoutedEventArgs e)
        {
            _isRunning = false;
            LogTextBox.AppendText("Bot stopped.\n");
        }

        private void LogResult(string message)
        {
            Dispatcher.Invoke(() =>
            {
                LogTextBox.AppendText($"{message}\n");
                LogTextBox.ScrollToEnd();
            });
        }

 

        protected void OnPropertyChanged(string name)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }

        private void ServerAddressTextBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            // Implement logic to handle the text change event
        }

        private void UsernameTextBox_TextChanged(object sender, TextChangedEventArgs e)
        {
            // Implement logic to handle the text change event
        }

        private void PasswordBox_PasswordChanged(object sender, RoutedEventArgs e)
        {
            PasswordLength = PasswordBox.Password.Length;
        }
    }
}
