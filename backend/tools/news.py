"""
News API integration for fetching news about cities and travel destinations
"""

import os
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_news(
    query: str,
    location: Optional[str] = None,
    num_articles: int = 5,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Fetch news articles related to a location or topic

    Args:
        query: The search query (e.g., "tourism", "events", "attractions")
        location: City or location to focus on (e.g., "Paris", "Tokyo")
        num_articles: Number of articles to return (max 10)
        language: Language code (default: "en")

    Returns:
        Dict containing news articles and metadata
    """
    try:
        api_key = os.getenv("NEWS_API_KEY")
        if not api_key:
            logger.error("NEWS_API_KEY not found in environment variables")
            return {
                "error": "News API key not configured",
                "articles": []
            }

        # Build search query
        if location:
            search_query = f"{location} {query}"
        else:
            search_query = query

        # Calculate date range (last 30 days)
        to_date = datetime.now()
        from_date = to_date - timedelta(days=30)

        # NewsAPI endpoint
        url = "https://newsapi.org/v2/everything"

        # Request parameters
        params = {
            "q": search_query,
            "apiKey": api_key,
            "language": language,
            "sortBy": "relevancy",
            "pageSize": min(num_articles, 10),
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d")
        }

        # Make API request
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            logger.error(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            return {
                "error": data.get("message", "Failed to fetch news"),
                "articles": []
            }

        # Process articles
        articles = []
        for article in data.get("articles", [])[:num_articles]:
            processed_article = {
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "publishedAt": article.get("publishedAt", ""),
                "author": article.get("author", "Unknown")
            }

            # Clean up the data
            if processed_article["title"] and processed_article["title"] != "[Removed]":
                articles.append(processed_article)

        return {
            "query": search_query,
            "location": location,
            "total_results": len(articles),
            "articles": articles,
            "language": language
        }

    except requests.exceptions.Timeout:
        logger.error("NewsAPI request timeout")
        return {
            "error": "Request timeout - please try again",
            "articles": []
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"NewsAPI request error: {e}")
        return {
            "error": f"Failed to fetch news: {str(e)}",
            "articles": []
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_news: {e}")
        return {
            "error": f"An unexpected error occurred: {str(e)}",
            "articles": []
        }


def get_top_headlines(
    location: str,
    category: Optional[str] = None,
    num_articles: int = 5
) -> Dict[str, Any]:
    """
    Fetch top headlines for a specific location

    Args:
        location: Country code (e.g., "us", "gb", "fr")
        category: Category filter (business, entertainment, general, health, science, sports, technology)
        num_articles: Number of articles to return

    Returns:
        Dict containing top headlines
    """
    try:
        api_key = os.getenv("NEWS_API_KEY")
        if not api_key:
            logger.error("NEWS_API_KEY not found in environment variables")
            return {
                "error": "News API key not configured",
                "articles": []
            }

        # NewsAPI top headlines endpoint
        url = "https://newsapi.org/v2/top-headlines"

        # Map common location names to country codes
        country_codes = {
            "united states": "us",
            "usa": "us",
            "america": "us",
            "united kingdom": "gb",
            "uk": "gb",
            "britain": "gb",
            "france": "fr",
            "germany": "de",
            "japan": "jp",
            "canada": "ca",
            "australia": "au",
            "india": "in",
            "italy": "it",
            "spain": "es",
            "netherlands": "nl",
            "brazil": "br",
            "mexico": "mx"
        }

        # Try to get country code
        country = country_codes.get(location.lower(), location.lower())

        # Request parameters
        params = {
            "apiKey": api_key,
            "country": country if len(country) == 2 else "us",
            "pageSize": min(num_articles, 10)
        }

        if category:
            params["category"] = category

        # Make API request
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("status") != "ok":
            # Fallback to everything endpoint if top-headlines fails
            return get_news(
                query="travel tourism attractions",
                location=location,
                num_articles=num_articles
            )

        # Process articles
        articles = []
        for article in data.get("articles", [])[:num_articles]:
            processed_article = {
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "source": article.get("source", {}).get("name", "Unknown"),
                "url": article.get("url", ""),
                "publishedAt": article.get("publishedAt", ""),
                "author": article.get("author", "Unknown")
            }

            if processed_article["title"] and processed_article["title"] != "[Removed]":
                articles.append(processed_article)

        return {
            "location": location,
            "country_code": country,
            "category": category,
            "total_results": len(articles),
            "articles": articles,
            "type": "headlines"
        }

    except Exception as e:
        logger.error(f"Error fetching top headlines: {e}")
        # Fallback to general news search
        return get_news(
            query="travel tourism",
            location=location,
            num_articles=num_articles
        )