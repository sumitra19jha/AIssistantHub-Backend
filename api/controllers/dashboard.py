from bs4 import BeautifulSoup
from http import HTTPStatus

from api.middleware.error_handlers import internal_error_handler

from api.assets import constants

from api.utils.classifier_models import ClassifierModels
from api.utils.content_db import ContentDataModel
from api.utils.dashboard import DashboardUtils
from api.utils.db import add_commit_, add_flush_, commit_
from api.utils.generator_models import GeneratorModels
from api.utils.instructor import Instructor
from api.utils.news_utlis import AssistantHubNewsAlgo
from api.utils.prompt import PromptGenerator
from api.utils.socket import Socket
from api.utils.validator import APIInputValidator
from api.utils.input_preprocessor import InputPreprocessor
from api.utils.scrapper import AssistantHubScrapper
from api.utils.time import TimeUtils
from api.utils.request import bad_response, response
from api.utils.seo_utils import AssistantHubSEO
from api.utils import logging_wrapper

from api.models import db
from api.models.content import Content
from api.models.chat import Chat
from api.models.youtube_seo_analysis import YouTubeSEOAnalysis

logger = logging_wrapper.Logger(__name__)

@internal_error_handler
def seo_analyzer_youtube(user, business_type, target_audience, industry, goals, user_ip):
    # Validate input
    validation_response = APIInputValidator.validate_input_for_seo(
        business_type,
        target_audience,
        industry,
        goals,
    )

    if validation_response:
        return validation_response

    country_name = AssistantHubScrapper.get_country_name_from_ip(user_ip)

    youtube_seo_data_model = YouTubeSEOAnalysis(
        user_id=user.id,
        business_type=business_type,
        target_audience=target_audience,
        industry=industry,
        goals=goals,
        country=country_name,
        user_ip=user_ip,
    )
    add_commit_(youtube_seo_data_model)

    # Generate YouTube search queries using GPT-4
    try:
        youtube_search_query_arr = GeneratorModels.generate_youtube_search_text_gpt4(
            user=user,
            business_type=business_type,
            target_audience=target_audience,
            industry=industry,
            location=country_name
        )
    except Exception as e:
        logger.exception(str(e))
        return response(
            success=False,
            message=f"Error generating search query: {str(e)}"
        )

    # Preprocess search queries
    youtube_array_of_search = DashboardUtils.preprocess_youtube_search_array(youtube_search_query_arr)

    # Remove short search queries
    youtube_array_of_search = [query for query in youtube_array_of_search if len(query) >= 5]

    if not youtube_array_of_search:
        return response(
            success=False,
            message="Unable to generate the search query.",
        )

    # Fetch YouTube video data
    try:
        youtube_data = AssistantHubSEO.youtube_search(youtube_array_of_search, youtube_seo_data_model.id)
    except Exception as e:
        return response(
            success=False,
            message=f"Error fetching YouTube data: {str(e)}"
        )

    # Extract keywords and phrases from video data
    title_documents, description_documents = AssistantHubSEO.yotube_video_keywords_extraction(youtube_data)

    # Compute the TF-IDF matrix for title and description
    title_tfidf_model, title_corpus, title_dictionary = AssistantHubSEO.compute_tfidf_matrix(title_documents)
    description_tfidf_model, description_corpus, description_dictionary = AssistantHubSEO.compute_tfidf_matrix(description_documents)

    # Identify top keywords for title and description
    top_title_keywords = AssistantHubSEO.identify_top_keywords(title_tfidf_model, title_corpus, title_dictionary)
    top_description_keywords = AssistantHubSEO.identify_top_keywords(description_tfidf_model, description_corpus, description_dictionary)

    # Calculate the keyword scores for title and description
    title_keyword_scores = AssistantHubSEO.calculate_keyword_score(top_title_keywords, youtube_data)
    description_keyword_scores = AssistantHubSEO.calculate_keyword_score(top_description_keywords, youtube_data)

    # Rank the keywords based on their scores
    ranked_title_keywords = AssistantHubSEO.rank_keywords(title_keyword_scores)
    ranked_description_keywords = AssistantHubSEO.rank_keywords(description_keyword_scores)

    # Filter the keywords based on their scores
    filtered_title_keywords = AssistantHubSEO.filter_keywords(ranked_title_keywords)
    filtered_description_keywords = AssistantHubSEO.filter_keywords(ranked_description_keywords)

    # Combine the top keywords from titles and descriptions and remove duplicates
    combined_keywords = list(set(filtered_title_keywords + filtered_description_keywords))

    # Generate title templates using GPT-3.5 Turbo
    try:
        title_templates = GeneratorModels.generate_title_templates_gpt4(
            user=user,
            business_type=business_type,
            target_audience=target_audience,
            industry=industry,
            location=country_name,
            num_templates=5  # You can adjust the number of templates generated
        )
    except Exception as e:
        return response(
            success=False,
            message=f"Error generating title templates: {str(e)}"
        )

    # Preprocess search queries
    filtered_templates = DashboardUtils.preprocess_youtube_search_array(title_templates)

    # Fill in the title templates with the top keywords to create content title variations
    content_titles = []
    for template in filtered_templates:
        for keyword in combined_keywords:
            content_title = template.lower().replace("{keyword}", keyword)
            content_titles.append(content_title)

    youtube_seo_data_model.suggestions = {
        "title_templates": title_templates,
        "content_titles": content_titles,
        "filtered_title_keywords": filtered_title_keywords,
        "filtered_description_keywords": filtered_description_keywords,
    }

    commit_()

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data=[data.to_dict() for data in youtube_data],
        title_keyword_scores=filtered_title_keywords,
        description_keyword_scores=filtered_description_keywords,
        content_titles=content_titles,
    )

