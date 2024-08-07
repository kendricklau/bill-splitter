import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def extract_text_from_image(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
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
            # Check for tax, tip, and service charges
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

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        text = extract_text_from_image(filepath)
        if text:
            items, tax, tip_and_service_charge = parse_receipt(text)
            return jsonify({'items': items, 'tax': tax, 'tip': tip_and_service_charge})
        else:
            return jsonify({'error': 'Failed to extract text from image', 'filepath': request.files['file']}), 500

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

def calculate_owed_amount(dishes_per_person, items, tax, tip, payer_name):
    amounts_owed = {}

    # Initialize owed amounts to zero
    for person in dishes_per_person:
        amounts_owed[person] = 0.0

    total_items_cost = sum(float(price) for price in items.values())

    # Calculate each person's share for each dish
    for dish, price in items.items():
        people_who_had_dish = [person for person in dishes_per_person if dish in dishes_per_person[person]]
        share = float(price) / len(people_who_had_dish)
        for person in people_who_had_dish:
            amounts_owed[person] += share

    # Calculate the total tax and tip share for each person
    total_extra = float(tax) + float(tip)
    for person in amounts_owed:
        person_share = amounts_owed[person] / total_items_cost
        amounts_owed[person] += person_share * total_extra

    return amounts_owed

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')