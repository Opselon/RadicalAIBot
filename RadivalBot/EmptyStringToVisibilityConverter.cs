using System;
using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace RadicalAIBot
{
    public class EmptyStringToVisibilityConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            // Check if the value is a string and is empty or null
            if (value is string str && string.IsNullOrEmpty(str))
            {
                // Return Visibility.Collapsed if the string is empty or null
                return Visibility.Collapsed;
            }
            // Return Visibility.Visible for non-empty strings or non-string values
            return Visibility.Visible;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            // This converter does not support converting back
            throw new NotSupportedException();
        }
    }
}