@internal_error_handler
def seo_analyzer_news(user, business_type, target_audience, industry, goals, user_ip):
    validation_response = APIInputValidator.validate_input_for_seo(
        business_type, 
        target_audience, 
        industry,
        goals,
    )
    
    if validation_response:
        return validation_response

    overall_goals = ", ".join(goals)
    country_name = AssistantHubScrapper.get_country_name_from_ip(user_ip)

    # Generate News search queries using GPT-4
    try:
        # news_search_query = AssistantHubNewsAlgo.generate_news_search_text_gpt4(
        #     user=user,
        #     business_type=business_type,
        #     target_audience=target_audience,
        #     industry=industry,
        #     location=country_name
        # )
        news_search_query = [f"1. {business_type} {target_audience} {industry} {country_name} news"]
    except Exception as e:
        logger.exception(str(e))
        return response(
            success=False,
            message=f"Error generating search query: {str(e)}"
        )

    news_array_of_search = DashboardUtils.preprocess_youtube_search_array(news_search_query)

    # Remove short search queries
    news_array_of_search = [query for query in news_array_of_search if len(query) >= 5]

    if not news_array_of_search:
        return response(
            success=False,
            message="Unable to generate the search query.",
        )

    news_articles = AssistantHubNewsAlgo.fetch_google_news(news_array_of_search)
    trending_topics = AssistantHubNewsAlgo.keywords_titles_builder(news_articles)
    titles = [AssistantHubNewsAlgo.generate_title(keywords, user) for keywords in trending_topics]

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data=news_articles,
        suggestion_titles= [AssistantHubNewsAlgo.clean_title(title) for title in titles],
    )


@internal_error_handler
def seo_analyzer_places(user, business_type, target_audience, industry, goals, user_ip):
    validation_response = APIInputValidator.validate_input_for_seo(
        business_type, 
        target_audience, 
        industry,
        goals,
    )
    
    if validation_response:
        return validation_response

    overall_goals = ", ".join(goals)
    query = f"{business_type} {target_audience} {industry} {overall_goals}"

    #4. Places search
    places_data = AssistantHubSEO.fetch_google_places(query)
    
    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data=places_data,
    )

