import streamlit as st
from zhipuai import ZhipuAI

# --- Настройки страницы ---
st.set_page_config(page_title="Умный Анализатор Резюме", layout="wide")

# --- Получаем ключ из секретов ---
try:
    api_key = st.secrets["ZHIPUAI_API_KEY"]
except:
    st.error("Ошибка: API ключ не найден в секретах. Добавьте его в .streamlit/secrets.toml")
    st.stop()
    
# ... остальной код остается без изменений ...

st.title("🤖 Умный Анализатор Резюме (Powered by GLM-4)")
st.markdown("Этот сервис использует ИИ для извлечения смысла из текста, а не просто поиск слов.")

# --- Функция анализа ---
def analyze_resume(text):
    if not api_key or "ВСТАВЬТЕ" in api_key:
        return "Ошибка: Не вставлен API Key в код программы!"
    
    try:
        client = ZhipuAI(api_key=api_key)
        
        prompt = f"""
        Ты — опытный HR-директор. Проанализируй следующее резюме и выдели самую суть.
        Резюме:
        {text}
        
        Верни ответ в следующем формате:
        1. **Имя кандидата**: ...
        2. **Контакты**: (телефон и email)
        3. **Ключевые навыки**: (списком через запятую, выдели 5-7 самых главных, опираясь на опыт работы)
        4. **Опыт**: (общее количество лет)
        5. **Рекомендация**: (стоит ли нанимать этого кандидата на руководящую должность? Коротко Да/Нет и почему)
        """
        
        response = client.chat.completions.create(
            model="glm-4",  
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка при обращении к ИИ: {e}"

# --- Интерфейс ---
resume_text = st.text_area("Вставьте текст резюме сюда:", height=300)

if st.button("Проанализировать с помощью ИИ", type="primary"):
    if resume_text.strip():
        with st.spinner("ИИ анализирует резюме... Это займет пару секунд."):
            result = analyze_resume(resume_text)
            st.markdown("---")
            st.markdown("### Результаты анализа:")
            st.markdown(result)
    else:
        st.warning("Пожалуйста, вставьте текст резюме.")

