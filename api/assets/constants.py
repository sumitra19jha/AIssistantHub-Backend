class ContentPrompt:
    linkedin_system_message = "You are a LinkedIn post creator assistant AI. You are generating a post for our client. The post should capture attention, encourage user interaction, and include a call to action. Consider using storytelling or personal anecdotes if relevant, as well as bullet points or numbered lists for readability. Mention relevant hashtags to increase visibility. Only provide the post in your response."
    linkedin_system_message_for_opinion = "You are a LinkedIn post creator. You are generating a post based on the source.\n\nThe post is an opinion that is framed using internet data. So cite the source in the post. The post should capture attention, encourage user interaction, and include a call to action. Consider using storytelling or personal anecdotes if relevant, as well as bullet points or numbered lists for readability. Mention relevant hashtags to increase visibility. Only provide post in the response."

    def linkedin_user_message_for_opinion(topic, websites_content, content_length):
        return f"Create a LinkedIn post on \"${topic}\" based on information from the internet website in \"${content_length}\". Stick to the word limit. The information provided by the websites are below:\n\n```\n{websites_content}\n```"
        
    def linkedin_user_message(topic, content_length):
        return f"Create a linkedin post that is approximately {content_length} long on below topic.\n\"\"\"\n{topic}\n\"\"\""

    def social_media_post_system_message(platform, topic, content_length):
        return f"Generate an engaging {platform} post on {topic} with a length of {content_length}. The post should capture attention, encourage user interaction, and include a call-to-action. Consider using storytelling or personal anecdotes if relevant, as well as bullet points or numbered lists for readability. Mention relevant hashtags to increase visibility. Your response should only contain the final post in HTML format."

    def social_media_post_user_message(platform, topic, content_length):
        return f"Create a {platform} post about {topic} that is approximately {content_length} long and engaging for audience. If its an opinion, use only data to create the post. Think step by step and provide only the social media post in your response."


class ChatPrompt:
    def social_media_system_chat_prompt():
        return "You are a customer representative GPT working for AIssistantHub company to understand and communicate user requirements.\n\nInstructions:\n1. User message is inside *\n\n2. We have already given content to the user.\n\n3. If you detect the user wants to update the content and has not provided feedback on changes that need to be done then begin your response as \"requirement//\".\n\n4. If you detect the user wants to update the content and has provided feedback on changes that need to be done, then begin your response with \"update//\"\n\n5. If it's an update then tell the user update has started in funny humour using emojis and talk to the user about his life like a human does. Begin your response with \"message//\". Meanwhile, the content will be updated in a few seconds.\n\n6. If your previous message in history starts with \"requirement//\" and the user has provided the requirement, begin your message with \"update//\" and tell the user we are updating the content.\n\n7. Your response can only begin with either \"message//\", \"update//\" or \"requirement//\"\n\n8. Keep your response as short as possible\n\n\nThink step by step and follow all the instructions. Provide a single final response to our client."

    def social_media_user_chat_prompt_by_system(user_name, type, platform, topic):
        return f"You are talking to {user_name}. You can start the conversation by greeting the user and informing that user request for {type} on \"{topic}\" for {platform} is created."
    
    def social_media_user_chat_prompt_by_system_for_opinion(user_name, type, platform, topic, websites):
        return f"You are talking to {user_name}. You can start the conversation by greeting the user and informing that user request for an opinion based {type} on \"{topic}\" for {platform} is created using these websites: {websites}. Make sure that your response is in less than 100 words."


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
    USER = "USER"
    AI = "AI"
    SYSTEM = "SYSTEM"


class ContentTypes:
    SOCIAL_MEDIA_POST = "SOCIAL MEDIA POST"
    BLOG_POST = "BLOG POST"
    ARTICLE = "ARTICLE"
    EMAIL_MARKETING = "EMAIL MARKETING"
    NEWS_LETTER = "NEWS LETTER"
    PRODUCT_DESCRIPTION = "PRODUCT DESCRIPTION"
    CASE_STUDY = "CASE STUDY"
    WHITE_PAPER = "WHITE PAPER"
    LISTICLE = "LISTICLE"
    VIDEO_SCRIPT = "VIDEO SCRIPT"
    WEBINAR_SCRIPT = "WEBINAR SCRIPT"
    EDUCATIONAL_CONTENT = "EDUCATIONAL CONTENT"

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
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"

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


class ProjectTypeCons:
    enum_youtube = "youtube"
    enum_news = "news"
    enum_maps = "maps"
    enum_google_search = "google_search"
    enum_competitor = "competitor"
    enum_reddit = "reddit"


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
    content_generated = "Successfully, Generated the content."
    content_history = "Successfully, Fetched the content history."
    keywords="Successfully fetched keywords"
    seo_analysis="Successfully fetched seo analysis"
