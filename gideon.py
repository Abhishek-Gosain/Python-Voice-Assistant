import os
import sys
import random
import datetime as dt
import webbrowser
import subprocess
from threading import Thread

import pyttsx3
import speech_recognition as sr
import wikipedia
import wolframalpha
from tkinter import Tk, LabelFrame, Message, Button, StringVar

from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

WOLFRAM_APP_ID = os.getenv("WOLFRAMALPHA_APP_ID")

MUSIC_FOLDER = os.getenv("MUSIC_FOLDER", "")
VIDEO_FOLDER = os.getenv("VIDEO_FOLDER", "")

if WOLFRAM_APP_ID:
    wolfram_client = wolframalpha.Client(WOLFRAM_APP_ID)
else:
    wolfram_client = None


# ============================================================
# APPLICATION WINDOW
# ============================================================

win = Tk()
win.title("Gideon AI")
win.geometry("380x585")
win.config(background="black")


usertext = StringVar()
comtext = StringVar()


# ============================================================
# TEXT-TO-SPEECH ENGINE
# ============================================================

try:
    engine = pyttsx3.init("sapi5")

    voices = engine.getProperty("voices")

    if len(voices) > 1:
        engine.setProperty("voice", voices[1].id)

except Exception as error:
    print(f"Text-to-speech initialization error: {error}")
    engine = None


# ============================================================
# GUI FUNCTIONS
# ============================================================

def printo(message):
    """Update the assistant message displayed in the GUI."""
    comtext.set(message)


def speak(message):
    """Display and speak an assistant response."""
    printo(message)

    if engine:
        try:
            engine.say(message)
            engine.runAndWait()
        except Exception as error:
            print(f"Speech error: {error}")


def exit_application():
    """Close the application."""
    try:
        win.destroy()
    except Exception:
        pass

    sys.exit(0)


def new_gui():
    """Display the available voice commands."""

    root = Tk()
    root.geometry("493x473")
    root.title("Commands List")

    commands = """
    Available Commands:

    1) Search Google <keyword>
       Example: search google Python

    2) Search YouTube <keyword>
       Example: search YouTube AI

    3) Open Google
       Opens Google in the browser.

    4) Open YouTube
       Opens YouTube in the browser.

    5) Wikipedia <topic>
       Searches Wikipedia for information.

    6) Play Music
       Plays a random audio file.

    7) Play Video
       Plays a random video file.

    8) Go Offline / Bye / Stop
       Closes the application.

    9) Shutdown
       Shuts down Windows.
    """

    frame = LabelFrame(
        root,
        text="Commands",
        font=("Arial", 12, "bold"),
        highlightthickness=3
    )

    frame.pack(fill="both", expand="yes")

    message = Message(
        frame,
        text=commands,
        bg="black",
        fg="#7adb1e"
    )

    message.config(font=("Arial", 10, "bold"))
    message.pack(fill="both", expand=True)

    Button(
        root,
        text="EXIT",
        font=("Arial", 11, "bold"),
        bg="red",
        fg="white",
        borderwidth=5,
        command=root.destroy
    ).pack(fill="x")

    root.mainloop()


# ============================================================
# VOICE RECOGNITION
# ============================================================

def create_recognizer():
    """Create and configure the speech recognizer."""

    recognizer = sr.Recognizer()

    recognizer.energy_threshold = 500
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1

    return recognizer


def get_voice_input(prompt=None):
    """
    Listen to the microphone and convert speech to text.

    Returns:
        str: Recognized speech or an empty string if recognition fails.
    """

    recognizer = create_recognizer()

    try:
        with sr.Microphone() as source:

            if prompt:
                speak(prompt)

            printo("Listening...")

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.3
            )

            audio = recognizer.listen(
                source,
                timeout=8,
                phrase_time_limit=10
            )

        printo("Recognizing...")

        query = recognizer.recognize_google(
            audio,
            language="en-IN"
        )

        usertext.set(f"User: {query}")

        return query.lower().strip()

    except sr.WaitTimeoutError:
        speak("I didn't hear anything. Please try again.")
        return ""

    except sr.UnknownValueError:
        speak("Sorry, I couldn't understand that.")
        return ""

    except sr.RequestError:
        speak("The speech recognition service is unavailable.")
        return ""

    except Exception as error:
        print(f"Voice recognition error: {error}")
        speak("Something went wrong while listening.")
        return ""


# ============================================================
# USER NAME
# ============================================================

