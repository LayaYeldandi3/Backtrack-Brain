import streamlit as st
import random
import time
import json
import base64
import re  # For password validation
from streamlit_lottie import st_lottie
import google.generativeai as genai

# --------------------------------------
# Configuration
# --------------------------------------

st.set_page_config(page_title="Reverse Quiz Game", page_icon="🔄", layout="wide")

# Configure Google Gemini API (Replace with your API key)
genai.configure(api_key="AIzaSyCA8_FOhqITTiowCCM6S7v8_bsjPIjsnho")  

# Initialize AI Model
model = genai.GenerativeModel("gemini-1.5-pro")

# --------------------------------------
# Lottie & Video Background Setup
# --------------------------------------

# Load Lottie Animation

# Function to Play Success Sound


    
def load_audio(audio_file):
    with open(audio_file, "rb") as f:
        audio_bytes = f.read()
    encoded_audio = base64.b64encode(audio_bytes).decode()
    return f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{encoded_audio}" type="audio/mp3">
        </audio>
    """
def set_background_image(image_path):
    with open(image_path, "rb") as img_file:
        base64_str = base64.b64encode(img_file.read()).decode()
        css_code = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpg;base64,{base64_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(css_code, unsafe_allow_html=True)

def load_lottie_file(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

lottie_bg = load_lottie_file("backgroundanimation.json")

# Inject Background Video (Optional)
video_html = """
    <video autoplay loop muted playsinline style="
        position: fixed;
        right: 0;
        bottom: 0;
        min-width: 100%;
        min-height: 100%;
        z-index: -2;
        object-fit: cover;">
        <source src="Video.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>
