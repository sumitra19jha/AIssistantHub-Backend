from flask import Blueprint, request, jsonify

from api.controllers import analysis as analysis_controller
from api.middleware.auth import (authenticate)

bp = Blueprint("analysis", __name__, url_prefix="/analysis")

@bp.route("/linkedin", methods=["POST"])
@authenticate
def linkedin_analysis():
    """Generate content analysis for linkedin social media post.
    ---
    tags:
        - Analysis
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
            content:
                type: string
                description: The linkedin post
        required:
            - content
    responses:
        200:
          description: In response, success and message are sent.
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
    return analysis_controller.linkedin_analysis(
      user=request.user,
      content=request.get_json()["content"],
    )