import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def extract_text_from_image(image_path):
    try:
        # Log the image path
        print(f"Extracting text from image: {image_path}")
        
        # Open the image file
        image = Image.open(image_path)
        
        # Log that the image was opened successfully
        print("Image opened successfully.")
        
        # Perform OCR using pytesseract
        text = pytesseract.image_to_string(image)
        
        # Log the extracted text
        print(f"Extracted text: {text}")
        
        return text
    except Exception as e:
        print(f"Error reading image: {e}")
        return None

def parse_receipt(text):
    items = {}
    tax = 0.0
    tip_and_service_charge = 0.0
    lines = text.split('\n')
    buffer = ""

    for line in lines:
        if '$' in line:
            if buffer:
                line = buffer + " " + line
                buffer = ""
            parts = line.rsplit('$', 1)
            item_name = parts[0].strip().lower()
            item_price = parts[1].strip()
            if "tax" in item_name:
                tax = float(item_price)
                continue
            elif "tip" in item_name or "service" in item_name:
                tip_and_service_charge += float(item_price)
                continue
            elif "subtotal" in item_name or "total" in item_name:
                continue
            try:
                item_price = float(item_price)
                items[item_name] = item_price
            except ValueError:
                continue
        else:
            buffer = line.strip()
    return items, tax, tip_and_service_charge

def calculate_owed_amount(dishes_per_person, items, tax, tip_and_service_charge, payer_name):
    amounts_owed = {}

    for person in dishes_per_person:
        amounts_owed[person] = 0.0

    total_items_cost = sum(float(price) for price in items.values())

    for dish, price in items.items():
        people_who_had_dish = [person for person in dishes_per_person if dish in dishes_per_person[person]]
        share = float(price) / len(people_who_had_dish)
        for person in people_who_had_dish:
            amounts_owed[person] += share

    total_extra = float(tax) + float(tip_and_service_charge)
    for person in amounts_owed:
        person_share = amounts_owed[person] / total_items_cost
        amounts_owed[person] += person_share * total_extra

    return amounts_owed

@app.route('/upload', methods=['POST'])
def upload_file():
    print("Received request:", request)
    if 'file' not in request.files:
        print("No file part in the request")
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        print("No selected file")
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        text = extract_text_from_image(filepath)
        if text is None:
            return jsonify({'error': 'Failed to extract text from image'}), 500
        items, tax, tip_and_service_charge = parse_receipt(text)
        return jsonify({'items': items, 'tax': tax, 'tip': tip_and_service_charge})

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    items = data['items']
    tax = data['tax']
    tip = data['tip']
    payer_name = data['payer_name']
    dishes_per_person = data['dishes_per_person']

    amounts_owed = calculate_owed_amount(dishes_per_person, items, tax, tip, payer_name)

    return jsonify(amounts_owed)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')