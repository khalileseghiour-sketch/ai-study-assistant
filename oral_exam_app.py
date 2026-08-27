import streamlit as st
from google import genai
from pypdf import PdfReader

st.set_page_config(page_title="AI Oral Examiner Multilingual", layout="wide")
st.title("🎙️ محاكي الإمتحانات الشفهية الذكي (متعدد اللغات والدارجة)")

# 1. إعداد API Key
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ يرجى ضبط GEMINI_API_KEY في Streamlit Secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# 2. القائمة الجانبية
st.sidebar.header("⚙️ إعدادات الإمتحان")
subject_name = st.sidebar.text_input("اسم المادة / الموضوع:", "علوم وتكنولوجيا - أوتوماتيك")
difficulty = st.sidebar.select_slider("مستوى الصعوبة:", options=["سهل", "متوسط", "صعب"])
language = st.sidebar.selectbox(
    "لغة/لهجة الأستاذ الممتحِن:", 
    ["الدارجة الجزائرية", "الدارجة المصرية", "العربية الفصحى", "Français", "English"]
)

# 3. رفع الملف
uploaded_pdf = st.file_uploader("📂 ارفع ملف الدرس (PDF) هنا ليطرح الأستاذ الأسئلة منه:", type=["pdf"])

lesson_text = ""
if uploaded_pdf:
    reader = PdfReader(uploaded_pdf)
    for page in reader.pages:
        text = page.extract_text()
        if text:
            lesson_text += text + "\n"
    st.success("✅ تم قراءة ملف الدرس بنجاح! جاهز للتسميع والامتحان.")

st.divider()

if "question" not in st.session_state:
    st.session_state.question = ""
if "feedback" not in st.session_state:
    st.session_state.feedback = ""

# 4. طرح السؤال
if st.button("🚀 اطرح سؤالاً جديداً من الدرس"):
    if not lesson_text:
        st.warning("⚠️ يرجى رفع ملف PDF للدرس أولاً لكي يستطيع الأستاذ سؤالك منه!")
    else:
        prompt = f"""
        أنت أستاذ ممتحن خبير ومُشجع في مادة: {subject_name}.
        مستوى الصعوبة: {difficulty}.
        اللغة/اللهجة المطلوبة للتحدث بها: {language}.
        
        محتوى الدرس المستخرج من الملف:
        {lesson_text[:12000]}
        
        التعليمات:
        1. اطرح سؤالاً شفهياً واحداً فقط ومباشراً يختبر فهم الطالب لجزء مهم من هذا الدرس.
        2. التزم تماماً بالتحدث بلغة/لهجة: {language} (إذا كانت الدارجة الجزائرية استخدم كلمات مثل: وش، كيفاش، علاش، فاهم، إلخ).
        3. اكتب السؤال مباشرة بدون مقدمات طويلة.
        """
        with st.spinner("الأستاذ يقرأ الدرس ويفكر في سؤال..."):
            res = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            st.session_state.question = res.text
            st.session_state.feedback = ""

# 5. التفاعل والتقييم
if st.session_state.question:
    st.subheader("👨‍🏫 سؤال الأستاذ الممتحِن:")
    st.info(st.session_state.question)

    st.subheader("🗣️ إجابتك (تحدث بأي لغة أو لهجة تريحك):")
    audio_val = st.audio_input("اضغط على الميكروفون وسجل إجابتك بصوتك:")
    text_val = st.text_area("أو اكتب الإجابة هنا:")

    if st.button("📤 تقديم الإجابة والتقييم"):
        user_response = ""
        
        if audio_val:
            with st.spinner("جاري استماع الأستاذ للصوت وتحليله..."):
                audio_bytes = audio_val.read()
                res_audio = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[
                        {"inline_data": {"mime_type": "audio/wav", "data": audio_bytes}},
                        "قم بتفريغ هذا الصوت إلى نص بدقة مهما كانت اللهجة (جزائرية، مصري، عرنسي، إنجليزي)."
                    ]
                )
                user_response = res_audio.text
                st.write(f"📝 **ما فهمه الأستاذ من كلامك الصوتي:** {user_response}")
        elif text_val:
            user_response = text_val

        if user_response:
            prompt_eval = f"""
            أنت أستاذ ممتحن.
            السؤال المطروح: {st.session_state.question}
            إجابة الطالب (سواء كانت بالدارجة أو الفصحى أو الإنجليزية/الفرنسية): {user_response}
            نص الدرس الأصلي: {lesson_text[:12000]}
            اللغة/اللهجة المطلوبة للرد بها: {language}

            المطلوب منك:
            1. فهم إجابة الطالب مهما كانت لهجته (يفهم الدارجة الجزائرية، المصرية، إلخ).
            2. تقييم الإجابة بنقطة من 10.
            3. تقديم التقييم والملاحظات بنفس اللغة/اللهجة المحدد ({language}).
            4. توضيح إذا كانت إجابته صحيحة، أو ما الذي نقصه في الفهم وكيف يصححه.
            """
            with st.spinner("الأستاذ يقيّم إجابتك الآن..."):
                eval_res = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt_eval
                )
                st.session_state.feedback = eval_res.text
        else:
            st.warning("سجل صوتك أو اكتب الإجابة أولاً!")

if st.session_state.feedback:
    st.divider()
    st.subheader("📊 تقييم الأستاذ وملاحظاته:")
    st.success(st.session_state.feedback)
