import requests 
import json 
import time 
import os 
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import seaborn as sns
import re


# Функция для извлечения навыков из HTML-резюме
def extract_skills_from_resume(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    skills = {'soft_skills': [], 'hard_skills': []}
    
    # Функция для разбиения составных навыков
    def split_composite_skills(skill_text):
        """Разбивает составные навыки на отдельные элементы"""
        result = []
        
        # Если навык содержит двоеточие, разбиваем его
        if ':' in skill_text:
            # Разделяем на категорию и значения
            category, values = skill_text.split(':', 1)
            # Разбиваем значения по запятым
            individual_skills = [v.strip() for v in values.split(',')]
            result.extend(individual_skills)
        else:
            result.append(skill_text)
        
        return result
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Ищем строки таблицы
        if '<tr class=odd>' in line or '<tr class=even>' in line:
            # Следующие две строки содержат категорию и значение
            if i + 2 < len(lines):
                category_line = lines[i + 1].strip()
                value_line = lines[i + 2].strip()
                
                # Извлекаем текст между тегами td
                if '<td class=c1>' in category_line and '<td class=c2>' in value_line:
                    category = category_line.replace('<td class=c1>', '').replace('</td>', '').strip()
                    value = value_line.replace('<td class=c2>', '').replace('</td>', '').strip()
                    
                    # Обрабатываем многострочные значения
                    if not value and i + 3 < len(lines):
                        next_line = lines[i + 3].strip()
                        if not next_line.startswith('<tr') and not next_line.startswith('</tr'):
                            value = next_line.replace('<br>', ' ').strip()
                    
                    # Soft Skills
                    if category == 'Личные качества' and value:
                        skills['soft_skills'].extend([skill.strip() for skill in value.split(',')])
                    
                    elif category == 'Увлечения' and value:
                        # Обрабатываем увлечения
                        hobbies = value.replace('<br>', ';').split(';')
                        for hobby in hobbies:
                            hobby = hobby.strip()
                            if hobby and ':' not in hobby:  # Простые увлечения
                                skills['soft_skills'].append(hobby)
                            elif ':' in hobby:  # Сложные структуры (Игры: ...)
                                hobby_type, hobby_list = hobby.split(':', 1)
                                skills['soft_skills'].append(hobby_type.strip())
                                # Разбиваем список игр/книг
                                sub_hobbies = [h.strip() for h in hobby_list.split(',')]
                                skills['soft_skills'].extend(sub_hobbies)
                    
                    elif category == 'Личные достижения' and value:
                        skills['soft_skills'].append(value)
                    
                    # Hard Skills
                    elif category == 'Владение языками' and value:
                        languages = value.split(';')
                        for lang in languages:
                            lang = lang.strip()
                            if '-' in lang:
                                lang_name, level = lang.split('-', 1)
                                skills['hard_skills'].append(f"{lang_name.strip()} ({level.strip()})")
                            else:
                                skills['hard_skills'].append(lang)
                    
                    elif category == 'Профессиональная специализация и владение компьютером' and value:
                        # Обрабатываем профессиональные навыки
                        lines_to_process = []
                        j = i + 2
                        while j < len(lines) and ('<td class=c2>' in lines[j] or '<br>' in lines[j] or 
                                                (lines[j].strip() and not lines[j].strip().startswith('<tr'))):
                            line_content = lines[j].strip()
                            if '<td class=c2>' in line_content:
                                line_content = line_content.replace('<td class=c2>', '').replace('</td>', '')
                            if line_content and not line_content.startswith('<tr'):
                                lines_to_process.append(line_content)
                            j += 1
                        
                        full_text = ' '.join(lines_to_process)
                        # Разбиваем по номерам пунктов
                        sections = full_text.split('<br>')
                        for section in sections:
                            section = section.strip()
                            if section and not section.isspace():
                                if '.' in section and section[0].isdigit():
                                    section = section.split('.', 1)[1].strip()
                                
                                # Разбиваем составные навыки
                                individual_skills = split_composite_skills(section)
                                skills['hard_skills'].extend(individual_skills)
    
    # Очистка и фильтрация навыков
    skills['soft_skills'] = [skill for skill in skills['soft_skills'] if skill and len(skill) > 1 and skill != 'br']
    skills['hard_skills'] = [skill for skill in skills['hard_skills'] if skill and len(skill) > 1 and skill != 'br']
    
    # Убираем дубликаты
    skills['soft_skills'] = list(set(skills['soft_skills']))
    skills['hard_skills'] = list(set(skills['hard_skills']))
    
    # Дополнительная очистка для hard skills (убираем пустые и слишком короткие)
    skills['hard_skills'] = [skill for skill in skills['hard_skills'] if skill and len(skill) > 2]
    
    return skills

# Функция для расчета семантического сходства
def calculate_semantic_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    
    # Создаем TF-IDF векторайзер
    vectorizer = TfidfVectorizer(stop_words='english', min_df=1)
    
    try:
        # Преобразуем тексты в TF-IDF векторы
        tfidf_matrix = vectorizer.fit_transform([text1, text2])
        
        # Вычисляем косинусное сходство
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return similarity*100
    except:
        return 0.0

# Основная функция для анализа сходства
def analyze_vacancies_similarity(vacancies_folder, resume_skills):
    results = []
    
    # Создаем текстовые представления навыков
    soft_skills_text = ' '.join(resume_skills['soft_skills'])
    hard_skills_text = ' '.join(resume_skills['hard_skills'])
    
    # Обрабатываем каждую вакансию
    for vacancy_file in os.listdir(vacancies_folder):
        if vacancy_file.endswith('.json'):
            try:
                with open(os.path.join(vacancies_folder, vacancy_file), 'r', encoding='utf-8') as f:
                    vacancy_data = json.load(f)
                
                vacancy_description = vacancy_data.get('description', '')
                vacancy_name = vacancy_data.get('name', '')
                vacancy_id = vacancy_data.get('id', '')
                
                if vacancy_description:
                    # Очищаем описание от HTML тегов
                    soup = BeautifulSoup(vacancy_description, 'html.parser')
                    clean_description = soup.get_text()
                    
                    # Вычисляем сходство
                    soft_similarity = calculate_semantic_similarity(clean_description, soft_skills_text)
                    hard_similarity = calculate_semantic_similarity(clean_description, hard_skills_text)
                    overall_similarity = (soft_similarity + hard_similarity) / 2
                    
                    results.append({
                        'vacancy_id': vacancy_id,
                        'vacancy_name': vacancy_name,
                        'soft_similarity': soft_similarity,
                        'hard_similarity': hard_similarity,
                        'overall_similarity': overall_similarity,
                        'description_length': len(clean_description)
                    })
                    
            except Exception as e:
                print(f"Ошибка при обработке вакансии {vacancy_file}: {e}")
                continue
    
    return pd.DataFrame(results)

# Функция для визуализации результатов
def visualize_results(df, resume_skills):
    # Создаем графики
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 1. Распределение сходства
    axes[0, 0].hist(df['soft_similarity'], bins=20, alpha=0.7, label='Soft Skills')
    axes[0, 0].hist(df['hard_similarity'], bins=20, alpha=0.7, label='Hard Skills')
    axes[0, 0].set_title('Распределение семантического сходства')
    axes[0, 0].set_xlabel('Сходство')
    axes[0, 0].set_ylabel('Количество вакансий')
    axes[0, 0].legend()
    
    # 2. Сравнение soft vs hard skills
    axes[0, 1].scatter(df['soft_similarity'], df['hard_similarity'], alpha=0.6)
    axes[0, 1].set_title('Soft Skills vs Hard Skills сходство')
    axes[0, 1].set_xlabel('Soft Skills сходство')
    axes[0, 1].set_ylabel('Hard Skills сходство')
    
    # 3. Топ вакансий по общему сходству
    top_vacancies = df.nlargest(10, 'overall_similarity')
    axes[0, 2].barh(range(len(top_vacancies)), top_vacancies['overall_similarity'])
    axes[0, 2].set_yticks(range(len(top_vacancies)))
    axes[0, 2].set_yticklabels([name[:30] + '...' for name in top_vacancies['vacancy_name']], fontsize=8)
    axes[0, 2].set_title('Топ-10 вакансий по сходству')
    
    # 4. Зависимость сходства от длины описания
    axes[1, 0].scatter(df['description_length'], df['overall_similarity'], alpha=0.6)
    axes[1, 0].set_title('Зависимость сходства от длины описания')
    axes[1, 0].set_xlabel('Длина описания')
    axes[1, 0].set_ylabel('Общее сходство')
    
    # 5. Boxplot сходства по типам навыков
    similarity_data = [df['soft_similarity'], df['hard_similarity']]
    axes[1, 1].boxplot(similarity_data, labels=['Soft Skills', 'Hard Skills'])
    axes[1, 1].set_title('Распределение сходства по типам навыков')
    
    # 6. Heatmap корреляции
    corr_matrix = df[['soft_similarity', 'hard_similarity', 'overall_similarity', 'description_length']].corr()
    sns.heatmap(corr_matrix, annot=True, ax=axes[1, 2], cmap='coolwarm')
    axes[1, 2].set_title('Матрица корреляции')
    
    plt.tight_layout()
    plt.savefig('semantic_similarity_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("\n=== СТАТИСТИКА АНАЛИЗА СЕМАНТИЧЕСКОГО СХОДСТВА ===")
    print(f"Всего проанализировано вакансий: {len(df)}")
    print(f"\nSoft Skills из резюме: {resume_skills['soft_skills']}")
    print(f"\nHard Skills из резюме: {resume_skills['hard_skills']}")
    print(f"\nСтатистика сходства:")
    print(f"Soft Skills - Среднее: {df['soft_similarity'].mean():.3f}%, Макс: {df['soft_similarity'].max():.3f}%")
    print(f"Hard Skills - Среднее: {df['hard_similarity'].mean():.3f}%, Макс: {df['hard_similarity'].max():.3f}%")
    print(f"Общее - Среднее: {df['overall_similarity'].mean():.3f}%, Макс: {df['overall_similarity'].max():.3f}%")


if __name__ == "__main__":
    # Извлекаем навыки из резюме
    print("Извлечение навыков из резюме...")
    resume_skills = extract_skills_from_resume('index.htm')
    
    print("Soft Skills:", resume_skills['soft_skills'])
    print("Hard Skills:", resume_skills['hard_skills'])
    
    # Анализируем сходство вакансий
    if os.path.isdir('vacancies_desc'):
        print("\nАнализ семантического сходства...")
        results_df = analyze_vacancies_similarity('vacancies_desc', resume_skills)
        
        if not results_df.empty:
            results_df.to_excel('semantic_similarity_results.xlsx', index=False)
            results_df = results_df.sort_values('overall_similarity', ascending=False)
            top_results = results_df.head(20)
            top_results.to_excel('top_similar_vacancies.xlsx', index=False)
            visualize_results(results_df, resume_skills)
            
            print(f"\nРезультаты сохранены в файлы:")
            print("- semantic_similarity_results.xlsx (все вакансии)")
            print("- top_similar_vacancies.xlsx (топ-20 вакансий)")
            print("- semantic_similarity_analysis.png (графики)")
        else:
            print("Нет данных для анализа. Убедитесь, что вакансии были собраны.")
    else:
        print("Папка 'vacancies' не найдена. Сначала выполните сбор вакансий.")
