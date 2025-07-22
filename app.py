from flask import Flask, render_template, request
import google.generativeai as genai
import os
import pdfplumber  # Better PDF text extraction

app = Flask(__name__)

# Load Gemini API key
os.environ["GOOGLE_API_KEY"] = "your api key"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash")

# ========== Functions ==========

def predict_fake_or_real_email_content(text):
    prompt = f"""
You are an expert in cybersecurity email analysis. Classify the message strictly as one of the following:
- Real/Legitimate
- Scam/Fake

Here are some examples:

---
Message: "Your Amazon order has been shipped. Track your package at amazon.com"
Classification: Real/Legitimate

---
Message: "Congratulations! You've won a lottery of ₹10,00,000. Click here to claim your prize: bit.ly/claim-now"
Classification: Scam/Fake

---
Message: "Your electricity bill is due. Pay securely at tneb.gov.in"
Classification: Real/Legitimate

---
Message: "Dear user, your account has been suspended. Reactivate here: suspicious-link.net"
Classification: Scam/Fake

---

Now classify this message:

\"\"\"{text}\"\"\"

Respond ONLY with one of:
- Real/Legitimate
- Scam/Fake
"""
    try:
        response = model.generate_content(prompt)
        result = response.text.strip().splitlines()[0].strip()
        if "Real" in result:
            return "Real/Legitimate"
        elif "Scam" in result:
            return "Scam/Fake"
        else:
            return "Unclear classification: " + result
    except Exception as e:
        return f"Error: {str(e)}"

# ✅ Unchanged
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
        try:
            with pdfplumber.open(file) as pdf:
                extracted_text = " ".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as e:
            return render_template("index.html", message=f"PDF error: {str(e)}")
    elif file.filename.endswith('.txt'):
        extracted_text = file.read().decode("utf-8")
    else:
        return render_template("index.html", message="Invalid file type. Upload PDF or TXT.")

    if not extracted_text.strip():
        return render_template("index.html", message="File is empty or unreadable.")

    print("Extracted Text:\n", extracted_text)  # Optional debug

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
