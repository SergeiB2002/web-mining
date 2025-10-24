import time
import matplotlib.pyplot as plt
import pandas as pd
import psutil
import os
import json
from hh_selenium import HHAPISeleniumParser
import random

def create_directories():
    """Создает директории для графиков."""
    directories = [
        'graphs_selenium_api/load_testing',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Создана директория: {directory}")

def get_memory_usage():
    """Получает использование памяти текущим процессом в МБ"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def selenium_api_load_testing():
    """
    Нагрузочное тестирование для Selenium API парсера.
    """
    create_directories()
    
    test_pages = [1, 3, 5, 10]
    avg_response_times = []
    memory_usage_list = []
    vacancies_per_minute = []
    detailed_metrics = []
    
    for num_pages in test_pages:
        print(f"\n--- Тест с {num_pages} страницами ---")
        
        start_time = time.time()
        start_memory = get_memory_usage()
        
        parser = HHAPISeleniumParser(headless=True)
        
        try:
            search_start = time.time()
            
            vacancies = []
            for page in range(num_pages):
                page_start = time.time()
                data = parser.get_vacancies_from_page(page, "Python")
                page_end = time.time()
                
                if data and 'items' in data:
                    vacancies.extend(data['items'])
                    page_time = (page_end - page_start) * 1000
                    print(f"Страница {page}: {len(data['items'])} вакансий, {page_time:.2f} мс")
                
                time.sleep(0.5)  # Задержка между страницами
            
            search_end = time.time()
            search_time = search_end - search_start
            
        finally:
            parser.close()
        
        end_time = time.time()
        end_memory = get_memory_usage()
        
        # Расчет метрик
        total_time = end_time - start_time
        avg_response_time = (search_time / num_pages) * 1000 if num_pages > 0 else 0
        vpm = (len(vacancies) / total_time) * 60 if total_time > 0 else 0
        memory_used = end_memory
        
        avg_response_times.append(avg_response_time)
        memory_usage_list.append(memory_used)
        vacancies_per_minute.append(vpm)
        
        detailed_metrics.append({
            'pages_parsed': num_pages,
            'vacancies_found': len(vacancies),
            'avg_time_per_page_ms': avg_response_time,
            'vacancies_per_minute': vpm,
            'memory_used_mb': memory_used,
            'total_time_sec': total_time
        })
        
        print(f"Найдено вакансий: {len(vacancies)}")
        print(f"Среднее время на страницу: {avg_response_time:.2f} мс")
        print(f"Вакансий в минуту: {vpm:.2f}")
        print(f"Использование памяти: {memory_used:.2f} МБ")
        print(f"Общее время теста: {total_time:.2f} сек")
        
        time.sleep(2)
    
    # Графики нагрузочного тестирования
    # График 1: Среднее время на страницу
    plt.figure(figsize=(10, 6))
    plt.plot(test_pages, avg_response_times, 'bo-', linewidth=2, markersize=8)
    plt.title('Selenium API: Среднее время загрузки страницы')
    plt.xlabel('Количество страниц')
    plt.ylabel('Время на страницу (мс)')
    plt.grid(True, alpha=0.3)
    plt.savefig('graphs_selenium_api/load_testing/response_time_per_page.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # График 2: Вакансий в минуту
    plt.figure(figsize=(10, 6))
    plt.plot(test_pages, vacancies_per_minute, 'go-', linewidth=2, markersize=8)
    plt.title('Selenium API: Производительность парсинга')
    plt.xlabel('Количество страниц')
    plt.ylabel('Вакансий в минуту')
    plt.grid(True, alpha=0.3)
    plt.savefig('graphs_selenium_api/load_testing/vacancies_per_minute.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # График 3: Использование памяти
    plt.figure(figsize=(10, 6))
    plt.plot(test_pages, memory_usage_list, 'ro-', linewidth=2, markersize=8)
    plt.title('Selenium API: Использование памяти')
    plt.xlabel('Количество страниц')
    plt.ylabel('Память (МБ)')
    plt.grid(True, alpha=0.3)
    plt.savefig('graphs_selenium_api/load_testing/memory_usage.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Сохраняем метрики
    df_metrics = pd.DataFrame(detailed_metrics)
    df_metrics.to_csv('selenium_api_load_testing_metrics.csv', index=False, encoding='utf-8-sig')
    print("\nМетрики нагрузочного тестирования сохранены")
    
    return df_metrics


if __name__ == "__main__":
    load_metrics = selenium_api_load_testing()
