import os
import sys
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def extract_text_from_image(image_path):
    try:
        print(f"Extracting text from image: {image_path}")
        sys.stdout.flush()
        image = Image.open(image_path)
        print("Image opened successfully.")
        sys.stdout.flush()
        
        # Log the image format and size
        print(f"Image format: {image.format}, size: {image.size}")
        sys.stdout.flush()
        
        # Convert image to a supported format (e.g., JPEG)
        if image.format not in ['JPEG', 'JPG', 'PNG']:
            image = image.convert('RGB')
            image_path = image_path + '.jpg'
            image.save(image_path, 'JPEG')
            print(f"Image converted to JPEG: {image_path}")
            sys.stdout.flush()
        
        text = pytesseract.image_to_string(image)
        print(f"Extracted text: {text}")
        sys.stdout.flush()
        return text
    except Exception as e:
        print(f"Error reading image: {e}")
        sys.stdout.flush()
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

def calculate_owed_amount(dishes_per_person, items, tax, tip_and_service_charge):
    amounts_owed = {}
    breakdown = {}

    total_items_cost = sum(float(price) for price in items.values())

    for person in dishes_per_person:
        amounts_owed[person] = 0.0
        breakdown[person] = {
            'total': 0.0,
            'dishes': [],
            'tax': 0.0,
            'tip': 0.0
        }

    for dish, price in items.items():
        people_who_had_dish = [person for person in dishes_per_person if dish in dishes_per_person[person]]
        share = float(price) / len(people_who_had_dish)
        for person in people_who_had_dish:
            amounts_owed[person] += share
            breakdown[person]['dishes'].append({'name': dish, 'amount': share})

    total_extra = float(tax) + float(tip_and_service_charge)
    for person in amounts_owed:
        person_share = amounts_owed[person] / total_items_cost
        tax_share = person_share * float(tax)
        tip_share = person_share * float(tip_and_service_charge)
        amounts_owed[person] += tax_share + tip_share
        breakdown[person]['total'] = amounts_owed[person]
        breakdown[person]['tax'] = tax_share
        breakdown[person]['tip'] = tip_share

    return breakdown

@app.route('/upload', methods=['POST'])
def upload_file():
    print("Received request:", request)
    sys.stdout.flush()
    if 'file' not in request.files:
        print("No file part in the request")
        sys.stdout.flush()
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        print("No selected file")
        sys.stdout.flush()
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Ensure the uploads directory exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
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
    tax = data.get('tax', 0.0)
    tip = data.get('tip', 0.0)
    dishes_per_person = data['dishes_per_person']

    amounts_owed = calculate_owed_amount(dishes_per_person, items, tax, tip)

    return jsonify(amounts_owed)

@app.route('/check-tesseract', methods=['GET'])
def check_tesseract():
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        return jsonify({'tesseract_version': result.stdout})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')