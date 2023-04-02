import json

from api.assets import constants
from api.utils.smtp_email import send_email
from jinja2 import Environment, PackageLoader, select_autoescape


def send_email_from_template(
    email_template, email_body_text, to, subject, from_email=None, **kwargs
):
    jinja_env = Environment(
        loader=PackageLoader("app", "email_templates"),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = jinja_env.get_template(email_template)
    email_body = template.render(**kwargs)
    return send_email(to, subject, email_body_text, email_body, from_email=from_email)


def send_otp_email(
    email_recipient,
    recipient_name,
    otp,
    context,
    domain,
    from_email=None,
):
    email_subject = "Your KeywordIQ OTP is %s" % otp
    email_body_text = "Your requested KeywordIQ OTP is %s" % otp

    # Select template based on context passed

    if context == constants.EmailTemplateCons.password_change_otp:
        email_subject = "Your KeywordIQ OTP to change password is %s" % otp
        template_name = "password_change.html"
    elif context == constants.EmailTemplateCons.account_delete_otp:
        email_subject = "Your KeywordIQ OTP to delete account"
        template_name = "account_delete.html"
    else:
        template_name = "otp.html"

    return send_email_from_template(
        template_name,
        email_body_text,
        email_recipient,
        email_subject,
        otp=otp,
        user=recipient_name,
        domain=domain,
        role_message="Content Making",
        from_email=from_email,
    )
