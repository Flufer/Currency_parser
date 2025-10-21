import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import argparse
import os

def get_currency_rate(currency_code='R01235', days=30):
    """
    Получает курс валюты с API ЦБ РФ за указанный период.
    
    Args:
        currency_code (str): Код валюты (R01235 - USD, R01239 - EUR)
        days (int): Количество дней для анализа
    
    Returns:
        pd.DataFrame: DataFrame с датами и курсами
    """
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Форматируем даты для API
    date_req1 = start_date.strftime('%d/%m/%Y')
    date_req2 = end_date.strftime('%d/%m/%Y')
    
    url = "http://www.cbr.ru/scripts/XML_dynamic.asp"
    params = {
        'date_req1': date_req1,
        'date_req2': date_req2,
        'VAL_NM_RQ': currency_code
    }
    
    try:
        print(f"Запрашиваю данные с {date_req1} по {date_req2}...")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Парсим XML ответ
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        
        data = []
        for record in root.findall('Record'):
            date = record.get('Date')
            rate = record.find('Value').text.replace(',', '.')
            data.append({
                'date': datetime.strptime(date, '%d.%m.%Y'),
                'rate': float(rate)
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"Успешно получено {len(df)} записей")
        return df
        
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return None

def plot_currency_rate(df, currency_name='USD/RUB', save_path=None):
    """
    Строит график курса валюты.
    
    Args:
        df (pd.DataFrame): DataFrame с данными
        currency_name (str): Название валютной пары
        save_path (str): Путь для сохранения графика
    """
    
    plt.figure(figsize=(12, 6))
    plt.plot(df['date'], df['rate'], marker='o', linewidth=2, markersize=4)
    plt.title(f'Курс {currency_name} за период с {df["date"].min().strftime("%d.%m.%Y")} по {df["date"].max().strftime("%d.%m.%Y")}', fontsize=14)
    plt.xlabel('Дата')
    plt.ylabel('Курс, руб.')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Добавляем аннотацию с последним значением
    last_rate = df['rate'].iloc[-1]
    last_date = df['date'].iloc[-1]
    plt.annotate(f'{last_rate:.2f}', 
                xy=(last_date, last_rate), 
                xytext=(10, 10), 
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"График сохранен: {save_path}")
    
    plt.close()

def analyze_currency_data(df):
    """
    Анализирует данные и выводит статистику.
    """
    if df is None or df.empty:
        print("Нет данных для анализа")
        return
    
    print("\n=== АНАЛИЗ ДАННЫХ ===")
    print(f"Период: {df['date'].min().strftime('%d.%m.%Y')} - {df['date'].max().strftime('%d.%m.%Y')}")
    print(f"Количество точек данных: {len(df)}")
    print(f"Минимальный курс: {df['rate'].min():.2f} руб.")
    print(f"Максимальный курс: {df['rate'].max():.2f} руб.")
    print(f"Средний курс: {df['rate'].mean():.2f} руб.")
    print(f"Последний курс: {df['rate'].iloc[-1]:.2f} руб.")
    
    # Изменение за период
    change = df['rate'].iloc[-1] - df['rate'].iloc[0]
    change_percent = (change / df['rate'].iloc[0]) * 100
    print(f"Изменение за период: {change:+.2f} руб. ({change_percent:+.1f}%)")

def main():
    """Основная функция для запуска из командной строки."""
    
    # Словарь кодов валют
    CURRENCY_CODES = {
        'USD': 'R01235',
        'EUR': 'R01239',
        'GBP': 'R01035',
        'CNY': 'R01375'
    }
    
    parser = argparse.ArgumentParser(description='Парсинг и визуализация курсов валют ЦБ РФ')
    parser.add_argument('--currency', '-c', choices=CURRENCY_CODES.keys(), default='USD',
                       help='Валюта для анализа (USD, EUR, GBP, CNY)')
    parser.add_argument('--days', '-d', type=int, default=30,
                       help='Количество дней для анализа')
    parser.add_argument('--output', '-o', default='currency_chart.png',
                       help='Путь для сохранения графика')
    
    args = parser.parse_args()
    
    currency_code = CURRENCY_CODES[args.currency]
    currency_name = f'{args.currency}/RUB'
    
    print(f"Анализируем курс {currency_name} за {args.days} дней...")
    
    # Получаем данные
    df = get_currency_rate(currency_code, args.days)
    
    if df is not None and not df.empty:
        # Анализируем данные
        analyze_currency_data(df)
        
        # Строим график
        plot_currency_rate(df, currency_name, args.output)
        
        # Сохраняем данные в CSV
        csv_filename = f"{args.currency.lower()}_rates.csv"
        df.to_csv(csv_filename, index=False)
        print(f"Данные сохранены в: {csv_filename}")
        
    else:
        print("Не удалось получить данные")

# Пример использования
if __name__ == "__main__":
    # Если запускаем напрямую - анализируем USD за 30 дней
    print("=== ПАРСЕР КУРСОВ ВАЛЮТ ЦБ РФ ===")
    
    # Получаем данные по USD
    df_usd = get_currency_rate('R01235', 30)
    
    if df_usd is not None:
        analyze_currency_data(df_usd)
        plot_currency_rate(df_usd, 'USD/RUB', 'usd_rub_chart.png')
        
        # Дополнительно: пример с EUR
        print("\n" + "="*50)
        df_eur = get_currency_rate('R01239', 30)
        if df_eur is not None:
            analyze_currency_data(df_eur)
            plot_currency_rate(df_eur, 'EUR/RUB', 'eur_rub_chart.png')
