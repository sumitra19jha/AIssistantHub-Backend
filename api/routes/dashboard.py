from flask import Blueprint, request, jsonify

from api.controllers import dashboard as dashboard_controller
from api.utils.request import get_parsed_data_list
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
      - name: platform
        in: query
        description: Platform of the content
        schema:
          type: string
          example: "Twitter"
        required: false
      - name: purpose
        in: query
        description: Purpose of the content
        schema:
          type: string
          example: "Promotional"
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
      platform=request.args.get("platform", None),
      purpose=request.args.get("purpose", None),
      keywords=request.args.get("keywords", None),
      length=request.args.get("length", None),
    )


@bp.route("/history/content", methods=["GET"])
@authenticate
def history_of_user_contents():
  """Get content history of the given user
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
    - name: page
      in: query
      schema:
        type: integer
        example: 1
      required: false
    - name: per_page
      in: query
      schema:
        type: integer
        example: 10
      required: false
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
  page = request.args.get("page", 1, type=int)
  per_page = request.args.get("per_page", 10, type=int)

  return dashboard_controller.content_history(
    user=request.user,
    page=page,
    per_page=per_page,
  )



@bp.route("/content/chat/history", methods=["GET"])
@authenticate
def history_of_chat_for_a_content():
    """Get content history of the given user
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
      - name: content_id
        in: query
        description: Id of content
        type: integer
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
    return dashboard_controller.content_chat_history(
      user=request.user,
      content_id=request.args.get("content_id", None),
    )

@bp.route('/content/save', methods=['POST'])
@authenticate
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
            contentId:
                type: integer
                description: The contentId
            content:
                type: string
                description: The content for saving by the user
        required:
            - contentId
            - content
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
    return dashboard_controller.save_content(
      user=request.user,
      *get_parsed_data_list(request, ["contentId", "content"])
    )