def get_user_name():
    """Ask the user for their name."""

    while True:

        name = get_voice_input("What is your name?")

        if name:
            return name

        speak("Please tell me your name again.")


def wish_user(name):
    """Give a time-based greeting."""

    hour = dt.datetime.now().hour

    if 0 <= hour < 12:
        greeting = "Good morning"

    elif 12 <= hour < 18:
        greeting = "Good afternoon"

    else:
        greeting = "Good evening"

    speak(f"{greeting}, {name}.")
    speak(f"Hello {name}. How can I help you?")


# ============================================================
# WEB SEARCH
# ============================================================

def google_search(query):
    """Search Google using the provided query."""

    keyword = query.replace("search google", "", 1).strip()

    if not keyword:
        speak("What would you like me to search for?")
        return

    speak(f"Searching Google for {keyword}.")

    search_url = (
        "https://www.google.com/search?q="
        + keyword.replace(" ", "+")
    )

    webbrowser.open(search_url)


def youtube_search(query):
    """Search YouTube using the provided query."""

    keyword = query.replace("search youtube", "", 1).strip()

    if not keyword:
        speak("What would you like me to search for?")
        return

    speak(f"Searching YouTube for {keyword}.")

    search_url = (
        "https://www.youtube.com/results?search_query="
        + keyword.replace(" ", "+")
    )

    webbrowser.open(search_url)


# ============================================================
# WIKIPEDIA
# ============================================================

def wikipedia_search(query):
    """Search Wikipedia and read a short summary."""

    topic = query.replace("wikipedia", "", 1).strip()

    if not topic:
        speak("Please tell me what you want to search on Wikipedia.")
        return

    try:

        speak("Searching Wikipedia.")

        result = wikipedia.summary(
            topic,
            sentences=3,
            auto_suggest=True
        )

        printo(result)
        speak("According to Wikipedia.")
        speak(result)

    except wikipedia.exceptions.DisambiguationError as error:

        options = error.options[:3]

        speak(
            "The topic has multiple results. "
            "Please be more specific."
        )

        printo("Possible results:\n" + "\n".join(options))

    except wikipedia.exceptions.PageError:

        speak("I couldn't find that topic on Wikipedia.")

    except Exception as error:

        print(f"Wikipedia error: {error}")
        speak("There was an error while searching Wikipedia.")


# ============================================================
# MUSIC
# ============================================================

def play_music():
    """Play a random music file from the configured folder."""

    if not MUSIC_FOLDER:
        speak(
            "Music folder is not configured. "
            "Please update the MUSIC_FOLDER setting."
        )
        return

    if not os.path.isdir(MUSIC_FOLDER):
        speak("The configured music folder does not exist.")
        return

    files = [
        file
        for file in os.listdir(MUSIC_FOLDER)
        if file.lower().endswith((".mp3", ".wav", ".m4a"))
    ]

    if not files:
        speak("No music files were found.")
        return

    selected_file = random.choice(files)
    file_path = os.path.join(MUSIC_FOLDER, selected_file)

    try:
        os.startfile(file_path)
        speak("Playing music. Enjoy!")

    except Exception as error:
        print(f"Music playback error: {error}")
        speak("I couldn't play the music file.")


# ============================================================
# VIDEO
# ============================================================

def play_video():
    """Play a random video file from the configured folder."""

    if not VIDEO_FOLDER:
        speak(
            "Video folder is not configured. "
            "Please update the VIDEO_FOLDER setting."
        )
        return

    if not os.path.isdir(VIDEO_FOLDER):
        speak("The configured video folder does not exist.")
        return

    files = [
        file
        for file in os.listdir(VIDEO_FOLDER)
        if file.lower().endswith(
            (".mp4", ".avi", ".mkv", ".mov")
        )
    ]

    if not files:
        speak("No video files were found.")
        return

    selected_file = random.choice(files)
    file_path = os.path.join(VIDEO_FOLDER, selected_file)

    try:
        os.startfile(file_path)
        speak("Playing video. Enjoy!")

    except Exception as error:
        print(f"Video playback error: {error}")
        speak("I couldn't play the video file.")


# ============================================================
# WOLFRAMALPHA
# ============================================================

def ask_wolframalpha(query):
    """Send a general question to WolframAlpha."""

    if not wolfram_client:

        speak(
            "WolframAlpha is not configured. "
            "Please add your API key to the environment settings."
        )

        return

    try:

        speak("Searching for an answer. Please wait.")

        result = wolfram_client.query(query)

        answer = next(result.results).text

        if answer:
            speak(answer)

        else:
            speak("I couldn't find an answer.")

    except StopIteration:

        speak("I couldn't find a suitable answer.")

    except Exception as error:

        print(f"WolframAlpha error: {error}")

        speak(
            "I couldn't find an answer for that question."
        )


