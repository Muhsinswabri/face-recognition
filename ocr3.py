import requests
import json

api_key = 'K81896172688957' # Public API key for ocr.space
images = [
    r"C:\Users\hp\.gemini\antigravity\brain\24b6da2d-cf72-4325-a8ad-4ff50931ea43\media__1773123795974.png"
]

for img in images:
    print(f"--- {img} ---")
    with open(img, 'rb') as f:
        r = requests.post(
            'https://api.ocr.space/parse/image',
            files={img: f},
            data={'apikey': api_key, 'language': 'eng'}
        )
    print(r.json().get('ParsedResults', [{}])[0].get('ParsedText', 'No text found'))
