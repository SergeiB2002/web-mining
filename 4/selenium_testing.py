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

def selenium_load_testing():
    """
    Нагрузочное тестирование для Selenium API парсера.
    """
    create_directories()
    
    # Тестовые сценарии - количество страниц для парсинга
    test_pages = [5, 10, 20, 30, 50]
    
    # Метрики для хранения результатов
    avg_response_times_ms = []  # Среднее время ответа в миллисекундах
    rps_list = []               # Запросов в секунду
    memory_usage_list = []      # Использование памяти в МБ
    detailed_metrics = []       # Детальные метрики для каждого теста
    
    print("=== НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ SELENIUM API ===")
    
    for num_pages in test_pages:
        print(f"\n--- Тест с {num_pages} страницами ---")
        
        start_time = time.time()
        start_memory = get_memory_usage()
        
        parser = HHAPISeleniumParser(headless=True)
        response_times = []
        successful_requests = 0
        
        try:
            for page in range(num_pages):
                print(f"Запрос страницы {page + 1}...")
                
                request_start = time.time()
                data = parser.get_vacancies_from_page(page, "Python")
                request_end = time.time()
                
                request_time_ms = (request_end - request_start) * 1000
                response_times.append(request_time_ms)
                
                if data and 'items' in data:
                    successful_requests += 1
                    print(f"  Успешно: {len(data['items'])} вакансий, время: {request_time_ms:.2f} мс")
                else:
                    print(f"  Ошибка запроса")
                
                # Небольшая задержка между запросами
                time.sleep(0.5)
                
        finally:
            parser.close()
        
        end_time = time.time()
        end_memory = get_memory_usage()
        
        total_time = end_time - start_time
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        rps = successful_requests / total_time if total_time > 0 else 0
        memory_used = end_memory
        
        avg_response_times_ms.append(avg_response_time)
        rps_list.append(rps)
        memory_usage_list.append(memory_used)
        
        detailed_metrics.append({
            'pages_parsed': num_pages,
            'successful_requests': successful_requests,
            'avg_response_time_ms': avg_response_time,
            'rps': rps,
            'memory_used_mb': memory_used,
            'total_time_sec': total_time
        })
        
        print(f"Результаты теста:")
        print(f"  Успешных запросов: {successful_requests}/{num_pages}")
        print(f"  Среднее время ответа: {avg_response_time:.2f} мс")
        print(f"  RPS: {rps:.2f} запросов/сек")
        print(f"  Использование памяти: {memory_used:.2f} МБ")
        print(f"  Общее время теста: {total_time:.2f} сек")
        
        # Задержка между тестами
        time.sleep(2)
    
    # График 1: Среднее время ответа
    plt.figure(figsize=(10, 6))
    plt.plot(test_pages, avg_response_times_ms, 'bo-', linewidth=2, markersize=8)
    plt.title('Selenium API: Среднее время ответа')
    plt.xlabel('Количество страниц')
    plt.ylabel('Время ответа (мс)')
    plt.grid(True, alpha=0.3)
    plt.savefig('graphs_selenium_api/load_testing/response_time.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Сохранен график: Среднее время ответа")
    
    # График 2: Запросов в секунду (RPS)
    plt.figure(figsize=(10, 6))
    plt.plot(test_pages, rps_list, 'go-', linewidth=2, markersize=8)
    plt.title('Selenium API: Запросов в секунду (RPS)')
    plt.xlabel('Количество страниц')
    plt.ylabel('Запросов в секунду')
    plt.grid(True, alpha=0.3)
    plt.savefig('graphs_selenium_api/load_testing/rps_performance.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Сохранен график: Запросов в секунду (RPS)")
    
    # График 3: Использование памяти
    plt.figure(figsize=(10, 6))
    plt.plot(test_pages, memory_usage_list, 'ro-', linewidth=2, markersize=8)
    plt.title('Selenium API: Использование памяти')
    plt.xlabel('Количество страниц')
    plt.ylabel('Память (МБ)')
    plt.grid(True, alpha=0.3)
    plt.savefig('graphs_selenium_api/load_testing/memory_usage.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Сохранен график: Использование памяти")
    
    # Сохраняем детальные метрики в таблицу
    df_metrics = pd.DataFrame(detailed_metrics)
    df_metrics.to_csv('selenium_load_testing_metrics.csv', index=False, encoding='utf-8-sig')
    print("\n✓ Метрики нагрузочного тестирования сохранены в 'selenium_load_testing_metrics.csv'")
    
    return df_metrics

if __name__ == "__main__":
    selenium_load_testing()
