import email.utils
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config

# Replace sender@example.com with your "From" address.
# This address must be verified.
SENDER = Config.SMTP_EMAIL_SENDER
SENDERNAME = Config.SMTP_EMAIL_SENDER_NAME

# Replace recipient@example.com with a "To" address. If your account
# is still in the sandbox, this address must be verified.
# RECIPIENT = "user@emai.com"

# Replace smtp_username with your Amazon SES SMTP user name.
USERNAME_SMTP = Config.SMTP_USERNAME

# Replace smtp_password with your Amazon SES SMTP password.
PASSWORD_SMTP = Config.SMTP_PASSWORD

# (Optional) the name of a configuration set to use for this message.
# If you comment out this line, you also need to remove or comment out
# the "X-SES-CONFIGURATION-SET:" header below.
# CONFIGURATION_SET = "ConfigSet"

# If you're using Amazon SES in an AWS Region other than US West (Oregon),
# replace email-smtp.us-west-2.amazonaws.com with the Amazon SES SMTP
# endpoint in the appropriate region.
HOST = Config.SMTP_HOST
PORT = Config.SMTP_PORT


# The subject line of the email.
# SUBJECT = "Amazon SES Test (Python smtplib) - 2"

# The email body for recipients with non-HTML email clients.
# BODY_TEXT = (
#     "Amazon SES Test\r\n"
#     "This email was sent through the Amazon SES SMTP "
#     "Interface using the Python smtplib package."
# )

# The HTML body of the email.
# BODY_HTML = """<html>
# <head></head>
# <body>
#   <h1>Amazon SES SMTP Email Test</h1>
#   <p>This email was sent with Amazon SES using the
#     <a href='https://www.python.org/'>Python</a>
#     <a href='https://docs.python.org/3/library/smtplib.html'>
#     smtplib</a> library.</p>
# </body>
# </html>
#             """


def send_email(recipient, subject, body_text, body_html, from_email=None):
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    if from_email is not None:
        msg["From"] = email.utils.formataddr((SENDERNAME, from_email))
    else:
        msg["From"] = email.utils.formataddr((SENDERNAME, SENDER))
    msg["To"] = recipient
    # Comment or delete the next line if you are not using a configuration set
    # msg.add_header("X-SES-CONFIGURATION-SET", CONFIGURATION_SET)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(body_text, "plain")
    part2 = MIMEText(body_html, "html")

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Try to send the message.
    try:
        server = smtplib.SMTP(HOST, PORT)
        server.ehlo()
        server.starttls()
        # stmplib docs recommend calling ehlo() before & after starttls()
        server.ehlo()
        server.login(USERNAME_SMTP, PASSWORD_SMTP)
        server.sendmail(SENDER, recipient, msg.as_string())
        server.close()
    # Display an error message if something goes wrong.
    except Exception as e:
        print("Error: ", e)
        return False
    else:
        return True
