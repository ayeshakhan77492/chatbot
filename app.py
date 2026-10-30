
import streamlit as st
from google import genai
import json
import re

st.set_page_config(
    page_title="AI Chatbot Buddy",
    page_icon="🤖",
    layout="wide"
)

# Gemini AI connection
client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

# Custom design
st.markdown("""
<style>
.stApp {
    background-color: #f4f7fc;
}
.main-title {
    text-align: center;
    color: #2446a8;
    font-size: 38px;
    font-weight: bold;
}
.subtitle {
    text-align: center;
    color: #64748b;
    font-size: 17px;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# Sidebar
with st.sidebar:
    st.title("🤖 Chatbot Buddy")
    st.write("Your personal AI study assistant.")
    st.divider()

    st.subheader("📚 Study Topics")
    st.write("🐍 Python Programming")
    st.write("🧠 Artificial Intelligence")
    st.write("🔐 Cybersecurity")

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🔄 Reset Quiz", use_container_width=True):
        st.session_state.quiz_questions = []
        st.session_state.quiz_submitted = False
        st.rerun()

    st.caption("Made with Python and Gemini AI")

# Main heading
st.markdown(
    '<div class="main-title">🤖 AI Chatbot Buddy</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Your Friendly Personal AI Study Assistant</div>',
    unsafe_allow_html=True
)

# Chatbot section
st.header("💬 Ask Your Study Buddy")

if not st.session_state.messages:
    st.info(
        "👋 Hello! Ask me anything about Python, "
        "Artificial Intelligence or Cybersecurity!"
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input(
    "Ask me about Python, AI or Cybersecurity..."
)

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Buddy is thinking..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=f"""
                    You are AI Chatbot Buddy, a friendly study assistant.
                    Explain Python, Artificial Intelligence and
                    Cybersecurity in simple language with examples.
                    When showing Python code, use proper separate lines
                    and clear code formatting.

                    Student question: {user_input}
                    """
                )

                answer = response.text or "Please try asking again."
                st.markdown(answer)

            except Exception as e:
                answer = f"Sorry, something went wrong: {e}"
                st.error(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

# Quiz section
st.divider()
st.header("📝 Student Quiz Mode")
st.write("Test your knowledge with AI-generated MCQs!")

quiz_topic = st.selectbox(
    "Choose your quiz topic:",
    ["Python", "Artificial Intelligence", "Cybersecurity"],
    key="quiz_topic"
)

if st.button("🎯 Generate 5 MCQs"):
    with st.spinner("Preparing your quiz..."):
        try:
            quiz_response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=f"""
                Create exactly 5 beginner-level MCQs about {quiz_topic}.

                Return ONLY a valid JSON array in this format:
                [
                  {{
                    "question": "Question text",
                    "options": {{
                      "A": "First option",
                      "B": "Second option",
                      "C": "Third option",
                      "D": "Fourth option"
                    }},
                    "answer": "A",
                    "explanation": "Short explanation"
                  }}
                ]

                The answer must be one of A, B, C, or D.
                Make all questions educational and accurate.
                Do not include Markdown or extra text.
                """
            )

            raw_text = quiz_response.text.strip()
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            questions = json.loads(raw_text)

            if len(questions) != 5:
                raise ValueError("The AI did not generate exactly 5 questions.")

            for q in questions:
                if (
                    not isinstance(q, dict)
                    or not isinstance(q.get("question"), str)
                    or not isinstance(q.get("options"), dict)
                    or set(q["options"].keys()) != {"A", "B", "C", "D"}
                    or q.get("answer") not in ["A", "B", "C", "D"]
                    or not isinstance(q.get("explanation"), str)
                ):
                    raise ValueError("The generated quiz format is invalid.")

            st.session_state.quiz_questions = questions
            st.session_state.quiz_submitted = False

        except Exception as e:
            st.error(f"Quiz could not be generated: {e}")

# Interactive quiz display
if st.session_state.quiz_questions:
    st.subheader("📖 Answer the Questions")

    if not st.session_state.quiz_submitted:
        with st.form("student_quiz"):
            for i, q in enumerate(st.session_state.quiz_questions):
                st.markdown(f"**Q{i + 1}. {q['question']}**")

                st.radio(
                    "Select your answer:",
                    options=["A", "B", "C", "D"],
                    format_func=lambda x, options=q["options"]:
                        f"{x}. {options[x]}",
                    key=f"quiz_answer_{i}"
                )

                st.divider()

            submitted = st.form_submit_button("✅ Submit My Answers")

        if submitted:
            st.session_state.quiz_submitted = True
            st.rerun()

    else:
        score = 0

        for i, q in enumerate(st.session_state.quiz_questions):
            selected = st.session_state.get(f"quiz_answer_{i}")

            st.markdown(f"**Q{i + 1}. {q['question']}**")
            st.write(f"Your answer: {selected}. {q['options'][selected]}")

            if selected == q["answer"]:
                score += 1
                st.success("Correct answer!")
            else:
                correct = q["answer"]
                st.error(
                    f"Incorrect. Correct answer: "
                    f"{correct}. {q['options'][correct]}"
                )

            st.info(f"Explanation: {q['explanation']}")
            st.divider()

        st.subheader(f"🏆 Your Score: {score} / 5")

        if score == 5:
            st.balloons()
            st.success("Excellent! Perfect score!")
        elif score >= 3:
            st.success("Good job! Keep practicing!")
        else:
            st.warning("Keep learning. You can do better!")

        if st.button("🔄 Try Another Quiz"):
            st.session_state.quiz_questions = []
            st.session_state.quiz_submitted = False
            st.rerun()
