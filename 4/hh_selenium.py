from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import json
import pandas as pd
import random
import logging
from typing import List, Dict, Any, Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HHAPISeleniumParser:
    """
    Парсер HH.ru через API с использованием Selenium (рабочий пример из книги).
    """
    
    def __init__(self, headless: bool = True):
        self.driver = None
        self.setup_driver(headless)
    
    def setup_driver(self, headless: bool):
        """Настройка ChromeDriver."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
    
    def get_vacancies_from_page(self, page: int, search_text: str = "программист") -> Dict[str, Any]:
        """
        Получает вакансии с указанной страницы через API.
        """
        url = f'https://api.hh.ru/vacancies?text={search_text}&area=1&per_page=50&page={page}'
        print(f"Загружаем страницу {page}: {url}")
        
        self.driver.get(url)
        time.sleep(2)  # Небольшая задержка для стабильности
        
        try:
            content = self.driver.find_element(By.TAG_NAME, "pre").text
            data = json.loads(content)
            return data
        except Exception as e:
            print(f"Ошибка при получении данных со страницы {page}: {e}")
            return {}
    
    def search_vacancies(self, search_queries: List[str], pages_per_query: int = 5) -> List[Dict[str, Any]]:
        """
        Поиск вакансий по нескольким запросам.
        """
        all_vacancies = []
        
        for query in search_queries:
            print(f"\n=== Поиск вакансий: '{query}' ===")
            
            for page in range(pages_per_query):
                print(f"Страница {page + 1}...")
                
                data = self.get_vacancies_from_page(page, query)
                
                if not data or 'items' not in data:
                    print(f"Нет данных на странице {page}. Прерывание.")
                    break
                
                vacancies = data['items']
                if not vacancies:
                    print("Больше вакансий нет. Прерывание.")
                    break
                
                for vacancy in vacancies:
                    vacancy['search_query'] = query
                
                all_vacancies.extend(vacancies)
                print(f"Добавлено вакансий: {len(vacancies)}")
                
                if page >= data.get('pages', 1) - 1:
                    break
                
                # Задержка для соблюдения лимитов API
                time.sleep(0.5)
        
        print(f"\nВсего собрано вакансий: {len(all_vacancies)}")
        return all_vacancies
    
    def close(self):
        """Закрытие драйвера."""
        if self.driver:
            self.driver.quit()
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str = "hh_api_vacancies.json"):
        """Сохраняет данные в JSON файл."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Данные сохранены в {filename}")

def main():
    """Основная функция для запуска Selenium парсера."""
    print("Запуск Selenium парсера hh.ru...")
    
    parser = HHAPISeleniumParser(headless=True)
    
    try:
        search_queries = [
        "Data Scientist",
        "ML Engineer",
        "Системный аналитик",
        "Программист",
        "Разработчик"
    ]
        
        all_vacancies = parser.search_vacancies(search_queries, pages_per_query=3)
        
        # Сохраняем сырые данные
        parser.save_to_json(all_vacancies, "hh_api_vacancies.json")
        
        print(f"\nУспешно собрано вакансий: {len(all_vacancies)}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        parser.close()

if __name__ == "__main__":
    main()
