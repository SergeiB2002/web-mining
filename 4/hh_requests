import requests
import time
import json
from typing import Dict, List, Any, Optional

class HHParser:
    """
    Парсер для API HeadHunter для поиска вакансий, связанных с программированием.
    """
    
    def __init__(self):
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def search_vacancies(self, text: str, area: int = 1, per_page: int = 100, page: int = 0) -> Optional[Dict[str, Any]]:
        """
        Поиск вакансий по текстовому запросу.
        
        Args:
            text (str): Текст для поиска (напр., "Python разработчик").
            area (int): ID региона (1 - Москва, 2 - СПб, 113 - Россия).
            per_page (int): Количество вакансий на странице (макс. 100).
            page (int): Номер страницы (начинается с 0).
            
        Returns:
            Dict[str, Any]: JSON-ответ от API или None в случае ошибки.
        """
        params = {
            'text': text,
            'area': area,
            'per_page': per_page,
            'page': page,
            'only_with_salary': True  # Опционально: только вакансии с указанной зарплатой
        }
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()  # Проверка на HTTP ошибки
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")
            return None

    def parse_vacancies(self, search_query: str, pages_to_parse: int = 5) -> List[Dict[str, Any]]:
        """
        Парсит несколько страниц с вакансиями.
        
        Args:
            search_query (str): Запрос для поиска.
            pages_to_parse (int): Количество страниц для парсинга.
            
        Returns:
            List[Dict[str, Any]]: Список спарсенных вакансий.
        """
        all_vacancies = []
        
        for page in range(pages_to_parse):
            print(f"Парсинг страницы {page + 1}...")
            
            data = self.search_vacancies(search_query, page=page)
            
            if data is None:
                print(f"Не удалось получить данные для страницы {page}. Прерывание.")
                break
                
            vacancies = data.get('items', [])
            if not vacancies:
                print("Больше вакансий нет. Прерывание.")
                break
                
            all_vacancies.extend(vacancies)
            
            if page >= data['pages'] - 1:
                break
                
            # Уважаем API и добавляем задержку
            time.sleep(0.5)
            
        print(f"Всего спарсено вакансий: {len(all_vacancies)}")
        return all_vacancies

    def save_to_json(self, data: List[Dict[str, Any]], filename: str = "hh_vacancies.json"):
        """Сохраняет данные в JSON файл."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Данные сохранены в {filename}")

if __name__ == "__main__":
    parser = HHParser()
    
    search_queries = [
        "Python разработчик",
        "Java разработчик",
        "JavaScript разработчик",
        "C++ разработчик",
        "Data Scientist",
        "Программист"
    ]
    
    all_vacancies_data = []
    
    for query in search_queries:
        print(f"\n=== Поиск вакансий для: '{query}' ===")
        vacancies = parser.parse_vacancies(search_query=query, pages_to_parse=3)
        all_vacancies_data.extend(vacancies)
    
    parser.save_to_json(all_vacancies_data, "programming_vacancies.json")
