import os
import fitz  # PyMuPDF
import requests
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Configuration
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "txt"}
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join([page.get_text("text") for page in doc])
    doc.close()
    return text

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        
        text_content = extract_text_from_pdf(file_path)
        
        return jsonify({"message": "File uploaded successfully", "text": text_content})
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/query", methods=["POST"])
def query_chatbot():
    data = request.json
    query_text = data.get("query", "")
    document_text = data.get("document_text", "")
    
    if not query_text or not document_text:
        return jsonify({"error": "Missing query or document text"}), 400
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": "You are an AI assistant helping to answer questions about a specific document."},
            {"role": "user", "content": f"Document: {document_text}\n\nQuestion: {query_text}\n\nAnswer the question based strictly on the information in the document."}
        ]
    }
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            json=payload, 
            headers=headers
        )
        
        response.raise_for_status()
        return jsonify(response.json())
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)