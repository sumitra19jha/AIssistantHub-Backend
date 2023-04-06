import random

from config import Config

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

class ContentLengths:
    SHORT="SHORT"
    MEDIUM="MEDIUM"
    LONG="LONG"

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