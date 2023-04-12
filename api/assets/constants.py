import random

from config import Config

class ContentPrompt:
    linkedin_system_message="""You are a LinkedIn post creator working for KeywordIQ. You are generating a post for our client. The post should capture attention, encourage user interaction, and include a call to action. Consider using storytelling or personal anecdotes if relevant, as well as bullet points or numbered lists for readability. Mention relevant hashtags to increase visibility. In order for the post to reach a wide audience LinkedIn algorithm checks the following:

1. Named Entity Recognition
2. Keywords and Themes
3. Positive Sentiment
4. Topics
5. Words Embedding


Create a post accordingly."""
    def linkedin_user_message(topic, content_length):
        return f"Create a post on \"{topic}\" that is approximately {content_length} long. If it's an opinion, use only data to create the post. Think step by step and your reply should only contain the Social Media Post text and nothing else.";

    def social_media_post_system_message(platform, topic, content_length):
        return f"Generate an engaging {platform} post on {topic} with a length of {content_length}. The post should capture attention, encourage user interaction, and include a call-to-action. Consider using storytelling or personal anecdotes if relevant, as well as bullet points or numbered lists for readability. Mention relevant hashtags to increase visibility. Your response should only contain the final post in HTML format."

    def social_media_post_user_message(platform, topic, content_length):
        return f"Create a {platform} post about {topic} that is approximately {content_length} long and engaging for audience. If its an opinion, use only data to create the post. Think step by step and provide only the social media post in your response."


class ChatPrompt:
    def social_media_system_chat_prompt(platform):
        return f"You are now an assistant content creator GPT called 'IntelliMate' working for KeywordIQ Company. You are doing real-time communication with our client to work on Social Media Post that we have created for user to be used on ${platform}. Make communication with our client helpful and supportive."


class EmailTemplateCons:
    login_otp = "LOGIN_OTP"
    account_delete_otp = "ACCOUNT_DELETE_OTP"
    password_change_otp = "PASSWORD_CHANGE"
    default_domain = "keywordiq.com"


class EmailType:
    SALES = "SALES"
    SUPPORT = "SUPPORT"

class SubscriptionTypes:
    TRIAL = "TRIAL"
    STARTER = "STARTER"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

class UserSubscriptionStatus:
    ISSUED = "ISSUED"
    REVOKED = "REVOKED"

class ChatTypes:
    USER="USER"
    AI="AI"
    SYSTEM="SYSTEM"

class ContentTypes:
    SOCIAL_MEDIA_POST="SOCIAL MEDIA POST"
    BLOG_POST="BLOG POST"
    ARTICLE="ARTICLE"
    EMAIL_MARKETING="EMAIL MARKETING"
    NEWS_LETTER="NEWS LETTER"
    PRODUCT_DESCRIPTION="PRODUCT DESCRIPTION"
    CASE_STUDY="CASE STUDY"
    WHITE_PAPER="WHITE PAPER"
    LISTICLE="LISTICLE"
    VIDEO_SCRIPT="VIDEO SCRIPT"
    WEBINAR_SCRIPT="WEBINAR SCRIPT"
    EDUCATIONAL_CONTENT="EDUCATIONAL CONTENT"

    def all():
        return [
            ContentTypes.SOCIAL_MEDIA_POST,
            ContentTypes.BLOG_POST,
            ContentTypes.ARTICLE,
            ContentTypes.EMAIL_MARKETING,
            ContentTypes.NEWS_LETTER,
            ContentTypes.PRODUCT_DESCRIPTION,
            ContentTypes.CASE_STUDY,
            ContentTypes.WHITE_PAPER,
            ContentTypes.LISTICLE,
            ContentTypes.VIDEO_SCRIPT,
            ContentTypes.WEBINAR_SCRIPT,
            ContentTypes.EDUCATIONAL_CONTENT,
        ]

class ContentLengths:
    SHORT="SHORT"
    MEDIUM="MEDIUM"
    LONG="LONG"

    def all():
        return [
            ContentLengths.SHORT, 
            ContentLengths.MEDIUM, 
            ContentLengths.LONG,
        ]

class ContentStatus:
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

class LogScope:
    INFO = "info"
    DEBUG = "debug"
    WARNING = "warning"
    ERROR = "error"

class ErrorMessage:
    internal_server_error = "Something went wrong. Please try again."
    class_join = "Failed to join the class"
    class_not_found = "No class found"
    otp_not_sent = "There was a problem while sending OTP. Please try again."
    wrong_otp = "Wrong otp entered. Please try again."
    doc_type_not_recognized = "Document type is not recognized."
    storage_limit_exceeded = "Storage limit exceeded."
    add_liveclass_audience_to_class = "Failed to add users to class"

class UserCons:
    status = "status"

    enum_status_email_verification_pending = "email_verification_pending"
    enum_status_phone_verification_pending = "phone_verification_pending"
    enum_status_active = "active"
    enum_status_temp = "temporary"
    enum_status_deleted = "deleted"

    enum_gender_male = "male"
    enum_gender_female = "female"

class SessionCons:
    enum_active = "active"
    enum_logged_out = "logged_out"

    enum_login_method_email = "email"
    enum_login_method_name = "name"
    enum_login_method_phone = "phone"
    enum_login_method_google = "google"
    enum_login_method_facebook = "facebook"
    enum_login_method_apple = "apple"

class SuccessMessage:
    user_exists = "User exists. Please sign in"
    otp_sent = "OTP sent successfully"
    otp_verified = "OTP verified successfully"
    logged_in = "User logged in successfully"
    logged_out = "User logged out successfully"
    content_generated="Successfully, Generated the content."
    content_history="Successfully, Fetched the content history."