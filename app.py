from flask import Flask, render_template, request
import google.generativeai as genai
import os
import PyPDF2

app = Flask(__name__)

# Load your Gemini API Key
os.environ["GOOGLE_API_KEY"] = "your api key"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash")

# ========== Functions ==========

def predict_fake_or_real_email_content(text):
    prompt = f"""
    You are an expert in identifying scam messages. Analyze the text below and classify it as:
    - Real/Legitimate
    - Scam/Fake

    Text: {text}
    Return only the classification message.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def url_detection(url):
    prompt = f"""
    Classify the URL as:
    - benign
    - phishing
    - malware
    - defacement

    URL: {url}
    Return only the one class in lowercase.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip().lower()
    except Exception:
        return "unknown"

# ========== Routes ==========

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/scam/', methods=['POST'])
def detect_scam():
    file = request.files.get('file')
    if not file:
        return render_template("index.html", message="No file uploaded.")

    extracted_text = ""
    if file.filename.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(file)
        extracted_text = " ".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    elif file.filename.endswith('.txt'):
        extracted_text = file.read().decode("utf-8")
    else:
        return render_template("index.html", message="Invalid file type.")

    if not extracted_text.strip():
        return render_template("index.html", message="File is empty.")

    message = predict_fake_or_real_email_content(extracted_text)
    return render_template("index.html", message=message)

@app.route('/predict', methods=['POST'])
def predict_url():
    url = request.form.get('url', '').strip()
    if not url.startswith(("http://", "https://")):
        return render_template("index.html", message="URL must start with http:// or https://", input_url=url)

    classification = url_detection(url)
    return render_template("index.html", input_url=url, predicted_class=classification)

if __name__ == '__main__':
    app.run(debug=True)
