import streamlit as st
from zhipuai import ZhipuAI
from pypdf import PdfReader
import sqlite3
import pandas as pd
from datetime import datetime

# --- Настройка страницы ---
st.set_page_config(page_title="HR-Аналитик PRO", layout="wide")

# --- 1. Настройка Базы Данных ---
def init_db():
    conn = sqlite3.connect('resume_history.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            full_name TEXT,
            job_title TEXT,
            match_score TEXT,
            recommendation TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_analysis(full_name, job, score, rec):
    conn = sqlite3.connect('resume_history.db')
    c = conn.cursor()
    c.execute('INSERT INTO analyses (timestamp, full_name, job_title, match_score, recommendation) VALUES (?, ?, ?, ?, ?)',
              (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), full_name, job, score, rec))
    conn.commit()
    conn.close()

def load_history():
    conn = sqlite3.connect('resume_history.db')
    query = """
        SELECT 
            timestamp as 'Дата/Время', 
            full_name as 'ФИО Кандидата', 
            job_title as 'Вакансия', 
            match_score as 'Соответствие', 
            recommendation as 'Решение'
        FROM analyses ORDER BY timestamp DESC LIMIT 10
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

init_db()

# --- Настройки API ---
try:
    api_key = st.secrets["ZHIPUAI_API_KEY"]
except:
    st.error("Ошибка: API ключ не найден.")
    st.stop()

# --- Функции обработки ---
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def analyze_match(resume_text, job_description):
    if not api_key:
        return "Ошибка: Нет API Key"
    
    try:
        client = ZhipuAI(api_key=api_key)
        
        prompt = f"""
        Ты — старший HR-директор. Проведи глубокий анализ соответствия резюме вакансии.

        РЕЗЮМЕ:
        {resume_text}

        ВАКАНСИЯ:
        {job_description}

        Выполни анализ и выведи результат ТОЧНО в следующем формате. Не меняй названия меток.

        ### 1. Полное ФИО для сохранения
        (Напиши здесь только Фамилию Имя Отчество цифрами и буквами, без лишних слов. Например: Иванов Иван Иванович)

        ### 2. Оценка соответствия
        (Напиши только цифру с процентом, например: 85%)

        ### 3. Анализ навыков
        (Напиши развернутый анализ: совпадения, пробелы, риски. 3-4 предложения).

        ### 4. Обоснование рекомендации
        (Напиши подробное обоснование твоего решения. 3-4 предложения).

        ### 5. Итоговый вердикт
        (Напиши строго одно слово: РЕКОМЕНДУЕТСЯ или НЕ РЕКОМЕНДУЕТСЯ)
        """

        response = client.chat.completions.create(
            model="glm-4",  
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка при обращении к ИИ: {e}"

# --- Интерфейс ---
st.title("🚀 HR-Аналитик PRO")

# ИЗМЕНЕНИЕ ДИЗАЙНА: Выносим выбор формата НАД колонки
st.subheader("📄 Ввод данных")
option = st.radio("Формат резюме:", ("Текст", "PDF"), horizontal=True, key="r_opt")

# Создаем колонки
col1, col2 = st.columns(2)

resume_text = ""

with col1:
    # Заголовок левой колонки
    st.markdown("**Резюме кандидата (скопируйте и вставте в окно или прикрепите в файле pdf)**")
    
    if option == "PDF":
        uploaded_file = st.file_uploader("Загрузите файл PDF", type="pdf", label_visibility="collapsed")
        if uploaded_file:
            resume_text = extract_text_from_pdf(uploaded_file)
            # Если текст извлечен, показываем его в маленьком окне для проверки
            if resume_text:
                with st.expander("✅ Текст извлечен (нажмите для просмотра)"):
                    st.text(resume_text)
    else:
        # ИЗМЕНЕНИЕ ДИЗАЙНА: Фиксированная высота окна
        resume_text = st.text_area("Текст резюме", height=300, label_visibility="collapsed")

with col2:
    # Заголовок правой колонки
    st.markdown("**Требования вакансии (скопируйте и вставте в это окно)**")
    
    # ИЗМЕНЕНИЕ ДИЗАЙНА: Фиксированная высота окна, совпадающая с левой
    job_description = st.text_area("Текст вакансии", height=300, label_visibility="collapsed")

# --- Кнопка и логика ---
st.markdown("---")
if st.button("🔍 Анализировать и Сохранить", type="primary"):
    if resume_text and job_description:
        with st.spinner("Глубокий анализ..."):
            result = analyze_match(resume_text, job_description)
            st.markdown("---")
            st.markdown("### 📝 Результат анализа:")
            st.markdown(result)
            
            # Логика парсинга
            try:
                lines = result.split('\n')
                full_name = "Не указано"
                score = "0%"
                rec = "Не определено"
                
                current_block = ""
                for line in lines:
                    line_clean = line.strip().replace('*', '')
                    
                    if "### 1." in line:
                        current_block = "name"
                        continue
                    if "### 2." in line:
                        current_block = "score"
                        continue
                    
                    if current_block == "name" and line_clean and "ФИО" not in line_clean:
                        full_name = line_clean
                        current_block = ""
                    
                    if "%" in line_clean:
                        score = line_clean

                if "НЕ РЕКОМЕНДУЕТСЯ" in result:
                    rec = "НЕ РЕКОМЕНДУЕТСЯ"
                elif "РЕКОМЕНДУЕТСЯ" in result:
                    rec = "РЕКОМЕНДУЕТСЯ"
                
                save_analysis(full_name, job_description, score, rec)
                st.success(f"Сохранено в историю: {full_name}")
            except Exception as e:
                st.warning(f"Анализ показан, но не сохранен (ошибка парсинга).")
    else:
        st.warning("Заполните оба поля.")

# --- Блок Истории ---
st.markdown("---")
st.subheader("📚 История последних анализов")
history_df = load_history()
if not history_df.empty:
    st.dataframe(history_df, use_container_width=True)
else:
    st.info("История пуста. Проведите первый анализ.")