@internal_error_handler
def seo_analyzer_search_results(user, business_type, target_audience, industry, goals, user_ip):
    validation_response = APIInputValidator.validate_input_for_seo(
        business_type, 
        target_audience, 
        industry,
        goals,
    )
    
    if validation_response:
        return validation_response

    overall_goals = ", ".join(goals)
    country_name = AssistantHubScrapper.get_country_name_from_ip(user_ip)
    
    query = f"{business_type} {target_audience} {industry} {overall_goals}"
    num_pages=1

    #1. Search Engine Analysis
    search_results = AssistantHubSEO.fetch_google_search_results(query, num_pages)

    # Analyse the google search results and get the keywords
    search_analysis = AssistantHubSEO.analyze_google_search_results(search_results)

    search_text_data = [item.get("title", "") + " " + item.get("snippet", "") for item in search_results.get("items", [])]

    # NLP Analysis
    semantic_keywords_and_topics = AssistantHubSEO.get_lsi_topic_and_keywords(search_text_data, num_topics=5)
    long_tail_keywords = AssistantHubSEO.get_long_tail_keywords(search_text_data, max_keywords=50)

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data=search_results.get("items", []),
        search_results_analysis=search_analysis,
        semantic_topics= semantic_keywords_and_topics["topics"],
        long_tail_keywords= long_tail_keywords,
        lsi_keywords= semantic_keywords_and_topics["keywords"],
    )

@internal_error_handler
def seo_analyzer_competitors(user, business_type, target_audience, industry, goals, user_ip):
    validation_response = APIInputValidator.validate_input_for_seo(
        business_type, 
        target_audience, 
        industry,
        goals,
    )
    
    if validation_response:
        return validation_response

    overall_goals = ", ".join(goals)
    country_name = AssistantHubScrapper.get_country_name_from_ip(user_ip)
    
    query = f"{business_type} {target_audience} {industry} {overall_goals}"
    
    #Competition Analysis
    competitor_urls = AssistantHubSEO.fetch_competitors(query)
    comptitor_analysis = []
    competitor_display = []
    competition_text_data = []

    for url in competitor_urls:
        html = AssistantHubSEO.fetch_html(url)

        if html:
            analysis = AssistantHubSEO.analyze_competion_page(html)
            comptitor_analysis.append(analysis)
            competitor_display.append({"title": analysis["title"], "url": url, "meta_description": "" if analysis["meta_description"] == None else analysis["meta_description"]})
            competition_text_data.append(analysis["title"] + " " + ( "" if analysis["meta_description"] == None else analysis["meta_description"]))

    # NLP Analysis
    semantic_keywords_and_topics = AssistantHubSEO.get_lsi_topic_and_keywords(competition_text_data, num_topics=5)
    long_tail_keywords = AssistantHubSEO.get_long_tail_keywords(competition_text_data, max_keywords=50, n_components=20)

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data= competitor_display,
        comptitor_analysis= comptitor_analysis,
        semantic_topics= semantic_keywords_and_topics["topics"],
        long_tail_keywords= long_tail_keywords,
        lsi_keywords= semantic_keywords_and_topics["keywords"],
    )


@internal_error_handler
def seo_analyzer_online_forums(user, business_type, target_audience, industry, goals, user_ip):
    validation_response = APIInputValidator.validate_input_for_seo(
        business_type, 
        target_audience, 
        industry,
        goals,
    )
    
    if validation_response:
        return validation_response

    overall_goals = ", ".join(goals)
    country_name = AssistantHubScrapper.get_country_name_from_ip(user_ip)
    
    query = f"{business_type} {target_audience} {industry} {overall_goals}"
    num_pages=1

    #Online Social Forum Analysis
    #TODO: Change this to a subreddit of the user's choice
    subreddit_name = "photography"

    analysis = AssistantHubSEO.analyze_reddit_subreddit(subreddit_name)
    subreddit_text_data = [post.get("title", "") + " " + post.get("body", "") for post in analysis["posts"]]

    # NLP Analysis
    semantic_keywords_and_topics = AssistantHubSEO.get_lsi_topic_and_keywords(subreddit_text_data, num_topics=5)
    long_tail_keywords = AssistantHubSEO.get_long_tail_keywords(subreddit_text_data, max_keywords=50, n_components=20)

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data= analysis.get("posts", []),
        semantic_topics= semantic_keywords_and_topics["topics"],
        long_tail_keywords= long_tail_keywords,
        lsi_keywords= semantic_keywords_and_topics["keywords"],
    )


