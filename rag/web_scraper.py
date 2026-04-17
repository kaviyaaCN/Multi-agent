"""
rag/web_scraper.py
==================
Fetches web documents via Tavily API and stores them in data/documents/
for RAG ingestion and plagiarism checking.
"""

from utils.config import settings
from utils.logger import logger

def fetch_domain_documents(query: str, max_results: int = 5) -> int:
    """Scrape web pages using Tavily and save as TXT files in data/documents."""
    api_key = settings.tavily_api_key
    if not api_key:
        logger.warning("Tavily API key not configured. Web context gathering skipped.")
        return 0

    try:
        from tavily import TavilyClient
    except ImportError:
        logger.error("tavily-python is not installed.")
        return 0

    client = TavilyClient(api_key=api_key)
    logger.info(f"Fetching context from Tavily for query: {query}")

    try:
        # We need raw_content so we have text to index
        response = client.search(
            query=query, 
            search_depth="advanced", 
            include_raw_content=True, 
            max_results=max_results
        )
    except Exception as exc:
        logger.error(f"Tavily search failed: {exc}")
        return 0

    results = response.get("results", [])
    if not results:
        logger.warning(f"No documents found on Tavily for: {query}")
        return 0

    docs_dir = settings.docs_dir
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    saved_count = 0
    for idx, r in enumerate(results):
        content = r.get("raw_content") or r.get("content")
        if content:
            safe_title = "".join(c if c.isalnum() else "_" for c in r.get("title", f"tavily_doc_{idx}"))
            safe_title = safe_title[:50]
            filepath = docs_dir / f"{safe_title}_{idx}.txt"
            
            doc_text = f"Title: {r.get('title', 'Unknown')}\nURL: {r.get('url', 'Unknown')}\n\n{content}"
            # Write to data/documents/ so RAG/FAISS can index it
            try:
                filepath.write_text(doc_text, encoding="utf-8", errors="ignore")
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving tavily document {filepath}: {e}")

    logger.info(f"Saved {saved_count} web documents to {docs_dir}")
    return saved_count
