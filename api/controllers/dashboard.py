import math
from bs4 import BeautifulSoup
from http import HTTPStatus
from concurrent.futures import ThreadPoolExecutor
from flask import current_app, session

import concurrent.futures
from api.middleware.error_handlers import internal_error_handler
from api.assets import constants
from api.models.analysis import Analysis
from api.models.purchase import Purchase
from api.models.search_analysis_rel import SearchAnalysisRel
from api.models.search_query import SearchQuery

from api.utils.classifier_models import ClassifierModels
from api.utils.competitors_util import CompetitorUtils
from api.utils.content_db import ContentDataModel
from api.utils.dashboard import DashboardUtils
from api.utils.db import add_commit_, add_flush_, commit_
from api.utils.generator_models import GeneratorModels
from api.utils.instructor import Instructor
from api.utils.maps_utils import AssistantHubMapsAlgo
from api.utils.news_utlis import AssistantHubNewsAlgo
from api.utils.prompt import PromptGenerator
from api.utils.search_utils import GoogleSearchUtils
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
from api.models.seo_project import SEOProject
from api.utils.youtube_utils import YotubeSEOUtils

logger = logging_wrapper.Logger(__name__)

def is_user_have_sufficient_points(user_id):
    purchase = (
        Purchase.query
        .filter(
            Purchase.user_id == user_id,
            Purchase.points > 0,
        )
        .first()
    )

    if purchase is None:
        return False, None
    
    return True, purchase