@internal_error_handler
def seo_optimisation_generator(user, business_type, target_audience, industry, goals, user_ip):
    validation_response = APIInputValidator.validate_input_for_seo(
        business_type, 
        target_audience, 
        industry,
        goals,
    )
    
    if validation_response:
        return validation_response

    overall_goals = ", ".join(goals)
    country_name = AssistantHubScrapper.get_country_name_from_ip(user_ip)
    
    query = f"{business_type} {target_audience} {industry} {overall_goals}"
    num_pages=1

    #1. Search Engine Analysis
    search_results = AssistantHubSEO.fetch_google_search_results(query, num_pages)

    # Analyse the google search results and get the keywords
    search_analysis = AssistantHubSEO.analyze_google_search_results(search_results)

    #2. Youtube Search
    youtube_search_query = GeneratorModels.generate_youtube_search_text(
        user=user,
        bussiness_type=business_type,
        target_audience=target_audience,
        industry=industry,
        goals=overall_goals,
        location=country_name
    )

    youtube_array_of_search = DashboardUtils.create_array_from_text(youtube_search_query)
    
    if len(youtube_array_of_search) == 0:
        youtube_query = f"{business_type} {target_audience} {industry} {overall_goals}"
    else:
        youtube_query = youtube_array_of_search[0]
        print(youtube_query)

    youtube_data = AssistantHubSEO.youtube_search(youtube_query)

    #3. News Search
    news_search_query = GeneratorModels.generate_news_search_text(
        user=user,
        bussiness_type=business_type,
        target_audience=target_audience,
        industry=industry,
        goals=overall_goals,
        location=country_name
    )

    news_array_of_search = DashboardUtils.create_array_from_text(news_search_query)

    if len(news_array_of_search) == 0:
        news_query = f"{business_type} {target_audience} {industry} {overall_goals}"
    else:
        news_query = news_array_of_search[0]
        print(news_query)

    news_data = AssistantHubSEO.fetch_google_news(news_query)

    #4. Places search
    places_data = AssistantHubSEO.fetch_google_places(query)
    
    #Competition Analysis
    competitor_urls = AssistantHubSEO.fetch_competitors(query)
    comptitor_analysis = []
    competitor_display = []
    competition_text_data = []

    for url in competitor_urls:
        html = AssistantHubSEO.fetch_html(url)

        if html:
            analysis = AssistantHubSEO.analyze_competion_page(html)
            comptitor_analysis.append(analysis)
            competitor_display.append({"title": analysis["title"], "url": url, "meta_description": "" if analysis["meta_description"] == None else analysis["meta_description"]})
            competition_text_data.append(analysis["title"] + " " + ( "" if analysis["meta_description"] == None else analysis["meta_description"]))

    #Online Social Forum Analysis
    #TODO: Change this to a subreddit of the user's choice
    subreddit_name = "photography"

    analysis = AssistantHubSEO.analyze_reddit_subreddit(subreddit_name)
    subreddit_text_data = [post.get("title", "") + " " + post.get("body", "") for post in analysis["posts"]]

    search_text_data = [item.get("title", "") + " " + item.get("snippet", "") for item in search_results.get("items", [])]
    youtube_text_data = [video.get("title", "") for video in youtube_data] if youtube_data else []
    news_text_data = [item.get("title", "") + " " + item.get("snippet", "") for item in news_data.get("items", [])] if news_data else []

    # NLP Analysis
    semantic_keywords_and_topics = AssistantHubSEO.get_lsi_topic_and_keywords(search_text_data + news_text_data + youtube_text_data + competition_text_data + subreddit_text_data, num_topics=5)
    long_tail_keywords = AssistantHubSEO.get_long_tail_keywords(search_text_data + news_text_data + youtube_text_data + competition_text_data + subreddit_text_data, max_keywords=50)

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        search_results=search_results,
        search_results_analysis=search_analysis,
        news_data=news_data,
        youtube_data=youtube_data,
        places_data=places_data,
        competitor_data= competitor_display,
        comptitor_analysis= comptitor_analysis,
        online_forums= analysis,
        semantic_topics= semantic_keywords_and_topics["topics"],
        long_tail_keywords= long_tail_keywords,
        lsi_keywords= semantic_keywords_and_topics["keywords"],
    )

