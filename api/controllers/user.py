import json
import bcrypt
from datetime import datetime as dt, timedelta, timezone
from dateutil.relativedelta import relativedelta
from http import HTTPStatus

from api.utils.otp import verify_otp
from api.utils.otp import generate_otp
from api.utils.db import add_flush_, commit_
from api.utils.send_email import send_otp_email
from api.utils.request import bad_response, response

from api.middleware.error_handlers import internal_error_handler

from api.models.user import User
from api.models import db
from api.models.session import Session
from api.models.subscriptions import Subscription
from api.models.subscription_type import SubscriptionType

from api.assets import constants


def create_session(user_id, login_method, device_details=None, ip_address=None):
    if device_details is not None and ip_address is not None:
        device_details["ipAddress"] = ip_address
        session = Session(
            user_id=user_id,
            login_method=login_method,
            timezone=device_details["timezone"],
            ip_address=device_details["ipAddress"],
            platform=device_details["device"],
            platform_os_version="{0} {1}".format(
                device_details["osName"], device_details["osVersion"]
            ),
            app_version=device_details["appVersion"],
            device_details=json.dumps(device_details),
        )
    else:
        session = Session(user_id=user_id, login_method=login_method)
    add_flush_(session)
    return session


def create_user(**kwargs):
    # Create new user object
    new_kwargs = {x: y for x, y in kwargs.items() if y is not None}
    user = User(**new_kwargs)
    add_flush_(user)
    return user

def create_free_use_subscription(user):
    subs = Subscription(
        user_id=user.id,
        subscription_type_id=1,
        valid_till=(dt.utcnow() + timedelta(days=7)),
    )
    add_flush_(subs)

    return subs


