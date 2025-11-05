from flask import Flask, request, jsonify
from PIL import Image
from pix2tex.cli import LatexOCR
from flask_cors import CORS
import io

app = Flask(__name__)
CORS(app)  # allow requests from your standalone frontend

model = LatexOCR()

@app.route('/api/convert', methods=['POST'])
def convert_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    uploaded_image = request.files['image']
    image = Image.open(io.BytesIO(uploaded_image.read()))
    latex_text = model(image)

    return jsonify({"latex": latex_text})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