@internal_error_handler
def generate_content_for_social_media(user, topic, platform, keywords, length, urls, user_ip):
    validation_response = APIInputValidator.validate_content_input_for_social_media(
        topic, 
        platform, 
        length,
    )
    
    if validation_response:
        return validation_response
    
    try:
        processed_input = InputPreprocessor.preprocess_user_input_for_social_media_post(
            topic, 
            urls, 
            length, 
            platform
        )
    except ValueError as e:
        return response(
            success=False,
            message=str(e),
            status_code=HTTPStatus.BAD_REQUEST,
        )
    except Exception as e:
        return response(
            success=False,
            message=str(e),
            status_code=HTTPStatus.BAD_REQUEST,
        )

    is_opinion = ClassifierModels.is_the_topic_opinion_based(processed_input['topic'])

    if is_opinion:
        web_searched_results = AssistantHubScrapper.search_and_crawl(
            processed_input['topic'], 
            user_ip,
        )

        web_content = ""
        for result in web_searched_results:
            web_content = web_content + result['website'] + "\n\n"
            web_content = web_content + result['content'] + "\n\n"

        system_message, user_message = PromptGenerator.generate_messages_on_opinion_for_social_media(
            processed_input['topic'],
            processed_input['platform'],
            processed_input["length"],
            web_content
        )
    else:
        web_searched_results = None
        system_message, user_message = PromptGenerator.generate_messages_for_social_media(
            processed_input['topic'],
            processed_input['platform'],
            length,
            processed_input["length"],
        )

    content_data = ContentDataModel.create_content_data(
        user=user,
        type="SOCIAL_MEDIA_POST",
        topic=processed_input['topic'],
        platform=processed_input['platform'],
        keywords=keywords,
        length=length,
        system_message=system_message,
        user_message=user_message,
        purpose=None,
    )

    try:
        assistant_response = GeneratorModels.generate_content(user, system_message, user_message)
        ContentDataModel.update_content_model_after_successful_ai_response(assistant_response, content_data)
    except Exception as e:
        assistant_response = None
        ContentDataModel.update_content_model_after_failed_ai_response(content_data)

    if assistant_response == None:
        return response(
            success=False,
            message="Unable to generate the content.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
        
    Instructor.handle_chat_instruction_for_social_media(
        user.name,
        content_data,
        is_opinion,
        web_searched_results,
    )

    # Call the Node.js server to create a room
    Socket.create_room_for_content(
        content_data.id, 
        content_data.user_id,
    )

    return response(
        success=True,
        message=constants.SuccessMessage.content_generated,
        content=content_data.model_response,
        contentId=content_data.id,
    )


@internal_error_handler
def generate_content(user, type, topic, purpose, keywords, length, urls, user_ip):
    validation_response = APIInputValidator.validate_content_input(
        type=type, 
        topic=topic, 
        length=length
    )

    if validation_response:
        return validation_response

    # Prprocessing
    try:
        processed_input = InputPreprocessor.preprocess_user_input(
            topic=topic,
            urls=urls,
            length=length,
        )
    except ValueError as e:
        return response(
            success=False,
            message=str(e),
            status_code=HTTPStatus.BAD_REQUEST,
        )
    except Exception as e:
        return response(
            success=False,
            message=str(e),
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # 'platform': platform,
    # 'topic': topic,
    # 'urls': parsed_urls,
    # 'length': content_length,
    # 'url_contents': url_contents
    web_searched_results = None
    system_message, user_message = PromptGenerator.generate_messages(
        type=type,
        topic=processed_input['topic'],
        content_length=processed_input["length"],
        purpose=purpose
    )

    content_data = ContentDataModel.create_content_data(
        user=user,
        type=type,
        topic=processed_input['topic'],
        platform=None,
        purpose=purpose,
        keywords=keywords,
        length=length,
        system_message=system_message,
        user_message=user_message
    )

    try:
        assistant_response = GeneratorModels.generate_content(user, system_message, user_message)
        ContentDataModel.update_content_model_after_successful_ai_response(assistant_response, content_data)
    except Exception as e:
        assistant_response = None
        ContentDataModel.update_content_model_after_failed_ai_response(content_data)

    if assistant_response == None:
        return response(
            success=False,
            message="Unable to generate the content.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    
    Instructor.handle_chat_instruction(
        name_of_user=user.name,
        content_data=content_data,
    )

    # Call the Node.js server to create a room
    Socket.create_room_for_content(
        content_data.id, 
        content_data.user_id,
    )

    return response(
        success=True,
        message=constants.SuccessMessage.content_generated,
        content=content_data.model_response,
        contentId=content_data.id,
    )


@internal_error_handler
def content_history(user, page=1, per_page=10):
    contents_data = (
        Content.query.filter(
            Content.user_id == user.id,
            Content.status == constants.ContentStatus.SUCCESS,
        )
        .order_by(Content.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    history = []
    for content in contents_data.items:
        # Create a BeautifulSoup object to parse the HTML content
        soup = BeautifulSoup(content.model_response, "html.parser")

        # Get only the text content of the page
        model_response_text = soup.get_text()
        created_at = TimeUtils.time_ago(content.created_at)

        history.append({
            "content_id": content.id,
            "created_at": created_at,
            "type": content.type,
            "topic": content.topic,
            "length": content.length,
            "model_response": model_response_text,
            "html_form": content.model_response,
        })

    return response(
        success=True,
        message=constants.SuccessMessage.content_generated,
        history=history,
        pagination={
            "page": contents_data.page,
            "per_page": contents_data.per_page,
            "total_pages": contents_data.pages,
            "total_items": contents_data.total,
        },
    )


@internal_error_handler
def content_chat_history(user, content_id):
    chats_data = (
        Chat.query.filter(
            Chat.content_id == content_id,
            Chat.hidden == False,
            Chat.type != constants.ChatTypes.SYSTEM,
        )
        .all()
    )

    history = []
    for chat in chats_data:
        history.append({
            "id": chat.id,
            "type": "ai" if chat.type == constants.ChatTypes.AI else "user",
            "content": chat.message,
            "username": "Proton" if chat.type == constants.ChatTypes.AI else user.name,
            "timestamp": chat.created_at,
        })

    return response(
        success=True,
        message=constants.SuccessMessage.content_generated,
        history=history,
    )


@internal_error_handler
def save_content(user, contentId, content):
    print(content)
    if contentId is not None and (not isinstance(contentId, int)):
        return response(
            success=False,
            message="contentId(int) is invalid / empty.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if content is not None and (not isinstance(content, str) or content.strip() == ""):
        return response(
            success=False,
            message="content(str) is invalid / empty.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    content_db_data = (
        Content.query
        .filter(
            Content.id == contentId,
            Content.user_id == user.id,
        )
        .first()
    )

    content_db_data.content_data = content
    db.session.commit()

    return response(
        success=True,
        message=constants.SuccessMessage.content_generated,
        content=content,
    )