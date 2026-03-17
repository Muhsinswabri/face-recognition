import google.generativeai as genai
import sys
import PIL.Image

# Use the environment variable if available, otherwise just try
genai.configure() 

model = genai.GenerativeModel('gemini-2.5-flash')

images = [
    r"C:\Users\hp\.gemini\antigravity\brain\24b6da2d-cf72-4325-a8ad-4ff50931ea43\media__1773123795905.png",
    r"C:\Users\hp\.gemini\antigravity\brain\24b6da2d-cf72-4325-a8ad-4ff50931ea43\media__1773123795940.png",
    r"C:\Users\hp\.gemini\antigravity\brain\24b6da2d-cf72-4325-a8ad-4ff50931ea43\media__1773123795974.png"
]

prompt = "Extract all text from this screenshot. Specifically look for Appwrite Database IDs, Collection IDs, Attributes list, and any document lists to see if my schema 'student_id', 'name', 'major', 'year' match what is on screen."

for img_path in images:
    print(f"--- Analyzing {img_path} ---")
    try:
        img = PIL.Image.open(img_path)
        response = model.generate_content([prompt, img])
        print(response.text)
    except Exception as e:
        print("Error:", e)
