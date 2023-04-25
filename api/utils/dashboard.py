from api.assets import constants

class DashboardUtils:
    def sizeOfContent(type, length):
        if type == constants.ContentTypes.SOCIAL_MEDIA_POST:
            if length == constants.ContentLengths.SHORT:
                return "50 - 100 words"
            elif length == constants.ContentLengths.MEDIUM:
                return "100 - 200 words"
            else:
                return "200 - 300 words"
        elif (type == constants.ContentTypes.BLOG_POST) or (type == constants.ContentTypes.ARTICLE) or (type == constants.ContentTypes.LISTICLE):
            if length == constants.ContentLengths.SHORT:
                return "300 - 500 words"
            elif length == constants.ContentLengths.MEDIUM:
                return "500 - 1,200 words"
            else:
                return "1,200 - 2,500+ words"
        elif (type == constants.ContentTypes.EMAIL_MARKETING) or (type == constants.ContentTypes.NEWS_LETTER):
            if length == constants.ContentLengths.SHORT:
                return "100 - 200 words"
            elif length == constants.ContentLengths.MEDIUM:
                return "200 - 500 words"
            else:
                return "500 - 1,000 words"
        elif (type == constants.ContentTypes.PRODUCT_DESCRIPTION):
            if length == constants.ContentLengths.SHORT:
                return "50 - 100 words"
            elif length == constants.ContentLengths.MEDIUM:
                return "100 - 200 words"
            else:
                return "200 - 400 words"
        elif (type == constants.ContentTypes.CASE_STUDY):
            if length == constants.ContentLengths.SHORT:
                return "500 - 1,000 words"
            elif length == constants.ContentLengths.MEDIUM:
                return "1,000 - 2,000 words"
            else:
                return "2,000 - 5,000+ words"
        elif (type == constants.ContentTypes.VIDEO_SCRIPT):
            if length == constants.ContentLengths.SHORT:
                return "100 - 200 words"
            elif length == constants.ContentLengths.MEDIUM:
                return "200 - 600 words"
            else:
                return "600 - 1,200+ words"
        else:
            if length == constants.ContentLengths.SHORT:
                return "300 - 500 words"
            elif length == constants.ContentLengths.MEDIUM:
                return "500 - 1,200 words"
            else:
                return "1,200 - 2,500+ words"

    def format_string_for_chat(text):
        return ' '.join(word.capitalize(
        ) for word in text.replace('_', ' ').split(' '))
