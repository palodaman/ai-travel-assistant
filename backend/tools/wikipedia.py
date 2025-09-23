import wikipedia
from cache import cache_get, cache_set, key_for
import json

def search_wikipedia(query: str, sentences: int = 3):
    """
    Search Wikipedia for a given query and return a summary using wikipedia-api library.

    Args:
        query: The search term or page title
        sentences: Number of sentences to return in the summary (default 3)

    Returns:
        Dictionary containing title, summary, URL, and other metadata
    """
    # Check cache first
    cache_params = {"query": query, "sentences": sentences}
    cache_key = key_for("wikipedia", cache_params)
    if cached := cache_get(cache_key):
        return json.loads(cached)

    try:
        # Set language to English
        wikipedia.set_lang("en")

        # Search for the query
        search_results = wikipedia.search(query, results=5)

        if not search_results:
            # No results found
            result = {
                "error": f"No Wikipedia articles found for '{query}'",
                "query": query,
                "success": False,
                "suggestion": "Try a different search term or check the spelling"
            }
            cache_set(cache_key, result, ttl=300)
            return result

        # Try to get the page, starting with the first search result
        page = None
        page_title = None

        # First try exact match
        try:
            page = wikipedia.page(query)
            page_title = query
        except (wikipedia.DisambiguationError, wikipedia.PageError):
            # If exact match fails, try search results
            for result_title in search_results:
                try:
                    page = wikipedia.page(result_title)
                    page_title = result_title
                    break
                except (wikipedia.DisambiguationError, wikipedia.PageError):
                    continue

        if not page:
            # Handle disambiguation or try simplified search
            if "trends" in query.lower() or "latest" in query.lower() or "current" in query.lower():
                # Extract the main topic
                words = query.lower().replace("latest", "").replace("trends", "").replace("current", "").replace("in", "").strip().split()
                if words:
                    simplified_query = " ".join(words).strip()
                    if simplified_query != query:
                        return search_wikipedia(simplified_query, sentences)

            result = {
                "error": f"Could not retrieve Wikipedia article for '{query}'",
                "query": query,
                "suggestions": search_results[:3] if search_results else [],
                "success": False
            }
            cache_set(cache_key, result, ttl=300)
            return result

        # Get summary with specified number of sentences
        summary = wikipedia.summary(page_title, sentences=sentences)

        # Get page images
        images = page.images[:3] if hasattr(page, 'images') else []

        # Build result
        result = {
            "title": page.title,
            "summary": summary,
            "url": page.url,
            "categories": page.categories[:5] if hasattr(page, 'categories') else [],
            "images": images,
            "references": page.references[:5] if hasattr(page, 'references') else [],
            "success": True
        }

        # Cache for 1 hour
        cache_set(cache_key, result, ttl=3600)
        return result

    except wikipedia.DisambiguationError as e:
        # Multiple pages found, return options
        result = {
            "error": f"Multiple Wikipedia articles found for '{query}'",
            "query": query,
            "suggestions": e.options[:5],
            "success": False,
            "message": "Please be more specific or choose from the suggestions"
        }
        cache_set(cache_key, result, ttl=300)
        return result

    except wikipedia.PageError:
        result = {
            "error": f"No Wikipedia page exists for '{query}'",
            "query": query,
            "success": False
        }
        cache_set(cache_key, result, ttl=300)
        return result

    except Exception as e:
        return {
            "error": f"Error accessing Wikipedia: {str(e)}",
            "query": query,
            "success": False
        }