"""
st.markdown(
    f"""
    {video_html}
    <style>
    
    
    [data-testid="stAppViewContainer"] {{
        
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh !important;
        flex-direction: column;
        overflow: hidden !important;
        
    }}
    .container {{
        
        display: flex;
        justify-content: center;
        align-items: center;
        width: 90%;
        max-width: 1200px;
    }}
    .lottie-container {{
    position: fixed;
    top: 50%;
    left: 5%;
    transform: translateY(-50%);
    width: 400px;
    height: auto;
    z-index: 9999;
    pointer-events: none;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------
# User Authentication
# --------------------------------------

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Layout with Columns
    
    col1, col2 = st.columns([1.2, 1])

    # LEFT SIDE: Lottie Animation
    with col1:
        st.markdown('<div class="lottie-container">', unsafe_allow_html=True)
        st_lottie(lottie_bg, speed=1, loop=True, quality="high", height=500, width=500)
        st.markdown('</div>', unsafe_allow_html=True)

    # RIGHT SIDE: Authentication
    with col2:
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        st.title("BACKTRACK BRAIN")
        st.subheader(random.choice([
            "🤔 Are you ready to think in reverse?",
            "🧠 Flip your perspective & challenge your brain!",
            "🔄 The game where answers come first – can you create the question?",
            "🎉 Welcome to the upside-down world of trivia!",
        ]))

        avatars = ["🦸 Super Thinker", "🕵 Detective Genius", "🤓 Brainy Nerd", "🎭 Quiz Master"]
        avatar_choice = st.radio("Choose Your Avatar:", avatars, index=0)

        username = st.text_input("Enter Your Mind-Bending Username")
        password = st.text_input("Enter Your Secret Brain Code", type="password")

        # Password Validation
        def is_valid_password(password):
            return (
                re.search(r"[A-Z]", password)
                and re.search(r"[a-z]", password)
                and re.search(r"\d", password)
                and re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
                and len(password) >= 8
            )

        if st.button("🚀 Let’s Reverse the Quiz!"):
            if not username:
                st.error("⚠ Oops! You forgot to enter your username!")
            elif not is_valid_password(password):
                st.error(
                    "Your password must include:\n"
                    "✅ At least 8 characters\n"
                    "✅ One uppercase letter (A-Z)\n"
                    "✅ One number (0-9)\n"
                    "✅ One special character (!@#$...)"
                )
            else:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.avatar = avatar_choice
                st.success(f"Welcome, {username} the {avatar_choice}! Get ready to twist some questions!")

    st.stop()

# --------------------------------------
# Game Logic Starts Here After Authentication
# --------------------------------------

# Initialize Game State
if "previous_answers" not in st.session_state:
    st.session_state.previous_answers = {}

if "submitted_questions" not in st.session_state:
    st.session_state.submitted_questions = set()

if "game_started" not in st.session_state:
    st.session_state.game_started = False
    st.session_state.show_coding_subcategories = False
    st.session_state.score = 0
    st.session_state.current_answer = ""
    st.session_state.category = ""
    st.session_state.subcategory = ""

# Dataset Mapping
datasets = {
    "Science": "science.txt",
    "History": "history.txt",
    "Math": "math.txt",
    "English": "english.txt",
    "Coding": {
        "C": "c.txt",
        "C++": "cpp.txt",
        "Java": "java.txt",
        "Python": "python.txt"
    }
}

# Get Random Unique Answer Function
def get_random_answer(category, subcategory=None):
    try:
        file_path = datasets[category] if category != "Coding" else datasets[category][subcategory]
        with open(file_path, "r") as file:
            answers = [line.strip() for line in file.readlines() if line.strip()]

        if not answers:
            return "No answers available."

        if category not in st.session_state.previous_answers:
            st.session_state.previous_answers[category] = set()

        available_answers = list(set(answers) - st.session_state.previous_answers[category])

        if not available_answers:
            return "No more unique answers available in this category."

        answer = random.choice(available_answers)
        st.session_state.previous_answers[category].add(answer)
        return answer
    except FileNotFoundError:
        return f"Error: {file_path} not found."
    except Exception as e:
        return f"Error: {str(e)}"

# AI Score Function
def score_question(user_question, answer):
    try:
        prompt = f"""
You are a strict evaluator. Given an ANSWER and a QUESTION, determine whether the QUESTION is highly RELEVANT to the ANSWER.

Definition of RELEVANT:
- The QUESTION must specifically ask about or directly relate to the ANSWER.
- If the QUESTION is vague, incomplete, generic, or partially related, or it is same as ANSWER, it is NOT relevant.
- The QUESTION should not repeat or mention in the ANSWER.

Scoring rules:
- 1 (RELEVANT): Only if the QUESTION clearly asks for the ANSWER.
- 0 (NOT RELEVANT): If the QUESTION is incomplete, partially related, vague, or does not make sense.

ONLY return a single number: 1 or 0.

ANSWER: {answer}
QUESTION: {user_question}
"""
        response = model.generate_content(prompt)
        score_text = response.text.strip()
        score = int(score_text)
        return max(0, min(score, 1))
    
       
    
        
    except Exception as e:
        st.error(f"Scoring error: {e}")
        return 0

# Start, Restart, and Back Functions
def start_game(category, subcategory=None):
    st.session_state.game_started = True
    st.session_state.category = category
    st.session_state.subcategory = subcategory
    st.session_state.current_answer = get_random_answer(category, subcategory)

def restart_game():
    st.session_state.current_answer = get_random_answer(st.session_state.category, st.session_state.subcategory)

def go_back():
    st.session_state.game_started = False
    st.session_state.show_coding_subcategories = False

# --------------------------------------
# Game UI & Screens
# --------------------------------------

# 🎮 Main Menu
if not st.session_state.game_started:
    set_background_image("back.jpg")#if not st.session_state.game_started:
   

# Inject CSS for blue light effect on the title
    st.markdown(
    """
    <style>
    .title {
        font-size: 4rem;
        color: white;
        text-align: center;
        animation: glow 1.5s ease-in-out infinite;
    }
    @keyframes glow {
    0% {
        text-shadow: 0 0 5px #808000, 0 0 10px #808000, 0 0 15px #808000, 0 0 20px #808000;
        color: #ffffff;
    }
    50% {
        text-shadow: 0 0 10px #a0a040, 0 0 20px #a0a040, 0 0 30px #a0a040, 0 0 40px #a0a040;
        color: #ffffff;
    }
    100% {
        text-shadow: 0 0 5px #808000, 0 0 10px #808000, 0 0 15px #808000, 0 0 20px #808000;
        color: #ffffff;
    }
}

.blinking-text {
    font-size: 2rem;
    font-weight: bold;
    color: #ffffff;
    animation: glow 1s infinite alternate;
}

    """,
    unsafe_allow_html=True
)

# Your Streamlit app content with the title having blue light effect
    st.markdown('<div class="title">🚀 Welcome to BackTrack Brain!</div>', unsafe_allow_html=True)
#st.write("This is your application with the glowing title effect!")

    st.markdown(f"<p style='font-size: 24px; text-align: center; font-weight: bold; background-color: #000000; padding: 10px; border-radius: 10px;'>🎯 Choose Your Catogery : </p>", unsafe_allow_html=True)
    #st.markdown("<p class='big-title'> Welcome to the BackTrack Brain! </p>", unsafe_allow_html=True)
    st.markdown(f"<p class='instructions' style='margin-left: 50px;'>👋 Hello {st.session_state.username} the {st.session_state.avatar}! 💡 You get an answer. Guess the right question! Choose a category to start. 🎯</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1], gap='large')
    col4 = st.columns([1])[0]

    with col1:
        if st.button("🔬 Science", key="science"):
            start_game("Science")
    with col2:
        if st.button("📜 History", key="history"):
            start_game("History")
    with col3:
        if st.button("💻 Coding", key="coding"):
            st.session_state.category = "Coding"

    col4, col5, col6 = st.columns([1, 1, 1], gap='large')
    with col4:
        if st.button("📖 English", key="english"):
            start_game("English")
    with col5:
        if st.button("🎲 Random", key="random"):
            random_category = random.choice(list(datasets.keys()))
            start_game(random_category)
    with col6:
        if st.button("➗ Math", key="math"):
            start_game("Math")
    if st.session_state.category == "Coding":
        st.subheader("Select a Programming Language")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("C", key="c"):
                start_game("Coding", "C")
        with col2:
            if st.button("C++", key="cpp"):
                start_game("Coding", "C++")
        with col3:
            if st.button("Java", key="java"):
                start_game("Coding", "Java")
        with col4:
            if st.button("Python", key="python"):
                start_game("Coding", "Python")

# 🎮 Gameplay Screen
else:
    st.markdown(f"<p class='big-title'>📚 Category: {st.session_state.category}</p>", unsafe_allow_html=True)
    st.markdown(f"<p class='answer-box'>🎯 Answer: {st.session_state.current_answer}</p>", unsafe_allow_html=True)

    user_question = st.text_input("💡 Enter Your Question:")

  
    if st.button("✅ Submit", key="submit"):
    # Check if the user has already answered this question
        if "answered_questions" not in st.session_state:
            st.session_state.answered_questions = []  # Initialize list to track answered questions
    
    # Check if the current question has already been answered
        if user_question in st.session_state.answered_questions:
            st.warning("❌ You've already answered this question. Score will not be updated.")
        else:
        # Calculate the score based on the user's answer
            score = score_question(user_question, st.session_state.current_answer)
        
        # Only increase the score for relevant questions
            if score == 1:
                st.session_state.score += score  # Increment the score only if relevant
                st.balloons()
                st.success(f"🎉 Great job! That's relevant! (+1 point)")
            # Add the question to the list of answered questions
                st.session_state.answered_questions.append(user_question)
            
            # Play success sound
                st.markdown(load_audio("success.mp3"), unsafe_allow_html=True)
            else:
                st.warning(f"❌ Oops! Not quite relevant. (+0 points)")
            # Play failure sound
                st.markdown(load_audio("wav.mp3"), unsafe_allow_html=True)

    # Display the updated total score
        st.info(f"🏆 Total Score: {st.session_state.score}")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("➡ Next Question"):
            start_game(st.session_state.category, st.session_state.subcategory)
    with col2:
        if st.button("🔙 Back"):
            go_back()