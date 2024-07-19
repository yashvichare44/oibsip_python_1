import tkinter as tk
from PIL import Image, ImageTk
import speech_recognition as sr
import pyttsx3
import datetime
import wikipedia
import webbrowser
import os
import time
import subprocess
import threading
from googletrans import Translator
from geopy.geocoders import Nominatim
from dateutil import parser

print('Loading your AI personal assistant - gems')

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

reminders = []
lock = threading.Lock()
geolocator = Nominatim(user_agent="your_app_name")
translator = Translator()

class VoiceAssistantGUI:
    def _init_(self, master, image_path):
        self.master = master
        self.master.title("Voice Assistant")
        self.master.geometry("800x600")  # Set the initial size of the window

        # Load and resize the background image to fit the window
        original_image = Image.open(image_path)
        resized_image = original_image.resize((800, 600), Image.BICUBIC)
        self.photo_image = ImageTk.PhotoImage(resized_image)

        self.image_label = tk.Label(master, image=self.photo_image)
        self.image_label.place(x=400, y=300, anchor="center")

        # Decorate the "Voice Assistant" text
        self.label = tk.Label(master, text="Voice Assistant", font=("Segoe UI", 20, "italic"), fg="black", bd=5, relief="flat")
        self.label.place(x=400, y=100, anchor="center")

        self.output_box = tk.Text(master, height=5, width=60, font=("Helvetica", 12), bg="lightgray")
        self.output_box.place(x=400, y=300, anchor="center")
        
        self.scrollbar = tk.Scrollbar(master, command=self.output_box.yview)
        self.scrollbar.place(in_=self.output_box, relx=1.0, relheight=1.0, bordermode="outside")
        self.output_box.config(yscrollcommand=self.scrollbar.set)

        self.listen_button = CircularButton(master, self.listen, radius=30)
        self.listen_button.place(x=350, y=420, anchor="center")

        self.exit_button = tk.Button(master, text="Exit", command=self.master.destroy, font=("Helvetica", 12), bg="#333", fg="white")
        self.exit_button.place(x=450, y=400)

    def listen(self, event=None):
        recognizer = sr.Recognizer()

        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            self.process_input(text)
        except sr.UnknownValueError:
            message = "Sorry, I could not understand your speech."
            print("Input: " + message)  # Print message in the terminal
            self.output_box.insert(tk.END, "Input: " + message + "\n\n")
        except sr.RequestError as e:
            message = f"Error with the speech recognition service; {e}"
            print("Input: " + message)  # Print message in the terminal
            self.output_box.insert(tk.END, "Input: " + message + "\n\n")

    def speak(self, text):
        global engine
        if not engine._inLoop:
            print("Output: " + text)  # Print message in the terminal
            self.output_box.insert(tk.END, "Output: " + text + "\n")
            engine.say(text)
            engine.runAndWait()

    def check_reminders(self):
        global reminders, lock

        while True:
            now = datetime.datetime.now()

            with lock:
                for reminder in reminders[:]:  # Iterate over a copy of the reminders to safely remove expired ones
                    reminder_time = reminder['time']

                    if now >= reminder_time:
                        self.speak(f"Reminder: {reminder['text']}")
                        reminders.remove(reminder)

            time.sleep(1)  # Pause for 1 second before
    def translate(self, text, target_language):
        translated_text = translator.translate(text, dest=target_language)
        return translated_text.text
    
    def process_input(self, statement):
        statement = statement.lower()
        print("Input: " + statement)
        self.output_box.delete('1.0', tk.END)  # Clear previous command
        self.output_box.insert(tk.END, "Input: " + statement + "\n")
        

        if "goodbye" in statement or "ok bye" in statement or "stop" in statement:
            self.speak('Your personal assistant gems is shutting down. Goodbye!')
            print('Your personal assistant gems is shutting down. Goodbye!')
            self.master.destroy()
        elif 'wikipedia' in statement:
            self.speak('Searching Wikipedia...')
            statement = statement.replace("wikipedia", "")
            results = wikipedia.summary(statement, sentences=3)
            self.speak("According to Wikipedia")
            print("Output: " + results)  # Print message in the terminal
            self.speak(results)
        elif 'open youtube' in statement:
            webbrowser.open_new_tab("https://www.youtube.com")
            self.speak("YouTube is open now")
        elif 'open google' in statement:
            webbrowser.open_new_tab("https://www.google.com")
            self.speak("Google Chrome is open now")
        elif 'my location' in statement or 'where am i' in statement:
            location = self.get_location()
            if location:
                self.speak(f"You are currently in {location.address}")
            else:
                self.speak("Sorry, I couldn't determine your location at the moment.")
        elif 'time' in statement:
            strTime = datetime.datetime.now().strftime("%H:%M:%S")
            self.speak(f"The time is {strTime}")
        elif 'who are you' in statement or 'what can you do' in statement:
            self.speak('I am Gems, your AI assistant. I can perform tasks like opening YouTube, Google Chrome, Gmail, searching Wikipedia, and more.')
        elif "who made you" in statement or "who created you" in statement or "who discovered you" in statement:
            self.speak("I was built by Yash Vichare")
        elif "open stack overflow" in statement:
            webbrowser.open_new_tab("https://stackoverflow.com/login")
            self.speak("Here is Stack Overflow")
        elif 'news' in statement:
            webbrowser.open_new_tab("https://timesofindia.indiatimes.com/home/headlines")
            self.speak('Here are some headlines from the Times of India. Happy reading!')
        elif 'search' in statement:
            statement = statement.replace("search", "")
            webbrowser.open_new_tab(statement)
        elif "log off" in statement or "sign out" in statement:
            self.speak("OK, your PC will log off in 10 seconds. Make sure you exit from all applications.")
            subprocess.call(["shutdown", "/l"])
        elif 'set a reminder' in statement or 'remind me' in statement:
            self.set_reminder()
        elif 'check reminders' in statement or 'what are my reminders' in statement:
            self.check_reminders()
        elif 'translate' in statement:
            self.speak("Sure, what would you like to translate?")
            text_to_translate = self.take_command()
            self.speak("To which language would you like to translate it?")
            target_language = self.take_command().lower()

            try:
                translated_text = self.translate(text_to_translate, target_language)
                self.speak(f"The translation is: {translated_text}")

            except Exception as e:
                self.speak("Sorry, I couldn't perform the translation at the moment.")

        self.output_box.see(tk.END)  # Scroll to the end of the text box to show the latest output

    def set_reminder(self):
        global reminders, lock

        self.speak("Sure, what is the reminder for?")
        reminder_text = self.take_command()
        self.speak("When should I remind you?")
        reminder_time = self.take_command()

        try:
            if 'in' in reminder_time:
                # Handling expressions like "in X seconds"
                seconds_offset = int(reminder_time.split()[-2])
                reminder_datetime = datetime.datetime.now() + datetime.timedelta(seconds=seconds_offset)
            else:
                # Parse the time normally
                reminder_datetime = parser.parse(reminder_time)

            now = datetime.datetime.now()

            # Calculate the time difference
            time_difference = (reminder_datetime - now).total_seconds()

            if time_difference > 0:
                with lock:
                    reminders.append({'text': reminder_text, 'time': reminder_datetime})
                self.speak(f"Reminder set for {reminder_time}")
                self.output_box.insert(tk.END, f"Output: Reminder set for {reminder_time}\n")
            else:
                self.speak("I'm sorry, but that time has already passed.")
                self.output_box.insert(tk.END, "Output: I'm sorry, but that time has already passed.\n")

        except ValueError as ve:
            print(f"Error setting reminder: {ve}")
            self.speak("Sorry, I didn't understand the time. Please try again.")
            self.output_box.insert(tk.END, "Output: Sorry, I didn't understand the time. Please try again.\n")

    def take_command(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source)
            print("Listening...")
            audio = r.listen(source)

        try:
            statement = r.recognize_google(audio, language='en-in')
            print("User said: " + statement)  # Print message in the terminal
            return statement.lower()

        except Exception as e:
            self.speak("Pardon me, please say that again")
            return "None"

class CircularButton(tk.Canvas):
    def _init_(self, master=None, command=None, radius=30, **kwargs):
        super()._init_(master, width=2 * radius, height=2 * radius, **kwargs)
        self.bind("<Button-1>", lambda event: command())
        self.configure(highlightthickness=0)
        self.configure(bg="SystemHighlight")
        self.create_oval(0, 0, 2 * radius, 2 * radius, fill="#0599fc", outline="#0599fc")
        self.create_text(radius, radius, text="🎤", font=("Helvetica", 24), fill="white")

if _name_ == "_main_":
    root = tk.Tk()

    # Specify the path to your image
    image_path = "guipic.jpg"
    app = VoiceAssistantGUI(root, image_path)

    reminder_thread = threading.Thread(target=app.check_reminders, daemon=True)
    reminder_thread.start()

    root.mainloop()