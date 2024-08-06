from flask import Flask, request, jsonify
import os
import smtplib
import logging
from email.message import EmailMessage
from email.utils import formataddr
from dotenv import load_dotenv
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.DEBUG)

EMAIL_SERVER = "smtp.gmail.com"
PORT = 587
load_dotenv()

sender_email = os.getenv("SENDER_EMAIL")
password_email = os.getenv("PASSWORD_EMAIL")

# Log the loaded environment variables for debugging
logging.debug(f"SENDER_EMAIL: {sender_email}")
logging.debug(f"PASSWORD_EMAIL: {password_email}")

def send_email(subject, name, receiver_email, response):
    logging.info(f"Attempting to send email to {receiver_email}")
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

    try:
        with smtplib.SMTP(EMAIL_SERVER, PORT, timeout=30) as server:
            server.starttls()
            server.login(sender_email, password_email)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        logging.info(f"Email sent successfully to {receiver_email}")
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}", exc_info=True)
        raise

@app.route('/send-email', methods=['POST'])
def api_send_email():
    logging.info("Received request to /send-email")
    try:
        data = request.get_json()
        logging.debug(f"Received data: {data}")
        
        name = data.get("name")
        receiver_email = data.get("receiver_email")
        response = data.get("response")

        if not all([name, receiver_email, response]):
            logging.warning("Missing data in request")
            return jsonify({"error": "Missing data"}), 400

        send_email(
            subject="Discover Our New Product!",
            name=name,
            receiver_email=receiver_email,
            response=response,
        )
        return jsonify({"message": "Email sent successfully"}), 200
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/test-smtp', methods=['GET'])
def test_smtp():
    logging.info("Testing SMTP connection")
    try:
        with smtplib.SMTP(EMAIL_SERVER, PORT, timeout=30) as server:
            server.starttls()
            server.login(sender_email, password_email)
        return "SMTP connection successful", 200
    except Exception as e:
        logging.error(f"SMTP connection failed: {str(e)}", exc_info=True)
        return f"SMTP connection failed: {str(e)}", 500

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    logging.info("Starting Flask application")
    if not all([sender_email, password_email]):
        logging.error("Missing email credentials in environment variables")
    app.run(debug=True)
