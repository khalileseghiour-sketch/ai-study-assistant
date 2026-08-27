import os
import streamlit as st
from google import genai
from pypdf import PdfReader

# إعداد واجهة التطبيق
st.set_page_config(page_title="AI Study Assistant", layout="wide")
st.title("📚 نظام أتمتة وتلخيص الدروس الذكي")

# القائمة الجانبية لإدخال المفتاح
api_key = st.sidebar.text_input("مفتاح Gemini API Key:", type="password")

# 1. رفع ملفات الدروس (PDF)
uploaded_files = st.file_uploader(
    "ارفع ملفات الدروس (PDF)", type=["pdf"], accept_multiple_files=True
)

extracted_text = ""

if uploaded_files:
    for pdf in uploaded_files:
        reader = PdfReader(pdf)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"

    st.success(
        f"تم استخراج النص بنجاح من {len(uploaded_files)} ملف/ملفات! (إجمالي الحروف: {len(extracted_text)})"
    )

    # أزرار الأتمتة
    col1, col2, col3 = st.columns(3)

    with col1:
        btn_summarize = st.button("📝 تلخيص الدرس كلياً")
    with col2:
        btn_quiz = st.button("❓ توليد أسئلة واختبارات")
    with col3:
        btn_keypoints = st.button("💡 استخراج المفاهيم الأساسية")

    # 2. أتمتة التلخيص والتحليل
    if api_key:
        client = genai.Client(api_key=api_key)

        # خيار التلخيص
        if btn_summarize:
            prompt = f"أنت أستاذ وخبير أكاديمي. قم بتلخيص النص التالي بأسلوب منظم وشامل باللغة العربية، مع إبراز النقاط الرئيسية:\n\n{extracted_text[:15000]}"
            with st.spinner("جاري التلخيص التلقائي..."):
                res = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                st.subheader("📌 ملخص الدرس:")
                st.write(res.text)

        # خيار توليد الكويز
        if btn_quiz:
            prompt = f"بناءً على النص التالي، أنشئ اختباراً من 5 أسئلة متعددة الخيارات (MCQ) مع الإجابات النموذجية والشرح في النهاية:\n\n{extracted_text[:15000]}"
            with st.spinner("جاري إنشاء الأسئلة..."):
                res = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                st.subheader("🧪 اختبار المراجعة السريعة:")
                st.write(res.text)

        # خيار النقاط المفتاحية
        if btn_keypoints:
            prompt = f"استخرج أهم القوانين، المصطلحات، والمفاهيم التي يجب حفظها أو فهمها من هذا النص بشكل نقاط مركزة:\n\n{extracted_text[:15000]}"
            with st.spinner("جاري استخراج القوانين والمفاهيم..."):
                res = client.models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                st.subheader("💡 أهم القوانين والمفاهيم:")
                st.write(res.text)

    else:
        if btn_summarize or btn_quiz or btn_keypoints:
            st.error("يرجى إدخال API Key في القائمة الجانبية أولاً!")

    # 3. شات مباشر مع الدرس
    st.divider()
    st.subheader("💬 اسأل الذكاء الاصطناعي عن أي جزئية في الملف")
    user_q = st.text_input("اكتب سؤالك هنا (مثال: اشرح لي القانون الموجود في الصفحة الأخيرة):")

    if user_q and api_key:
        prompt = f"بناءً على محتوى الدرس التالي، أجب عن سؤال المستخدم بدقة ودون اختلاق معطيات خارجية:\nالدرس:\n{extracted_text[:15000]}\n\nسؤال المستخدم: {user_q}"
        with st.spinner("جاري البحث والإجابة..."):
            res = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            st.write(res.text)