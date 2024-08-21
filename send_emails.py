from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import smtplib
import logging
from email.message import EmailMessage
from email.utils import formataddr
from dotenv import load_dotenv

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

EMAIL_SERVER = "smtp-mail.outlook.com"
PORT = 587
load_dotenv()

sender_email = os.getenv("SENDER_EMAIL")
password_email = os.getenv("PASSWORD_EMAIL")

# Log the loaded environment variables for debugging
logging.debug(f"SENDER_EMAIL: {sender_email}")
# Logging password is generally not recommended
# logging.debug(f"PASSWORD_EMAIL: {password_email}")

if not all([sender_email, password_email]):
    logging.error("Missing email credentials in environment variables")
    raise RuntimeError("Email credentials not configured properly")

def send_email(subject: str, name: str, receiver_email: str, response: str):
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
        with smtplib.SMTP(EMAIL_SERVER, PORT, timeout=10) as server:
            server.starttls()
            server.login(sender_email, password_email)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        logging.info(f"Email sent successfully to {receiver_email}")
    except smtplib.SMTPException as e:
        logging.error(f"Failed to send email: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send email")

@app.post('/send-email')
async def api_send_email(request: Request):
    logging.info("Received request to /send-email")
    try:
        data = await request.json()
        logging.debug(f"Received data: {data}")
        
        name = data.get("name")
        receiver_email = data.get("receiver_email")
        response = data.get("response")

        if not all([name, receiver_email, response]):
            logging.warning("Missing data in request")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing data")

        send_email(
            subject="Discover Our New Product!",
            name=name,
            receiver_email=receiver_email,
            response=response,
        )
        return JSONResponse(content={"message": "Email sent successfully"}, status_code=status.HTTP_200_OK)
    except HTTPException as e:
        raise e  # Reraise HTTP exceptions to preserve status code
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@app.get('/test-smtp')
async def test_smtp():
    logging.info("Testing SMTP connection")
    try:
        with smtplib.SMTP(EMAIL_SERVER, PORT, timeout=10) as server:
            server.starttls()
            server.login(sender_email, password_email)
        return JSONResponse(content="SMTP connection successful", status_code=status.HTTP_200_OK)
    except smtplib.SMTPException as e:
        logging.error(f"SMTP connection failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"SMTP connection failed: {str(e)}")

@app.exception_handler(Exception)
async def handle_exception(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(content={"error": "An unexpected error occurred"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

if __name__ == '__main__':
    import uvicorn
    logging.info("Starting FastAPI application")
    uvicorn.run(app, host="0.0.0.0", port=8000)
