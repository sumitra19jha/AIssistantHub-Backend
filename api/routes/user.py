from flask import Blueprint, request, jsonify

from config import Config
from api.utils.request import get_parsed_data_list
from api.controllers import user as user_controller
from api.middleware.auth import (authenticate)

bp = Blueprint("user", __name__, url_prefix="/user")


@bp.route("/oauth/google", methods=["POST"])
def oauth_google():
    """This is used as oauth google signup api. This api validates the token_id sent from the frontend and if successful, session will be created and the user will be logged in.
    ---
    tags:
        - User
    parameters:
      - name: body
        in: body
        schema:
          type: object
          required:
            - role
            - token_id
          properties:
            token_id:
              type: string
            role:
              type: string
              enum: [teacher, student]
            floating_user_id:
              type: integer

    responses:
      200:
        description: In response, user object, session_id are sent other than success and message. Frontend should login after successful response.
    """
    return user_controller.oauth_google(
        token_id=request.json.get("token_id", None),
        device_details=request.json.get("device_details", None),
        ip_address= request.remote_addr,
    )

@bp.route('/register', methods=['POST'])
def register():
    """
    User signup api
    ---
    tags:
      - User
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            name:
                type: string
                description: The name of the user
            email:
                type: string
                format: email
                description: The email address of the user
            password:
                type: string
                format: password
                description: The password of the user
        required:
            - name
            - email
            - password
    responses:
      200:
        description: A list of generated content ideas
        schema:
          type: object
          properties:
            ideas:
              type: array
              items:
                type: string
    """
    return user_controller.user_create(
        *get_parsed_data_list(request, ["name", "email", "password"])
    )


@bp.route("/verify-otp", methods=["POST"])
def signup_verify_otp():
    """This is used as otp verify api.
    ---
    tags:
        - User
    parameters:
      - name: body
        in: body
        schema:
          type: object
          required:
            - email
            - otp
          properties:
            email:
              type: string
              format: email
            otp:
              type: string
              pattern: '^\d{6}$'

    responses:
      200:
        description: The wrong_otp field can be used by frontend to show whether the otp is wrong or not. wrong_otp=true means otp entered is incorrect. on successful otp verification, frontend should proceed to set password or not based on whether the user has selected the option to set password.
    """
    return user_controller.signup_verify_otp(
        *get_parsed_data_list(request, ["email", "otp", "device_details"]),
        request.remote_addr
    )


@bp.route("/resend-otp", methods=["POST"])
def signup_resend_otp():
    """This is used as otp verify api.
    ---
    tags:
        - User
    parameters:
      - name: body
        in: body
        schema:
          type: object
          required:
            - email
            - otp
          properties:
            email:
              type: string
              format: email

    responses:
      200:
        description: The wrong_otp field can be used by frontend to show whether the otp is wrong or not.
    """
    return user_controller.resend_otp_signup(
        *get_parsed_data_list(request, ["email"]),
    )


@bp.route("/login", methods=["POST"])
def login():
    """This is used as login api. The email/phone and password will be verified. Only email or phone is required. otp/password both are sent in the same password field.
    ---
    tags:
        - User
    parameters:
      - name: body
        in: body
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              format: email
            password:
              type: string

    responses:
      200:
        description: In response, user object, session_id are sent other than success and message. Frontend should login after successful verification. The wrong_otp field can be used by frontend to show whether the otp/password is wrong or not. wrong_otp=true means otp/password entered is incorrect.
    """
    return user_controller.login(
        *get_parsed_data_list(
            request, ["email", "password", "device_details"]
        ),
        request.remote_addr
    )


@bp.route("/forget-password", methods=["POST"])
def login_send_otp():
    """This is used as send otp api in the login phone. Only email or phone is required. Can also be used for resend otp during login.
    ---
    tags:
        - User
    parameters:
      - name: body
        in: body
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              format: email

    responses:
      200:
        description: In response, only success and message are sent.
    """
    return user_controller.login_send_otp(
        *get_parsed_data_list(request, ["email"])
    )


@bp.route("/logout", methods=["POST"])
@authenticate
def user_logout():
    """This is used as logout api.
    ---
    tags:
        - User
    parameters:
      - name: Authorization
        in: header
        schema:
          type: string
          example: Bearer 52Y6QUDNSF2XRH43SUK3GSBMGUFZ08PNBOXSAO7QWQI6JJWAYN0F1GS5UA4W15XF3DJR7M369GOX8WDVXYZC2VBL2U2EHDZ9EABO
        required: true

    responses:
      200:
        description: In response, success and message are sent. Frontend should logout after successful response.
    """
    return user_controller.user_logout(
        session=request.session,
        session_id=request.session_id
    )


@bp.route("/subscriptions", methods=["GET"])
@authenticate
def user_subscriptions():
    """This is subscriptions api.
    ---
    tags:
        - User
    parameters:
      - name: Authorization
        in: header
        schema:
          type: string
          example: Bearer 52Y6QUDNSF2XRH43SUK3GSBMGUFZ08PNBOXSAO7QWQI6JJWAYN0F1GS5UA4W15XF3DJR7M369GOX8WDVXYZC2VBL2U2EHDZ9EABO
        required: true

    responses:
      200:
        description: In response, success and message are sent. Frontend should logout after successful response.
    """
    return user_controller.user_subscriptions(
        user=request.user
    )

@bp.route("/ai/details", methods=["GET"])
@authenticate
def user_subscriptions_ai_details():
    """This is subscriptions api.
    ---
    tags:
        - User
    parameters:
      - name: Authorization
        in: header
        schema:
          type: string
          example: Bearer 52Y6QUDNSF2XRH43SUK3GSBMGUFZ08PNBOXSAO7QWQI6JJWAYN0F1GS5UA4W15XF3DJR7M369GOX8WDVXYZC2VBL2U2EHDZ9EABO
        required: true

    responses:
      200:
        description: In response, success and message are sent. Frontend should logout after successful response.
    """
    return user_controller.user_subscriptions_ai_details(
        user=request.user
    )
