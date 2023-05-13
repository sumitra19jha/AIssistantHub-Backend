from flask import Blueprint, request, jsonify
from api.controllers import content as content_controller
from api.middleware.auth import (authenticate, authenticate_internal_rtc_backend)

bp = Blueprint("content", __name__, url_prefix="/content")


@bp.route("/create", methods=["POST"])
@authenticate
def create_content_for_social_media():
    """Generate Social Media Post based on the given parameters
    This API endpoint generates content based on the given parameters, such as type, topic, keywords, and length.
    ---
    tags:
        - Dashboard
    parameters:
      - name: Authorization
        in: header
        schema:
          type: string
          example: Bearer 52Y6QUDNSF2XRH43SUK3GSBMGUFZ08PNBOXSAO7QWQI6JJWAYN0F1GS5UA4W15XF3DJR7M369GOX8WDVXYZC2VBL2U2EHDZ9EABO
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            topic:
                type: string
                description: Topic of the content
            keywords:
                type: string
                description: List of keywords to include in the content
            platform:
                type: string
                description: Platform of the content
            length:
                type: string
                description: Length of the content
                enum: [SHORT, MEDIUM, LONG]
            urls:
                description: Urls for research
                type: array
                items:
                  type: object
        required:
            - topic
            - platform
            - length
    responses:
        200:
          description: In response, success and message are sent. Frontend should logout after successful response.
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    description: Indicates if the request was successful
                  message:
                    type: string
                    description: Message related to the request
    """
    return content_controller.create(
        user=request.user,
        topic=request.json.get("topic", None),
        keywords=request.json.get("keywords", None),
        platform=request.json.get("platform", None),
        length=request.json.get("length", None),
        urls=request.json.get("urls", None),
        user_ip=request.remote_addr,
    )


@bp.route("/fetch", methods=["POST"])
@authenticate
def fetch_content_for_social_media():
    """Generate Social Media Post based on the given parameters
    This API endpoint generates content based on the given parameters, such as type, topic, keywords, and length.
    ---
    tags:
        - Dashboard
    parameters:
      - name: Authorization
        in: header
        schema:
          type: string
          example: Bearer 52Y6QUDNSF2XRH43SUK3GSBMGUFZ08PNBOXSAO7QWQI6JJWAYN0F1GS5UA4W15XF3DJR7M369GOX8WDVXYZC2VBL2U2EHDZ9EABO
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            topic:
                content_id: integer
                description: Topic of the content
        required:
            - content_id
    responses:
        200:
          description: In response, success and message are sent. Frontend should logout after successful response.
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    description: Indicates if the request was successful
                  message:
                    type: string
                    description: Message related to the request
    """
    return content_controller.fetch_content(
      user=request.user,
      content_id=request.json.get("content_id", None),
      user_ip=request.remote_addr,
    )

@bp.route("/update", methods=["GET"])
@authenticate_internal_rtc_backend
def update_content():
    """Generate content based on the given parameters
    This API endpoint generates content based on the given parameters, such as type, topic, keywords, and length.
    ---
    tags:
        - RTC BACKEND CALLS
    parameters:
      - name: Authorization
        in: header
        schema:
          type: string
          example: Bearer 52Y6QUDNSF2XRH43SUK3GSBMGUFZ08PNBOXSAO7QWQI6JJWAYN0F1GS5UA4W15XF3DJR7M369GOX8WDVXYZC2VBL2U2EHDZ9EABO
        required: true
      - name: user_id
        in: query
        description: User id of content
        schema:
          type: integer
          example: 1
        required: true
      - name: content_id
        in: query
        description: User id of content
        schema:
          type: integer
          example: 1
        required: true
      - name: message
        in: query
        description: message of the user
        schema:
          type: string
          example: "Twitter"
        required: true
    responses:
        200:
          description: In response, success and message are sent. Frontend should logout after successful response.
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                    description: Indicates if the request was successful
                  message:
                    type: string
                    description: Message related to the request
    """
    return content_controller.update_content(
      user_id=request.args.get("user_id", None),
      user_name=request.args.get("user_name", None),
      content_id=request.args.get("content_id", None),
      message=request.args.get("message", None),
    )
