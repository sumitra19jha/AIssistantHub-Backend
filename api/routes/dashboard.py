from flask import Blueprint, request, jsonify

from api.controllers import dashboard as dashboard_controller
from api.middleware.auth import (authenticate)

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@bp.route("/generator/content", methods=["GET"])
@authenticate
def user_subscriptions():
    """Generate content based on the given parameters
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
      - name: type
        in: query
        type: string
        description: Type of content to generate
        enum: [BLOG POST, ARTICLE, LISTICLE, VIDEO SCRIPT, TWEET]
        required: true
      - name: topic
        in: query
        description: Topic of the content
        schema:
          type: string
          example: 'Sample topic'
        required: false
      - name: keywords
        in: query
        description: List of keywords to include in the content
        schema:
          type: string
          example: "Apple, Banana"
        required: false
      - name: length
        in: query
        description: Length of the content
        type: string
        enum: [SHORT, MEDIUM, LONG]
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
    return dashboard_controller.generate_content(
      user=request.user,
      type=request.args.get("type", None),
      topic=request.args.get("topic", None),
      keywords=request.args.get("keywords", None),
      length=request.args.get("length", None),
    )