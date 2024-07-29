from flask import Flask, request, jsonify
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from dotenv import load_dotenv

app = Flask(__name__)

EMAIL_SERVER = "smtp.gmail.com"
PORT = 587
load_dotenv()

sender_email = os.getenv("sender_email")
password_email = os.getenv("password_email")

def send_email(subject, name, receiver_email, response):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("EL-FI HOMES", sender_email))
    msg["To"] = receiver_email
    msg["BCC"] = sender_email

    response_text = (
        "Thank you for your positive response!" if response.lower() == "yes" else "We hope to hear from you soon!"
    )

    msg.set_content(
        f"""\
        Hi {name},
        We are excited to introduce our new product to you!
        We are reaching out to you because you showed interest in solar panels.
        {response_text}

        Best regards,
        Your Company Name
        """
    )

    msg.add_alternative(
        f"""\
    <html>
      <body>
        <p>Hi {name},</p>
        <p>We are excited to introduce our new product to you!</p>
        <p>We are reaching out to you because you showed interest in solar panels.</p>
        <p>{response_text}</p>
        <p>Best regards,</p>
        <p>Your Company Name</p>
      </body>
    </html>
    """,
        subtype="html",
    )

    with smtplib.SMTP(EMAIL_SERVER, PORT) as server:
        server.starttls()
        server.login(sender_email, password_email)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Email sent to {receiver_email}")

@app.route('/send-email', methods=['POST'])
def api_send_email():
    data = request.get_json()
    name = data.get("name")
    receiver_email = data.get("receiver_email")
    
    response = data.get("response")


    if not all([name, receiver_email, response]):
        return jsonify({"error": "Missing data"}), 400

    send_email(
        subject="Discover Our New Product!",
        name=name,
        receiver_email=receiver_email,
    
        response=response,
    )
    return jsonify({"message": "Email sent successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