@internal_error_handler
def seo_analyzer_create_project(user, business_type, target_audience, industry, goals, user_ip):
    is_allowed, purchase = is_user_have_sufficient_points(user.id)

    if not is_allowed:
        return bad_response(
            message="You don't have enough points to create a project.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    
    # Validate input
    validation_response = APIInputValidator.validate_input_for_seo(
        business_type,
        target_audience,
        industry,
        goals,
    )

    if validation_response:
        return validation_response

    overall_goals = ", ".join(goals)
    country_name, country_code = AssistantHubScrapper.get_country_name_and_code_from_ip(user_ip)

    if country_name is None:
        country_name = "India"

    if country_code is None:
        country_code = "IN"

    try:
        seo_project = SEOProject(
            user_id=user.id,
            business_type=business_type,
            target_audience=target_audience,
            industry=industry,
            goals=overall_goals,
            country=country_name,
            user_ip=user_ip,
            country_code=country_code,
        )
        add_commit_(seo_project)
    except Exception as e:
        logger.exception(e)
        return bad_response(
            message="Failed to create project",
            data={"error": str(e)},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    return response(
        success=True,
        message="Project created successfully",
        data=seo_project.to_dict(),
    )

@internal_error_handler
def seo_analyzer_youtube(user, project_id):
    if project_id is None:
        return bad_response(
            message="Project id is required",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    
    project_data_model = SEOProject.query.filter(SEOProject.id == project_id).first()

    # Generate YouTube search queries using GPT-4
    try:
        youtube_search_query_arr = YotubeSEOUtils.generate_youtube_search_text_gpt4(
            user=user,
            business_type=project_data_model.business_type,
            target_audience=project_data_model.target_audience,
            industry=project_data_model.industry,
            location=project_data_model.country,
        )
    except Exception as e:
        logger.exception(str(e))
        return response(
            success=False,
            message=f"Error generating search query: {str(e)}"
        )

    # Preprocess search queries
    youtube_array_of_search = DashboardUtils.preprocess_pointwise_search_array(youtube_search_query_arr)

    # Remove short search queries
    youtube_array_of_search = [query for query in youtube_array_of_search if len(query) >= 5]

    if not youtube_array_of_search:
        return response(
            success=False,
            message="Unable to generate the search query.",
        )

    # Fetch YouTube video data
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_video_data = {executor.submit(YotubeSEOUtils.youtube_search, current_app._get_current_object(), query, project_id): query for query in youtube_array_of_search}
            youtube_data = []
            for future in concurrent.futures.as_completed(future_to_video_data):
                query = future_to_video_data[future]
                try:
                    data = future.result()
                    youtube_data.extend(data)
                except Exception as e:
                    logger.exception(f"Error fetching YouTube data for query {query}: {str(e)}")
                    # Handle the exception as needed

    except Exception as e:
        return response(
            success=False,
            message=f"Error fetching YouTube data: {str(e)}"
        )

    # Extract keywords and phrases from video data
    title_documents, description_documents = YotubeSEOUtils.yotube_video_keywords_extraction(youtube_data)

    # Compute the TF-IDF matrix for title and description
    title_tfidf_model, title_corpus, title_dictionary = YotubeSEOUtils.compute_tfidf_matrix(title_documents)
    description_tfidf_model, description_corpus, description_dictionary = YotubeSEOUtils.compute_tfidf_matrix(description_documents)

    # Identify top keywords for title and description
    top_title_keywords = YotubeSEOUtils.identify_top_keywords(title_tfidf_model, title_corpus, title_dictionary)
    top_description_keywords = YotubeSEOUtils.identify_top_keywords(description_tfidf_model, description_corpus, description_dictionary)

    # Calculate the keyword scores for title and description
    title_keyword_scores = YotubeSEOUtils.calculate_keyword_score(top_title_keywords, youtube_data)
    description_keyword_scores = YotubeSEOUtils.calculate_keyword_score(top_description_keywords, youtube_data)

    # Rank the keywords based on their scores
    ranked_title_keywords = YotubeSEOUtils.rank_keywords(title_keyword_scores)
    ranked_description_keywords = YotubeSEOUtils.rank_keywords(description_keyword_scores)

    # Filter the keywords based on their scores
    filtered_title_keywords = YotubeSEOUtils.filter_keywords(ranked_title_keywords)
    filtered_description_keywords = YotubeSEOUtils.filter_keywords(ranked_description_keywords)

    # Combine the top keywords from titles and descriptions and remove duplicates
    combined_keywords = list(set(filtered_title_keywords + filtered_description_keywords))

    # Generate title templates using GPT-3.5 Turbo
    try:
        title_templates = YotubeSEOUtils.generate_title_templates_gpt4(
            user=user,
            keywords_str=",".join(combined_keywords),
            num_templates=5  # You can adjust the number of templates generated
        )
    except Exception as e:
        return response(
            success=False,
            message=f"Error generating title templates: {str(e)}"
        )

    # Preprocess search queries
    filtered_templates = DashboardUtils.preprocess_pointwise_search_array(title_templates)

    # TODO: Implement Suggestions
    project_data_model.youtube_suggestions = {
        "title_templates": title_templates,
        "filtered_templates": filtered_templates,
        "filtered_title_keywords": filtered_title_keywords,
        "filtered_description_keywords": filtered_description_keywords,
    }
    commit_()

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        project=project_data_model.to_dict(),
        data=[data.to_dict() for data in youtube_data],
        title_suggestion=filtered_templates,
    )

@internal_error_handler
def seo_analyzer_news(user, project_id):
    points = 0.0
    is_allowed, purchase = is_user_have_sufficient_points(user.id)

    if not is_allowed:
        return bad_response(
            message="You don't have enough points to create a project.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if project_id is None:
        return bad_response(
            message="Project id is required",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # Due to multiple session used user id needs to be stored in seprate variable
    user_id = user.id

    project_data_model = (
        SEOProject.query
        .filter(
            SEOProject.id == project_id,
            SEOProject.user_id == user_id,
        ).first()
    )

    if project_data_model is None:
        return bad_response(
            message="Project not found",
            status_code=HTTPStatus.NOT_FOUND,
        )

    if project_data_model.news_suggestions is not None:
        news_data = AssistantHubNewsAlgo.get_data(project_id)

        return response(
            success=True,
            message=constants.SuccessMessage.seo_analysis,
            data=news_data,
            suggestion_titles=project_data_model.news_suggestions["suggestion_titles"],
        )

    # Generate News search queries using GPT-4
    try:
        news_search_query = AssistantHubNewsAlgo.generate_news_search_text_gpt4(
            user=user,
            business_type=project_data_model.business_type,
            target_audience=project_data_model.target_audience,
            industry=project_data_model.industry,
            location=project_data_model.country
        )
        print(news_search_query)
        # news_search_query = [f"1. {project_data_model.business_type} {project_data_model.target_audience} {project_data_model.industry} {project_data_model.country} news"]
    except Exception as e:
        logger.exception(str(e))
        return response(
            success=False,
            message=f"Error generating search query: {str(e)}"
        )

    # news_array_of_search = DashboardUtils.preprocess_pointwise_search_array(news_search_query)

    # Remove short search queries
    news_array_of_search = [query for query in news_search_query if len(query) >= 5]

    if not news_array_of_search:
        return response(
            success=False,
            message="Unable to generate the search query.",
        )

    news_articles, total_points = AssistantHubNewsAlgo.fetch_google_news(news_array_of_search, project_id, project_data_model.country_code)
    points += total_points

    trending_topics = AssistantHubNewsAlgo.keywords_titles_builder(news_articles)

    # seo_analyzer_news function
    with ThreadPoolExecutor() as executor:
        titles_futures = [executor.submit(AssistantHubNewsAlgo.generate_title, keywords, user_id, current_app._get_current_object()) for keywords in trending_topics]
        titles_results = [future.result() for future in titles_futures]
        titles, total_tokens_list = zip(*titles_results)
        total_tokens_gpt4 = sum(total_tokens_list)
        
    points = points + ((total_tokens_gpt4 * 0.02)/1000)
    project_data_model.news_suggestions = {
        "suggestion_titles": [AssistantHubNewsAlgo.clean_title(title) for title in titles],
    }
    purchase.points = purchase.points - math.ceil((points * 100))
    db.session.commit()

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data=news_articles,
        suggestion_titles=project_data_model.news_suggestions["suggestion_titles"],
    )


@internal_error_handler
def seo_analyzer_places(user, project_id, app):
    points = 0.0
    is_allowed, purchase = is_user_have_sufficient_points(user.id)

    if not is_allowed:
        return bad_response(
            message="You don't have enough points to create a project.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if project_id is None:
        return bad_response(
            message="Project id is required",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    # Due to multiple session used user id needs to be stored in seprate variable
    user_id = user.id

    project_data_model = (
        SEOProject.query
        .filter(
            SEOProject.id == project_id,
            SEOProject.user_id == user_id,
        ).first()
    )

    if project_data_model is None:
        return bad_response(
            message="Project not found",
            status_code=HTTPStatus.NOT_FOUND,
        )

    if project_data_model.maps_suggestions is not None:
        maps_data = AssistantHubMapsAlgo.get_data(project_id)

        return response(
            success=True,
            message=constants.SuccessMessage.seo_analysis,
            data=maps_data,
            keywords=project_data_model.maps_suggestions["keywords"],
            geo_distribution=project_data_model.maps_suggestions["geo_distribution"],
        )

    # Generate News search queries using GPT-4
    try:
        maps_search_query, total_tokens = AssistantHubMapsAlgo.generate_maps_search_text_gpt4(
            user_id=user_id,
            business_type=project_data_model.business_type,
            target_audience=project_data_model.target_audience,
            industry=project_data_model.industry,
            location=project_data_model.country
        )
        points = points + ((total_tokens * 0.03)/1000)
    except Exception as e:
        logger.exception(str(e))
        return response(
            success=False,
            message=f"Error generating search query: {str(e)}"
        )

    if not maps_search_query:
        return response(
            success=False,
            message="Unable to generate the search query.",
        )

    search_model = SearchQuery.query.filter(
        SearchQuery.search_query == maps_search_query[0],
        SearchQuery.seo_project_id == project_id,
        SearchQuery.type == constants.ProjectTypeCons.enum_maps,
    ).first()

    if search_model is None:
        search_model = SearchQuery(
            search_query=maps_search_query[0],
            seo_project_id=project_id,
            type=constants.ProjectTypeCons.enum_maps,
        )
        add_commit_(search_model)

    places_data = AssistantHubMapsAlgo.fetch_google_places(maps_search_query[0])
    points += 0.02

    def create_map_analysis(place, title=None, urls=None, keywords=None):
        return Analysis(
            type=constants.ProjectTypeCons.enum_maps,
            address=str(place["address"]),
            map_url=str(place["google_maps_url"]),
            name=str(place["name"]),
            snippet=str(place["optimized_snippets"]),
            website=str(place.get("website")),
            title=title,
            backlinks=str(urls) if urls else None,
            keywords=str(keywords) if keywords else None,
            latitude=place["latitude"],
            longitude=place["longitude"],
        )

    set_of_keywords = set()

    def analyze_place(place, app):
        with app.app_context():
            map_model_db = (
                Analysis.query
                .filter(
                    Analysis.latitude == place["latitude"],
                    Analysis.longitude == place["longitude"],
                ).first()
            )

            new_snippet = f"Visit us at {place['name']} located at {place['address']} for the best experience."
            place["optimized_snippets"] = [new_snippet]

            response_place_data = {
                "address": place["address"],
                "google_maps_url": place["google_maps_url"],
                "name": place["name"],
                "snippets": place["optimized_snippets"],
                "website": None,
                "backlinks": None,
            }

            if place.get("website"):
                try:
                    website_data = AssistantHubMapsAlgo.fetch_website_data(place["website"])
                except Exception as e:
                    website_data = None

                if website_data is not None:
                    title, snippets, urls = website_data
                    all_text = title
                    keywords = AssistantHubMapsAlgo.process_text(all_text, place)
                    set_of_keywords.update(keywords)
                    place["optimized_snippets"] += snippets

                    response_place_data.update({
                        "website": place["website"],
                        "backlinks": len(urls),
                    })

                    if map_model_db is None:
                        map_model_db = create_map_analysis(place, title, urls, keywords)
                        add_commit_(map_model_db)
                else:
                    if map_model_db is None:
                        map_model_db = create_map_analysis(place)
                        add_commit_(map_model_db)
            else:
                if map_model_db is None:
                    map_model_db = create_map_analysis(place)
                    add_commit_(map_model_db)

            search_maps_rel_model = SearchAnalysisRel.query.filter(
                SearchAnalysisRel.search_query_id == search_model.id,
                SearchAnalysisRel.analysis_id == map_model_db.id,
            ).first()

            if search_maps_rel_model is None:
                search_maps_rel_model = SearchAnalysisRel(
                    search_query_id=search_model.id,
                    analysis_id=map_model_db.id
                )
                add_commit_(search_maps_rel_model)

            return response_place_data

    with ThreadPoolExecutor() as executor:
        response_places_data = executor.map(lambda place: analyze_place(place, app), places_data)

    response_places_data = list(response_places_data)
    geo_distribution = AssistantHubMapsAlgo.analyze_georaphic_distribution(places_data)
    
    project_data_model.maps_suggestions = {
        "keywords": list(set_of_keywords),
        "geo_distribution": geo_distribution,
    }
    purchase.points = purchase.points - math.ceil((points * 100))
    commit_()

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data=response_places_data,
        keywords=project_data_model.maps_suggestions["keywords"],
        geo_distribution=project_data_model.maps_suggestions["geo_distribution"],
    )

@internal_error_handler
def seo_analyzer_search_results(user, project_id):
    points = 0.0
    is_allowed, purchase = is_user_have_sufficient_points(user.id)

    if not is_allowed:
        return bad_response(
            message="You don't have enough points to create a project.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    if project_id is None:
        return bad_response(
            message="Project id is required",
        )

    user_id = user.id

    project_data_model = (
        SEOProject.query
        .filter(
            SEOProject.id == project_id,
            SEOProject.user_id == user_id,
        ).first()
    )

    if project_data_model is None:
        return bad_response(
            message="Project not found",
            status_code=HTTPStatus.NOT_FOUND,
        )

    if project_data_model.search_suggestion is not None:
        search_results = GoogleSearchUtils.get_data(project_id)

        return response(
            success=True,
            message=constants.SuccessMessage.seo_analysis,
            data=search_results,
            suggestion_titles=project_data_model.search_suggestion["suggestion_titles"],
        )

    query, search_model_id = GoogleSearchUtils.generate_search_query(project_data_model)
    num_pages = 1

    # 1. Search Engine Analysis
    search_results, total_point = GoogleSearchUtils.fetch_google_search_results(query, num_pages)
    points += total_point

    trending_topics = GoogleSearchUtils.keywords_titles_builder(search_results)
    with ThreadPoolExecutor() as executor:
        titles_futures = [executor.submit(GoogleSearchUtils.generate_title, keywords, user_id, current_app._get_current_object()) for keywords in trending_topics]
        titles_results = [future.result() for future in titles_futures]
        titles, total_tokens_list = zip(*titles_results)
        total_tokens_gpt4 = sum(total_tokens_list)

    points = points + ((total_tokens_gpt4 * 0.02)/1000)

    # Optimize database operations
    google_search_analyses = []
    google_search_search_rels = []

    for src in search_results:
        src_model = (
            Analysis.query.filter(
                Analysis.link == src.get("link", ""),
                Analysis.type == constants.ProjectTypeCons.enum_google_search,
            ).first()
        )

        if src_model is None:
            src_model = Analysis(
                type=constants.ProjectTypeCons.enum_google_search,
                title=src.get("title", ""),
                snippet=src.get("snippet", ""),
                link=src.get("link", ""),
                display_link=src.get("displayLink", ""),
                html_snippet=src.get("htmlSnippet", ""),
                html_title=src.get("htmlTitle", ""),
                pagemap=src.get("pagemap", ""),
                kind=src.get("kind", ""),
                html_formatted_url=src.get("htmlFormattedUrl", ""),
                formatted_url=src.get("formattedUrl", ""),
            )
            google_search_analyses.append(src_model)

    # Add and commit all new GoogleSearchAnalysis instances
    db.session.bulk_save_objects(google_search_analyses)
    db.session.commit()

    for src in search_results:
        src_model = (
            Analysis.query.filter(
                Analysis.link == src.get("link", ""),
                Analysis.type == constants.ProjectTypeCons.enum_google_search,
            ).first()
        )

        google_search_rel = (
            SearchAnalysisRel.query.filter(
                SearchAnalysisRel.analysis_id == src_model.id,
                SearchAnalysisRel.search_query_id == search_model_id
            ).first()
        )
        
        if google_search_rel is None:
            google_search_rel = SearchAnalysisRel(
                analysis_id=src_model.id,
                search_query_id=search_model_id,
            )
            google_search_search_rels.append(google_search_rel)

    # Add and commit all new GoogleSearchSearchRel instances
    db.session.bulk_save_objects(google_search_search_rels)
    db.session.commit()

    project_data_model.search_suggestion = {
        "suggestion_titles": [GoogleSearchUtils.clean_title(title) for title in titles],
    }
    purchase.points = purchase.points - math.ceil((points * 100))
    db.session.commit()

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data=search_results,
        suggestion_titles=project_data_model.search_suggestion["suggestion_titles"],
    )

@internal_error_handler
def seo_analyzer_competitors(user, project_id):
    points = 0.0
    is_allowed, purchase = is_user_have_sufficient_points(user.id)

    if not is_allowed:
        return bad_response(
            message="You don't have enough points to create a project.",
            status_code=HTTPStatus.BAD_REQUEST,
        )
    
    if project_id is None:
        return bad_response(
            message="Project id is required",
        )

    user_id = user.id
    project_data_model = (
        SEOProject.query
        .filter(
            SEOProject.id == project_id,
            SEOProject.user_id == user_id,
        ).first()
    )

    if project_data_model is None:
        return bad_response(
            message="Project not found",
            status_code=HTTPStatus.NOT_FOUND,
        )

    if project_data_model.competition_suggestion is not None:
        comptitor_analysis = CompetitorUtils.get_data(project_id)

        return response(
            success=True,
            message=constants.SuccessMessage.seo_analysis,
            data=comptitor_analysis,
            suggestion_titles=project_data_model.competition_suggestion["suggestion_titles"],
        )

    # Generate YouTube search queries using GPT-4
    try:
        competitor_search_query_arr, total_tokens_gpt4 = CompetitorUtils.generate_competitor_search_text_gpt4(
            user_id=user_id,
            business_type=project_data_model.business_type,
            target_audience=project_data_model.target_audience,
            industry=project_data_model.industry,
            location=project_data_model.country,
        )
        points = points + ((total_tokens_gpt4 * 0.02)/1000)
    except Exception as e:
        logger.exception(str(e))
        return response(
            success=False,
            message=f"Error generating search query: {str(e)}"
        )

    # Preprocess search queries
    competitor_array_of_search = DashboardUtils.preprocess_pointwise_search_array(competitor_search_query_arr)

    # Remove short search queries
    competitor_array_of_search = [query for query in competitor_array_of_search if len(query) >= 5]

    if not competitor_array_of_search:
        return response(
            success=False,
            message="Unable to generate the search query.",
        )

    # Competition Analysis
    competitor_urls, total_point = CompetitorUtils.fetch_competitors(competitor_array_of_search, project_id, project_data_model.country_code)
    points = points + total_point

    comptitor_analysis = []
    urls = []

    search_rel_dict = {}
    new_competitor_analysis = []
    new_competitor_search_rel = []

    for search_query_id, webpages in competitor_urls.items():
        for webpage in webpages:
            if webpage["link"] in urls:
                continue

            comp_anl_model = (
                Analysis.query
                .filter(
                    Analysis.link == webpage["link"], 
                    Analysis.type == constants.ProjectTypeCons.enum_competitor,
                ).first()
            )

            if comp_anl_model is None:
                comp_anl_model = Analysis(
                    type=constants.ProjectTypeCons.enum_competitor,
                    title=webpage.get("title", ""),
                    snippet=webpage.get("snippet", ""),
                    link=webpage.get("link", ""),
                    display_link=webpage.get("displayLink", ""),
                    html_snippet=webpage.get("htmlSnippet", ""),
                    html_title=webpage.get("htmlTitle", ""),
                    pagemap=webpage.get("pagemap", ""),
                    kind=webpage.get("kind", ""),
                    html_formatted_url=webpage.get("htmlFormattedUrl", ""),
                    formatted_url=webpage.get("formattedUrl", ""),
                )
                new_competitor_analysis.append(comp_anl_model)

    # Commit new CompetitorAnalysis objects to the database
    db.session.bulk_save_objects(new_competitor_analysis)
    db.session.commit()

    # Create CompetitorSearchRel objects for both new and existing CompetitorAnalysis models
    for search_query_id, webpages in competitor_urls.items():
        for webpage in webpages:
            comp_anl_model = (
                Analysis.query
                .filter(
                    Analysis.link == webpage["link"],
                    Analysis.type == constants.ProjectTypeCons.enum_competitor,
                ).first()
            )

            if not comp_anl_model:
                continue

            competitor_search_rel = (
                SearchAnalysisRel.query.filter(
                    SearchAnalysisRel.analysis_id == comp_anl_model.id,
                    SearchAnalysisRel.search_query_id == int(search_query_id)
                ).first()
            )

            if competitor_search_rel is None:
                competitor_search_rel = SearchAnalysisRel(
                    analysis_id=comp_anl_model.id,
                    search_query_id=int(search_query_id),
                )
                new_competitor_search_rel.append(competitor_search_rel)
                search_rel_dict[comp_anl_model.id] = competitor_search_rel

            comptitor_analysis.append(webpage)
            urls.append(webpage["link"])

    # Bulk insert new CompetitorSearchRel objects
    db.session.bulk_save_objects(new_competitor_search_rel)
    db.session.commit()

    # NLP Analysis
    trending_topics = CompetitorUtils.keywords_titles_builder(comptitor_analysis)

    with ThreadPoolExecutor() as executor:
        titles_futures = [executor.submit(CompetitorUtils.generate_title, user_id, keywords, current_app._get_current_object()) for keywords in trending_topics]
        titles_results = [future.result() for future in titles_futures]
        titles, total_tokens_list = zip(*titles_results)
        total_tokens_gpt4 = sum(total_tokens_list)

    points = points + ((total_tokens_gpt4 * 0.02)/1000)

    project_data_model.competition_suggestion = {
        "suggestion_titles": [AssistantHubNewsAlgo.clean_title(title) for title in titles],
    }
    purchase.points = purchase.points - math.ceil((points * 100))
    db.session.commit()

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data=comptitor_analysis,
        suggestion_titles=project_data_model.competition_suggestion["suggestion_titles"],
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
    num_pages = 1

    # Online Social Forum Analysis
    # TODO: Change this to a subreddit of the user's choice
    subreddit_name = "photography"

    analysis = AssistantHubSEO.analyze_reddit_subreddit(subreddit_name)
    subreddit_text_data = [post.get(
        "title", "") + " " + post.get("body", "") for post in analysis["posts"]]

    # NLP Analysis
    semantic_keywords_and_topics = AssistantHubSEO.get_lsi_topic_and_keywords(
        subreddit_text_data, num_topics=5)
    long_tail_keywords = AssistantHubSEO.get_long_tail_keywords(
        subreddit_text_data, max_keywords=50, n_components=20)

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        data=analysis.get("posts", []),
        semantic_topics=semantic_keywords_and_topics["topics"],
        long_tail_keywords=long_tail_keywords,
        lsi_keywords=semantic_keywords_and_topics["keywords"],
    )


@internal_error_handler
def generate_content_for_social_media(user, topic, platform, keywords, length, urls, user_ip):
    is_allowed, purchase = is_user_have_sufficient_points(user.id)

    if not is_allowed:
        return bad_response(
            message="You don't have enough points to create a project.",
            status_code=HTTPStatus.BAD_REQUEST,
        )

    points = 0.0
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

    is_opinion, total_tokens = ClassifierModels.is_the_topic_opinion_based(
        processed_input['topic'],
    )

    # Cost of Classification
    points = points + ((total_tokens * 0.02)/1000)

    if is_opinion:
        web_searched_results, total_point = AssistantHubScrapper.search_and_crawl(
            processed_input['topic'],
            user_ip,
        )

        # Cost of Crawl
        points = points + total_point

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
        assistant_response, total_tokens = GeneratorModels.generate_content(
            user, system_message, user_message
        )

        # Cost of Generation
        points = points + ((total_tokens * 0.03)/1000)

        ContentDataModel.update_content_model_after_successful_ai_response(
            assistant_response, content_data
        )
    except Exception as e:
        assistant_response = None
        ContentDataModel.update_content_model_after_failed_ai_response(
            content_data
        )

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

    purchase.points = purchase.points - math.ceil((points * 100))
    db.session.commit()

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
        assistant_response = GeneratorModels.generate_content(
            user, system_message, user_message)
        ContentDataModel.update_content_model_after_successful_ai_response(
            assistant_response, content_data)
    except Exception as e:
        assistant_response = None
        ContentDataModel.update_content_model_after_failed_ai_response(
            content_data)

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
def seo_history(user, page=1, per_page=10):
    seo_projects = (
        SEOProject.query.filter(
            SEOProject.user_id == user.id,
        )
        .order_by(SEOProject.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    # response_data_for_projects = []
    # for project in seo_projects:
    #     searches = (
    #         SearchQuery.query.filter(
    #             SearchQuery.user_id == user.id,
    #             SearchQuery.seo_project_id == project.id,
    #         ).all()
    #     )

    #     searches_ids = [search.id for search in searches]

    #     analysis_data = (
    #         SearchAnalysisRel.query.filter(
    #             SearchAnalysisRel.search_query_id.in_(searches_ids),
    #         )
    #     )

    #     analysis_ids = [analysis.id for analysis in analysis_data]

    #     analysis_data = (
    #         Analysis.query.filter(
    #             Analysis.id.in_(analysis_ids),
    #         ).all()
    #     )

    #     news_data = []
    #     competitors_data = []
    #     search_data = []
    #     maps_data = []

    #     for analysis in analysis_data:
    #         if analysis.type == constants.ProjectTypeCons.enum_news:
    #             response = {
    #                 "id": analysis.id,
    #                 "title": analysis.title,
    #                 "htmlTitle": analysis.html_title,
    #                 "displayLink": analysis.display_link,
    #                 "formattedUrl": analysis.formatted_url,
    #                 "htmlSnippet": analysis.snippet,
    #                 "kind":analysis.kind,
    #                 "link":analysis.link,
    #                 "pagemap":analysis.pagemap,
    #             }

    #             news_data.append(response)
            
    #         elif analysis.type == constants.ProjectTypeCons.enum_competitor:
    #             response = {
    #                 "id": analysis.id,
    #                 "title": analysis.title,
    #                 "snippet": analysis.snippet,
    #                 "link":analysis.link,
    #                 "displayLink": analysis.display_link,
    #                 "htmlSnippet": analysis.html_snippet,
    #                 "htmlTitle": analysis.html_title,
    #                 "pagemap":analysis.pagemap,
    #                 "kind":analysis.kind,
    #                 "htmlFormattedUrl": analysis.html_formatted_url,
    #                 "formattedUrl": analysis.formatted_url,
    #             }

    #             competitors_data.append(response)

    #         elif analysis.type == constants.ProjectTypeCons.enum_google_search:
    #             response = {
    #                 "id": analysis.id,
    #                 "title": analysis.title,
    #                 "snippet": analysis.snippet,
    #                 "link":analysis.link,
    #                 "displayLink": analysis.display_link,
    #                 "htmlSnippet": analysis.html_snippet,
    #                 "htmlTitle": analysis.html_title,
    #                 "pagemap":analysis.pagemap,
    #                 "kind":analysis.kind,
    #                 "htmlFormattedUrl": analysis.html_formatted_url,
    #                 "formattedUrl": analysis.formatted_url,
    #             }

    #             search_data.append(response)

    #         elif analysis.type == constants.ProjectTypeCons.enum_maps:
    #             response = {
    #                 "id": analysis.id,
    #                 "title": analysis.title,
    #                 "address": analysis.address,
    #                 "google_maps_url": analysis.map_url,
    #                 "name": analysis.name,
    #                 "optimized_snippets": analysis.snippet,
    #                 "website": analysis.website,
    #                 "backlinks": analysis.backlinks,
    #                 "keywords": analysis.keywords,
    #                 "latitude": analysis.latitude,
    #                 "longitude": analysis.longitude,
    #             }

    #             maps_data.append(response)
        
    #     response_data_for_projects.append({
    #         "id": project.id,
    #         "news_data": news_data,
    #         "news_suggestion_titles": project.news_suggestions,
    #         "competitors_data": competitors_data,
    #         "competitors_suggestion_titles": project.competition_suggestion,
    #         "search_data": search_data,
    #         "search_suggestion_titles": project.search_suggestion,
    #         "maps_data": maps_data,
    #         "maps_suggestions": project.maps_suggestions,
    #     })

    return response(
        success=True,
        message=constants.SuccessMessage.seo_analysis,
        pagination={
            "page": seo_projects.page,
            "per_page": seo_projects.per_page,
            "total_pages": seo_projects.pages,
            "total_items": seo_projects.total,
        },
        seo_projects=[{
            "content_id": project.id,
            "created_at": TimeUtils.time_ago(project.created_at),
            "type": "SEO",
            "topic": project.business_type,
            "length": project.industry,
            "model_response": "",
            "html_form": "",
        }
        for project in seo_projects.items
        ],
    )


@internal_error_handler
def content_history(user, page=1, per_page=10):
    contents_data = (
        Content.query.filter(
            Content.user_id == user.id,
            Content.content_data != None,
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
