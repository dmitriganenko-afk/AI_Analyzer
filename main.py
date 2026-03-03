import streamlit as st
from zhipuai import ZhipuAI
from pypdf import PdfReader  # Новая библиотека для чтения PDF

# --- Настройки страницы ---
st.set_page_config(page_title="Умный Анализатор Резюме", layout="wide")

# --- Получаем ключ из секретов ---
try:
    api_key = st.secrets["ZHIPUAI_API_KEY"]
except:
    st.error("Ошибка: API ключ не найден в секретах.")
    st.stop()

# --- Функция извлечения текста из PDF ---
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# --- Функция анализа (без изменений, только промпт чуть уточнил) ---
def analyze_resume(text):
    if not api_key:
        return "Ошибка: Нет API Key"
    
    try:
        client = ZhipuAI(api_key=api_key)
        
        prompt = f"""
        Ты — опытный HR-директор. Проанализируй следующее резюме и выдели самую суть.
        Резюме:
        {text}
        
        Верни ответ в следующем формате:
        1. **Имя кандидата**: ...
        2. **Контакты**: (телефон и email)
        3. **Ключевые навыки**: (списком через запятую, выдели 5-7 самых главных)
        4. **Опыт**: (общее количество лет)
        5. **Рекомендация**: (стоит ли нанимать этого кандидата? Коротко Да/Нет и почему)
        """
        
        response = client.chat.completions.create(
            model="glm-4",  
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка при обращении к ИИ: {e}"

# --- Интерфейс ---
st.title("🤖 Умный Анализатор Резюме (PDF + Текст)")
st.markdown("Загрузите резюме в формате PDF или вставьте текст вручную.")

# --- Выбор метода ввода ---
option = st.radio("Выберите способ ввода:", ("Текст", "Загрузить PDF"), horizontal=True)

resume_text = ""

if option == "Загрузить PDF":
    uploaded_file = st.file_uploader("Загрузите файл резюме (PDF)", type="pdf")
    if uploaded_file is not None:
        # Читаем файл
        resume_text = extract_text_from_pdf(uploaded_file)
        with st.expander("Посмотреть извлеченный текст"):
            st.text(resume_text)
else:
    resume_text = st.text_area("Вставьте текст резюме сюда:", height=300)

# --- Кнопка анализа ---
if st.button("Проанализировать с помощью ИИ", type="primary"):
    if resume_text.strip():
        with st.spinner("ИИ анализирует резюме..."):
            result = analyze_resume(resume_text)
            st.markdown("---")
            st.markdown("### Результаты анализа:")
            st.markdown(result)
    else:
        st.warning("Пожалуйста, загрузите файл или вставьте текст.")

