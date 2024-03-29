from api.assets import constants
import re
from api.utils import logging_wrapper

logger = logging_wrapper.Logger(__name__)

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

    def create_array_from_text(text):
        try:
            array_elements = re.findall(r'\[([\s\S]*?)\]', text)
            if len(array_elements) == 0:
                return []

            array_string = array_elements[0]
            items = [item.strip().strip('"') for item in array_string.split(",")]
            return items
        except Exception as e:
            return []
        
    def preprocess_pointwise_search_array(arr):
        try:
            # Remove leading numbers, quotes, and extra spaces
            processed_array = [query.split('. ')[1].strip('"') for query in arr if '. ' in query]
            return processed_array
        except Exception as e:
            logger.exception(str(e))
            print(f"Error: {e}")
            return []
