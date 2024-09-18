from flask import Flask, render_template, request, jsonify
import re
import json

app = Flask(__name__, template_folder='templates')

with open('static/json/finalC.json', 'r') as json_file:
    reference_data = json.load(json_file)

def modify_words(text):  # modifies words so all of them are in the dictionary
    words = re.findall(r'\b\w+\b', text.lower().strip())
    filtered_words = [word for word in words if len(word) > 2]
    modified_words = []
    for word in filtered_words:
        modified_word = None
        for reference_word in reference_data:
            # Calculate the similarity ratio using Levenshtein distance
            similarity = ratio(word, reference_word)
            if similarity >= 0.8:  # Adjust the threshold as needed
                modified_word = reference_word
                break
        if not modified_word is None:
            modified_words.append(modified_word)  # we're just removing words that don't match to make it easier (needs to be fixed)
    return ' '.join(modified_words)

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/", methods=['POST'])
def upload_file():
    f = request.files['file']
    rawText = f.read().decode('utf-8')  # Assuming the file contains text data
    modText = modify_words(rawText)
    return jsonify({'rawText': rawText, 'modText': modText})

API_KEY = 'AIzaSyDoQgxx7bhnkDsY2gZV2joWYE_7D875dd0'
CX = '02b947281690f4e71'
import requests
from googleapiclient.discovery import build
from PIL import Image
from io import BytesIO

def generateimage(query):
    service = build("customsearch", "v1", developerKey=API_KEY)
    res = service.cse().list(q=query, cx=CX, searchType='image', num=1).execute()
    first_image_url = res['items'][0]['link']
    
    response = requests.get(first_image_url)
    img = Image.open(BytesIO(response.content))
    img.show()
    
    return first_image_url

@app.route('/generate_image', methods=['POST'])
def generate_image():
    print("function called")
    data = request.json
    query = data.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    image_url = generateimage(query)
    print(image_url)
    return jsonify({'image_url': image_url})

if __name__ == '__main__':
    app.run(port=5001)