@internal_error_handler
def user_create(name, email, password):
    if (email is None or not isinstance(email, str) or email.strip() == ""):
        return response(
            success=False,
            message="Email is invalid / empty.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if name is not None and (not isinstance(name, str) or name.strip() == ""):
        return response(
            success=False,
            message="Name(str) is invalid / empty.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    
    if (
        password is None
        or not isinstance(password, str)
        or password.strip() == ""
    ):
        return response(
            success=False,
            message="password(str) is required",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if name is not None:
        name = name.strip()

    # Check if user exists already
    user = None
    if email is not None and isinstance(email, str) and "@" in email:
        email = email.strip().lower()
        user = User.query.filter(User.email == email).first()
    else:
        email = None

    if user is not None and user.status == constants.UserCons.enum_status_deleted:
        return response(
            success=False,
            message="Your account has been deleted. Please contact support.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    
    if user is not None and user.status == constants.UserCons.enum_status_active:
        has_set_password = user.password is not None
        otp = None

        if not has_set_password:
            otp = generate_otp(
                email=email,
                phone_country_code=None,
                phone_number=None,
            )

            email_sent = send_otp_email(
                email_recipient=email,
                recipient_name=name if user is None else user.name,
                otp=otp,
                context=constants.EmailTemplateCons.login_otp,
                domain=constants.EmailTemplateCons.default_domain,
            )

            if email_sent is False:
                otp = None

            return response(
                success=True,
                message=constants.SuccessMessage.user_exists,
                new_user=False,
                has_set_password=has_set_password,
                otp_sent=otp is not None,
            )
    
    otp = generate_otp(
        email=email, 
        phone_country_code=None, 
        phone_number=None
    )

    email_sent = send_otp_email(
        email_recipient=email,
        recipient_name=name,
        otp=otp,
        context=constants.EmailTemplateCons.login_otp,
        domain=constants.EmailTemplateCons.default_domain,
    )

    if email_sent is False:
        return response(
            success=False,
            message="Something went wrong while sending otp email. "
            "Please verify your email address or try again later.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    status = constants.UserCons.enum_status_email_verification_pending

    if user is None:
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = create_user(
            name=name,
            email=email,
            phone_country_code=None,
            phone_number=None,
            status=status,
            password=hashed_password.decode("utf-8"),
        )

        create_free_use_subscription(user)

    db.session.commit()
    return response(success=True, message=constants.SuccessMessage.otp_sent, new_user=True)


@internal_error_handler
def signup_verify_otp(email, otp, device_details=None, ip_address=None):
    if (email is None or not isinstance(email, str) or email.strip() == ""):
        return response(
            success=False,
            message="Email is required.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if otp is None or not isinstance(otp, str) or otp.strip() == "":
        return response(
            success=False,
            message="otp is required.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    user = None
    login_method = constants.SessionCons.enum_login_method_email

    if email is not None and isinstance(email, str) and "@" in email:
        # lower case email
        email = email.strip().lower()

        user = User.query.filter(User.email == email).first()
        login_method = constants.SessionCons.enum_login_method_email
    else:
        email = None

    if email is None:
        return response(
            success=False,
            message="Email is invalid.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if user is not None and user.status == constants.UserCons.enum_status_deleted:
        return response(
            success=False,
            message="Your account has been deleted. Please contact support.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if user is None:
        return response(
            success=False,
            message="User doesn't exist - signup first.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    verified = verify_otp(
        email=email,
        phone_country_code=None,
        phone_number=None,
        otp=otp,
    )

    if verified is False:
        return response(
            success=False, 
            message="OTP incorrect", 
            wrong_otp=True
        )

    user.status = constants.UserCons.enum_status_active

    session = create_session(
        user_id=user.id,
        login_method=login_method,
        device_details=device_details,
        ip_address=ip_address,
    )

    # If the email or phone is found in users_invited table with active status,
    # we should add them to the corresponding classes.

    db.session.commit()

    return response(
        success=True,
        message=constants.SuccessMessage.otp_verified,
        user=user.to_dict(),
        session_id=session.session_id,
        wrong_otp=False,
    )


@internal_error_handler
def resend_otp_signup(email):
    if (email is None or not isinstance(email, str) or email.strip() == ""):
        return response(
            success=False,
            message="Email is required.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    user = None

    if email is not None and isinstance(email, str) and "@" in email:
        # lower case email
        email = email.strip().lower()
        user = User.query.filter(User.email == email).first()
    else:
        email = None

    if email is None:
        return response(
            success=False,
            message="Email is invalid.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if user is not None and user.status == constants.UserCons.enum_status_deleted:
        return response(
            success=False,
            message="Your account has been deleted. Please contact support.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if user is None:
        return response(
            success=False,
            message="User does not exist. Please signup.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    otp = generate_otp(
        email=email, 
        phone_country_code=None, 
        phone_number=None,
    )

    email_sent = send_otp_email(
        email_recipient=email,
        recipient_name=user.name,
        otp=otp,
        context=constants.EmailTemplateCons.login_otp,
        domain=constants.EmailTemplateCons.default_domain,
    )

    if email_sent is False:
        return response(
            success=False,
            message="Something went wrong while sending otp email. "
            "Please verify your email address or try again later.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    

    return response(success=True, message=constants.SuccessMessage.otp_sent)


@internal_error_handler
def login(
    email,
    password,
    device_details=None,
    ip_address=None,
):

    if (not isinstance(email, str) or email.strip() == ""):
        return response(
            success=False,
            message="Email is required.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if not isinstance(password, str) or password.strip() == "":
        return response(
            success=False,
            message="Password is required.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # Check if user is registered
    user = None
    login_method = constants.SessionCons.enum_login_method_email

    if isinstance(email, str) and "@" in email:
        email = email.strip().lower()

        user = User.query.filter(User.email == email).first()
        login_method = constants.SessionCons.enum_login_method_email
    else:
        email = None

    if email is None:
        return response(
            success=False,
            message="Email is invalid.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if user is not None and user.status == constants.UserCons.enum_status_deleted:
        return response(
            success=False,
            message="Your account has been deleted. Please contact support.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if user is None:
        return response(
            success=False,
            message="User not registered. Please register first.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if not bcrypt.checkpw(
        password.encode("utf-8"), user.password.encode("utf-8")
    ):
        return response(
            success=False, 
            message="Password is incorrect.", 
            wrong_otp=True,
        )

    session = create_session(
        user_id=user.id,
        login_method=login_method,
        device_details=device_details,
        ip_address=ip_address,
    )

    db.session.commit()

    return response(
        success=True,
        message=constants.SuccessMessage.logged_in,
        user=user.to_dict(),
        session_id=session.session_id,
        wrong_otp=False,
    )


@internal_error_handler
def login_send_otp(email):
    if (not isinstance(email, str) or email.strip() == ""):
        return response(
            success=False,
            message="Either email is required.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # Check if user is registered
    user = None

    if email is not None and isinstance(email, str) and "@" in email:
        email = email.strip().lower()
        user = User.query.filter(User.email == email).first()
    else:
        email = None

    if email is None:
        return response(
            success=False,
            message="Email is invalid.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if user is not None and user.status == constants.UserCons.enum_status_deleted:
        return response(
            success=False,
            message="Your account has been deleted. Please contact support.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if user is None:
        return response(
            success=False,
            message="User not registered. Please register first.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    otp = generate_otp(
        email=email, 
        phone_country_code=None, 
        phone_number=None,
    )

    
    email_sent = send_otp_email(
        email_recipient=email,
        recipient_name=user.name,
        otp=otp,
        context=constants.EmailTemplateCons.login_otp,
        domain=constants.EmailTemplateCons.default_domain,
    )
    if email_sent is False:
        return response(
            success=False,
            message="Something went wrong while sending otp email. "
            "Please verify your email address or try again later.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    return response(
        success=True, 
        message=constants.SuccessMessage.otp_sent
    )

@internal_error_handler
def user_logout(session, session_id):

    if session is None:
        session = Session.query.filter(Session.session_id == session_id).first()

    session.status = constants.SessionCons.enum_logged_out
    db.session.commit()

    return response(
        success=True,
        message=constants.SuccessMessage.logged_out,
    )

@internal_error_handler
def user_subscriptions(user):
    subscriptions = (
        Subscription.query
        .filter(Subscription.user_id == user.id)
        .all()
    )

    user_subs = []
    for subscription in subscriptions:
        months_diff = relativedelta(subscription.valid_till, subscription.started_on).months
        subscription_data = {
            "date": subscription.created_at.strftime("%Y-%m-%d"),
            "plan": subscription.subscription_type.subscription_type,
            "cycle": f"{months_diff} months",
            "amount": subscription.subscription_type.subscription_price,
            "status": subscription.status,
            "invoice": subscription.invoice_link,
            "renewal": subscription.valid_till.strftime("%Y-%m-%d"),
        }
        user_subs.append(subscription_data)

    return response(
        success=True,
        message=constants.SuccessMessage.logged_out,
        subscriptions=user_subs,
    )