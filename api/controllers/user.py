import json
import bcrypt

from google.oauth2 import id_token
from google.auth.transport import requests as g_requests
from datetime import datetime as dt, timedelta, timezone
from dateutil.relativedelta import relativedelta
from http import HTTPStatus
from sqlalchemy import or_

from api.models.purchase import Purchase
from api.models.purchase_history import PurchaseHistory
from api.utils import logging_wrapper
from api.utils.otp import verify_otp
from api.utils.otp import generate_otp
from api.utils.db import add_flush_, commit_
from api.utils.send_email import send_otp_email
from api.utils.request import bad_response, response
from api.middleware.error_handlers import internal_error_handler
from api.models.user import User
from api.models import db
from api.models.session import Session
from api.assets import constants

from config import Config

from api.controllers.purchase import PhonePePayment
from flask import Flask, jsonify, request

logger = logging_wrapper.Logger(__name__)

def initiate_user_payment(user):
    phonepe = PhonePePayment()
    # assuming transaction details are stored in the user model
    payment_url = phonepe.initiate_payment(user.transaction_details) 
    return payment_url

def purchase_subscription(user):
    payment_url = initiate_user_payment(user)
    return payment_url

app = Flask(__name__)

@app.route('/purchase', methods=['POST'])
def purchase():
    user_id = request.json.get('user_id')
    user = User.query.get(user_id)  # or any other method you use to get a user
    
    if user is not None:
        payment_url = purchase_subscription(user)
        return jsonify({'message': 'Payment initiated', 'payment_url': payment_url}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

    

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
    purch = Purchase(
        user_id=user.id,
        points=100,
    )
    add_flush_(purch)

    purch_history = PurchaseHistory(
        purchase_id=purch.id,
        amount=0.0,
    )
    add_flush_(purch_history)

    return purch, purch_history

def create_user_session(
    login_method=None, device_details=None, ip_address=None, **kwargs
):
    kwargs.setdefault(constants.UserCons.status, constants.UserCons.enum_status_active)
    user = create_user(**kwargs)
    purch, purch_history = create_free_use_subscription(user)
    session = create_session(
        user_id=user.id,
        login_method=login_method,
        device_details=device_details,
        ip_address=ip_address,
    )
    commit_()  # TODO - @shivam - keep commits in main controller functions so that we know.
    return user, session, purch, purch_history


@internal_error_handler
def oauth_google(token_id, device_details=None, ip_address=None):
    if (
        token_id is None
        or not isinstance(token_id, str)
        or token_id.strip() == ""
    ):
        return response(
            success=False,
            message="token_id(str) is mandatory",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    try:
        user_data = id_token.verify_oauth2_token(
            token_id,
            g_requests.Request(),
            Config.GOOGLE_OAUTH_CLIENT_ID,
        )
        assert "sub" in user_data
    except Exception as e:
        logger.exception(str(e))
        return response(
            success=False,
            message="Something went wrong while authenticating (test) with Google. Please try again.",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    email, name, picture_url = (
        user_data.get("email", None),
        user_data.get("name", None),
        user_data.get("picture", None),
    )
    oauth_id_google = user_data.get("sub", None)

    if name is not None:
        name = name.strip()

    # Check if user is already present
    if email is not None and isinstance(email, str) and "@" in email:
        email = email.strip().lower()
        user = User.query.filter(
            or_(User.email == email, User.oauth_id_google == oauth_id_google)
        ).first()
    else:
        email = None
        user = User.query.filter(User.oauth_id_google == oauth_id_google).first()

    if user is not None:
        new_user = False
        if user.status == constants.UserCons.enum_status_deleted:
            return response(
                success=False,
                message="Your account has been deleted. Please contact support.",
                status_code=HTTPStatus.BAD_REQUEST,
            )
        if name is not None and user.name is None:
            user.name = name
        if email is not None:
            user.email = email
        if picture_url is not None:
            user.profile_photo_url = picture_url
        user.oauth_id_google = oauth_id_google
        user.status = constants.UserCons.enum_status_active
        session = create_session(
            user_id=user.id,
            login_method=constants.SessionCons.enum_login_method_google,
            device_details=device_details,
            ip_address=ip_address,
        )
    # Create new user
    else:
        new_user = True
        user, session, purch, purch_history = create_user_session(
            name=name,
            email=email,
            oauth_id_google=oauth_id_google,
            status=constants.UserCons.enum_status_active,
            profile_photo_url=picture_url,
            login_method=constants.SessionCons.enum_login_method_google,
            device_details=device_details,
            ip_address=ip_address,
        )

    # If the email or phone is found in users_invited table with active status,
    # we should add them to the corresponding classes.
    db.session.commit()

    return response(
        success=True,
        message=constants.SuccessMessage.logged_in,
        user=user.to_dict(),
        session_id=session.session_id,
        new_user=new_user,
    )


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
        Purchase.query
        .filter(Purchase.user_id == user.id)
        .all()
    )

    user_subs = []
    for subscription in subscriptions:
        purchase_history = PurchaseHistory.query.filter(PurchaseHistory.purchase_id == subscription.id).first()

        subscription_data = {
            "date": subscription.created_at.strftime("%Y-%m-%d"),
            "points": subscription.points,
            "price": purchase_history.amount,
            "status": "Activated",
        }
        user_subs.append(subscription_data)

    return response(
        success=True,
        message=constants.SuccessMessage.logged_out,
        subscriptions=user_subs,
    )

@internal_error_handler
def user_points(user):
    all_purchase = (
        Purchase.query
        .filter(Purchase.user_id == user.id)
        .all()
    )

    points = 0
    for purchase in all_purchase:
        points += purchase.points

    return response(
        success=True,
        message=constants.SuccessMessage.logged_out,
        points=points,
    )


@internal_error_handler
def user_subscriptions_ai_details(user):
    subscriptions = (
        Purchase.query
        .filter(Purchase.user_id == user.id)
        .all()
    )

    user_subs = []
    for subscription in subscriptions:
        subscription_data = {
            "date": subscription.created_at.strftime("%Y-%m-%d"),
            "name": "Proton",
            "description": "Social Media Content Creator",
            "status": "Active",
            "resume": "/proton/resume",
        }
        user_subs.append(subscription_data)

    return response(
        success=True,
        message=constants.SuccessMessage.logged_out,
        details=user_subs,
    )
