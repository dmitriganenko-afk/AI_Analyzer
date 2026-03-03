import streamlit as st
from zhipuai import ZhipuAI
from pypdf import PdfReader  # Новая библиотека для чтения PDF

# --- Настройки страницы ---
st.set_page_config(page_title="Умный Анализатор Резюме и Вакансии", layout="wide")

# --- Получаем ключ из секретов ---
try:
    api_key = st.secrets["ZHIPUAI_API_KEY"]  # здесь должен лежать ваш ключ ZhipuAI
except Exception:
    api_key = None

if not api_key:
    st.error("Ошибка: API ключ ZhipuAI не найден. Добавьте его в `st.secrets['ZHIPUAI_API_KEY']`.")
    st.stop()

# --- Функция извлечения текста из PDF (БЕЗ ИЗМЕНЕНИЙ) ---
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# --- Функция анализа соответствия резюме и вакансии через ZhipuAI ---
def analyze_resume_vs_job(resume_text: str, job_text: str) -> str:
    try:
        client = ZhipuAI(api_key=api_key)

        prompt = f"""
Ты — HR-менеджер.

У тебя есть два текста:

1) Резюме кандидата:
\"\"\"{resume_text}\"\"\"

2) Требования к вакансии:
\"\"\"{job_text}\"\"\"

Сравни резюме и вакансию и выдай результат СТРОГО в следующем формате (по-русски):

Имя кандидата: <ФИО или как указано в резюме, если нет — напиши "Не найдено">
Процент соответствия (Score): <число от 0 до 100 без знака %>
Плюсы (совпадающие навыки):
- навык 1
- навык 2
- ...
Минусы (недостающие навыки):
- навык 1
- навык 2
- ...
Рекомендация: <Нанимать или Не нанимать> — краткое обоснование в 1–2 предложениях.

Обязательно следуй ровно этой структуре и не добавляй ничего лишнего.
"""

        response = client.chat.completions.create(
            model="glm-4",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка при обращении к ИИ: {e}"

# --- Интерфейс ---
st.title("🤖 Анализатор Резюме и Требований Вакансии")
st.markdown(
    """
Слева — резюме кандидата (текст или PDF), справа — текст **\"Требования вакансии\"**.  
Нажмите кнопку, чтобы ИИ сравнил их и выдал оценку соответствия.
"""
)

# --- Две колонки: слева резюме, справа вакансия ---
col_left, col_right = st.columns(2)

resume_text = ""
job_text = ""

with col_left:
    st.subheader("Резюме кандидата")

    input_mode = st.radio(
        "Способ ввода резюме:",
        ("Текст", "Загрузить PDF"),
        horizontal=True,
    )

    if input_mode == "Загрузить PDF":
        uploaded_file = st.file_uploader("Загрузите файл резюме (PDF)", type="pdf")
        if uploaded_file is not None:
            resume_text = extract_text_from_pdf(uploaded_file)
            with st.expander("Показать извлечённый текст резюме"):
                st.text(resume_text)
    else:
        resume_text = st.text_area(
            "Текст резюме:",
            height=350,
            placeholder="Вставьте сюда текст резюме кандидата...",
        )

with col_right:
    st.subheader("Требования вакансии")
    job_text = st.text_area(
        "Текст требований к вакансии:",
        height=350,
        placeholder="Опишите требования к вакансии: обязанности, навыки, стек, опыт и т.п.",
    )

# --- Кнопка анализа соответствия ---
if st.button("Проанализировать соответствие", type="primary"):
    if not resume_text or not resume_text.strip():
        st.warning("Пожалуйста, введите или загрузите резюме кандидата.")
    elif not job_text or not job_text.strip():
        st.warning("Пожалуйста, введите текст требований вакансии.")
    else:
        with st.spinner("ИИ сравнивает резюме с вакансией..."):
            result = analyze_resume_vs_job(resume_text, job_text)
            st.markdown("---")
            st.markdown("### Результаты анализа соответствия")
            st.markdown(result)