# ============================================================
# SYSTEM COMMANDS
# ============================================================

def shutdown_system():
    """Shutdown the Windows operating system."""

    speak("Okay. Shutting down the system.")

    try:
        os.system("shutdown /s /t 5")

    except Exception as error:
        print(f"Shutdown error: {error}")
        speak("I couldn't shut down the system.")


# ============================================================
# COMMAND PROCESSING
# ============================================================

def process_command(query, name):
    """Process a recognized voice command."""

    if not query:
        return True

    # Google search
    if query.startswith("search google"):
        google_search(query)

    # YouTube search
    elif query.startswith("search youtube"):
        youtube_search(query)

    # Wikipedia
    elif query.startswith("wikipedia"):
        wikipedia_search(query)

    # Open YouTube
    elif "open youtube" in query:
        speak("Opening YouTube.")
        webbrowser.open("https://www.youtube.com")

    # Open Google
    elif "open google" in query:
        speak("Opening Google.")
        webbrowser.open("https://www.google.com")

    # Music
    elif "play music" in query:
        play_music()

    # Video
    elif "play video" in query:
        play_video()

    # Greetings
    elif query == "hello" or "hello" in query:
        speak(f"Hello {name}.")

    elif "how are you" in query or "what's up" in query:
        responses = [
            "I am doing great!",
            "I am fine and ready to help.",
            "Everything is working well.",
            "I am doing good. How can I help?"
        ]

        speak(random.choice(responses))

    # Exit commands
    elif (
        "go offline" in query
        or query == "bye"
        or "stop" in query
        or "nothing" in query
        or "abort" in query
    ):

        speak(f"Goodbye {name}. Have a great day.")
        return False

    # Shutdown
    elif "shutdown" in query:
        shutdown_system()
        return False

    # General query
    else:
        ask_wolframalpha(query)

    return True


# ============================================================
# APPLICATION FLOW
# ============================================================

def start_assistant():
    """Start the assistant and greet the user."""

    try:

        name = get_user_name()

        wish_user(name)

        return name

    except Exception as error:

        print(f"Assistant startup error: {error}")
        speak("I couldn't start the assistant.")
        return None


def run_assistant():
    """Continuously listen for and process user commands."""

    name = start_assistant()

    if not name:
        return

    while True:

        query = get_voice_input()

        if not query:
            continue

        should_continue = process_command(
            query,
            name
        )

        if not should_continue:
            break


# ============================================================
# GUI
# ============================================================

comtext.set(
    "Hello!\n"
    "I am your Personal Assistant - Gideon AI\n\n"
    "Click Start to begin."
)

usertext.set("")


Button(
    win,
    text="Start!",
    font=("Arial", 11, "bold"),
    bg="black",
    fg="#7adb1e",
    borderwidth=5,
    command=lambda: Thread(
        target=run_assistant,
        daemon=True
    ).start()
).pack(fill="x")


Button(
    win,
    text="Command List",
    font=("Arial", 11, "bold"),
    bg="black",
    fg="#7adb1e",
    borderwidth=5,
    command=new_gui
).pack(fill="x")


Button(
    win,
    text="EXIT",
    font=("Arial", 11, "bold"),
    bg="red",
    fg="white",
    borderwidth=5,
    command=exit_application
).pack(fill="x")


# Assistant output frame
compframe = LabelFrame(
    win,
    text="Gideon AI",
    font=("Arial", 10, "bold"),
    highlightthickness=2
)

compframe.pack(
    fill="both",
    expand=True
)


left2 = Message(
    compframe,
    textvariable=comtext,
    bg="#7adb1e",
    fg="black",
    justify="left"
)

left2.config(
    font=("Arial", 12, "bold")
)

left2.pack(
    fill="both",
    expand=True
)


# User output frame
userframe = LabelFrame(
    win,
    text="User",
    font=("Arial", 10, "bold"),
    highlightthickness=2
)

userframe.pack(
    fill="both",
    expand=True
)


left1 = Message(
    userframe,
    textvariable=usertext,
    bg="black",
    fg="#7adb1e",
    justify="left"
)

left1.config(
    font=("Arial", 12, "bold")
)

left1.pack(
    fill="both",
    expand=True
)


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    win.mainloop()
