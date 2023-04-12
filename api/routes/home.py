from flask import Blueprint, request, jsonify

from config import Config
from api.controllers import home as home_controller

bp = Blueprint("home", __name__, url_prefix="/home")

@bp.route('/generate_ideas', methods=['POST'])
def generate_ideas():
    """
    Generate content ideas
    ---
    tags:
      - ideas
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            query:
              type: string
              example: content marketing
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
    return home_controller.get_trending_topics(request.get_json()["query"])


@bp.route('/get_trending_keywords', methods=['POST'])
def get_trending_keywords():
    """
    Fetch trending topics and keyword suggestions
    ---
    tags:
      - keywords
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            query:
              type: string
              example: content marketing
    responses:
      200:
        description: Trending topics and keyword suggestions
        schema:
          type: object
          properties:
            trending_topics:
              type: array
              items:
                type: string
            keyword_suggestions:
              type: array
              items:
                type: string
    """
    data = request.get_json()
    query = data['query']
    trending_topics = home_controller.get_trending_topics(query)
    keyword_suggestions = home_controller.get_keyword_suggestions(query, Config.YOUR_SEMRUSH_API_KEY)
    return jsonify({"trending_topics": trending_topics, "keyword_suggestions": keyword_suggestions})


@bp.route('/seo_optimization', methods=['POST'])
def seo_optimization():
    """
    Fetch SEO Optimisation
    ---
    tags:
      - keywords
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            content:
              type: string
              example: content marketing
    responses:
      200:
        description: Trending topics and keyword suggestions
        schema:
          type: object
          properties:
            trending_topics:
              type: array
              items:
                type: string
            keyword_suggestions:
              type: array
              items:
                type: string
    """
    return home_controller.seo_optimization(request.get_json()['content'])

@bp.route('/generate_content_ideas', methods=['POST'])
def generate_content_ideas():
    """
    Generate content ideas
    ---
    tags:
      - ideas
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            prompt:
              type: string
              example: content marketing
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
    data = request.get_json()
    prompt = data['prompt']
    num_ideas = data.get('num_ideas', 5)
    return home_controller.generate_content_ideas(prompt, num_ideas)


@bp.route('/generate_content_brief', methods=['POST'])
def generate_content_brief():
    """
    Generate a content brief based on provided keywords, target audience, and competitors.
    ---
    tags:
      - Content Brief
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Data to generate a content brief
        required: true
        schema:
          type: object
          properties:
            keywords:
              type: array
              items:
                type: string
              description: List of target keywords for the content
              example: ["digital marketing", "SEO", "social media marketing"]
            target_audience:
              type: string
              description: Description of the target audience for the content
              example: "Small business owners looking to improve their online presence"
            competitors:
              type: array
              items:
                type: string
              description: List of competitors to consider while creating the content
              example: ["Moz", "HubSpot", "SEMrush"]
            num_sections:
              type: integer
              description: Number of sections to include in the content outline (optional)
              example: 5
    responses:
      200:
        description: Content brief generated successfully
        schema:
          type: object
          properties:
            content_brief:
              type: string
              description: The generated content brief
              example: "I. Introduction to Digital Marketing\\nII. Importance of SEO\\nIII. Social Media Marketing Strategies\\nIV. Email Marketing Best Practices\\nV. Conclusion"
    """
    data = request.get_json()
    keywords = data['keywords']
    target_audience = data['target_audience']
    competitors = data['competitors']
    num_sections = data.get('num_sections', 5)
    return home_controller.generate_content_brief(keywords, target_audience, competitors, num_sections)

@bp.route('/generate_social_media_posts', methods=['POST'])
def generate_social_media_posts():
    """
    Generate engaging social media posts, including captions and hashtags.
    ---
    tags:
      - Social Media
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Data to generate social media posts
        required: true
        schema:
          type: object
          properties:
            topic:
              type: string
              description: The topic for which to generate social media posts
              example: "Digital Marketing"
            num_posts:
              type: integer
              description: Number of social media posts to generate (optional)
              example: 3
    responses:
      200:
        description: Social media posts generated successfully
        schema:
          type: object
          properties:
            posts:
              type: array
              items:
                type: object
                properties:
                  caption:
                    type: string
                    description: The social media post caption
                    example: "Boost your digital marketing skills with these 5 amazing tips! 💪 #DigitalMarketing #MarketingTips"
                  hashtags:
                    type: string
                    description: The social media post hashtags
                    example: "#SEO #SocialMedia #EmailMarketing"
    """
    data = request.get_json()
    topic = data['topic']
    num_posts = data.get('num_posts', 3)
    posts = home_controller.generate_social_media_posts(topic, num_posts)
    return jsonify({"posts": posts})

@bp.route('/repurpose_content', methods=['POST'])
def repurpose_content():
    """
    Repurpose existing content into a different format, such as turning a blog post into a video script or infographic.
    ---
    tags:
      - Content Repurposing
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Data to repurpose content
        required: true
        schema:
          type: object
          properties:
            content:
              type: string
              description: The original content to repurpose
              example: "Digital marketing is an essential aspect of any business..."
            target_format:
              type: string
              description: The target format for repurposing the content
              example: "video script"
    responses:
      200:
        description: Content repurposed successfully
        schema:
          type: object
          properties:
            repurposed_content:
              type: string
              description: The repurposed content
              example: "In this video, we'll explore the importance of digital marketing for businesses..."
    """
    data = request.get_json()
    content = data['content']
    target_format = data['target_format']
    repurposed_content = home_controller.repurpose_content(content, target_format)
    return jsonify({"repurposed_content": repurposed_content})


@bp.route('/trends/keywords', methods=['GET'])
def trends_keywords():
    """
    Repurpose existing content into a different format, such as turning a blog post into a video script or infographic.
    ---
    tags:
      - Content Repurposing
    consumes:
      - application/json
    produces:
      - application/json
    responses:
      200:
        description: Content repurposed successfully
        schema:
          type: object
          properties:
            repurposed_content:
              type: string
              description: The repurposed content
              example: "In this video, we'll explore the importance of digital marketing for businesses..."
    """
    return {
        "keywords":["Today my blog is on Generative AI", "Lets brainstorm this week content"]
    }


