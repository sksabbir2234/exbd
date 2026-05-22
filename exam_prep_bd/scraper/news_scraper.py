import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import logging
from typing import List, Dict, Optional, Tuple
import asyncio
import random
from urllib.parse import urljoin

from database.session import get_db_session
from models import Article, Source, Category, Tag, ScrapeLog, ArticleTag
from utils.auth import generate_slug

logger = logging.getLogger(__name__)


# User agents for rotation to avoid blocking
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
]


class NewsScraper:
    """News scraper for Bangladeshi news sources."""
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
    
    def _get_random_headers(self) -> Dict[str, str]:
        """Get random headers with rotated user agent."""
        headers = self.headers.copy()
        headers["User-Agent"] = random.choice(USER_AGENTS)
        return headers
    
    async def fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content with retry logic."""
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self._get_random_headers(),
            follow_redirects=True
        ) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                return None
    
    async def scrape_rss_feed(self, source: Source) -> List[Dict]:
        """Scrape articles from RSS feed."""
        if not source.rss_feed_url:
            return []
        
        try:
            # Add jitter delay (1-3 seconds)
            await asyncio.sleep(random.uniform(1, 3))
            
            content = await self.fetch_url(source.rss_feed_url)
            if not content:
                return []
            
            feed = feedparser.parse(content)
            articles = []
            
            for entry in feed.entries[:20]:  # Limit to 20 articles per source
                article = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published"),
                    "summary": entry.get("summary", ""),
                    "content": "",
                    "author": entry.get("author", ""),
                    "image_url": ""
                }
                
                # Try to extract image from enclosures or media_content
                if hasattr(entry, "enclosures"):
                    for enclosure in entry.enclosures:
                        if enclosure.get("type", "").startswith("image/"):
                            article["image_url"] = enclosure.get("href", "")
                            break
                
                if hasattr(entry, "media_content"):
                    for media in entry.media_content:
                        if media.get("medium") == "image":
                            article["image_url"] = media.get("url", "")
                            break
                
                articles.append(article)
            
            logger.info(f"Found {len(articles)} articles from RSS feed: {source.name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping RSS feed for {source.name}: {e}")
            return []
    
    async def scrape_website(self, source: Source) -> List[Dict]:
        """Scrape articles directly from website (fallback when RSS not available)."""
        try:
            # Add jitter delay (1-3 seconds)
            await asyncio.sleep(random.uniform(1, 3))
            
            content = await self.fetch_url(source.url)
            if not content:
                return []
            
            soup = BeautifulSoup(content, "html.parser")
            articles = []
            
            # This is a generic scraper - each source needs custom selectors
            # For production, implement source-specific scrapers
            headline_links = soup.find_all("a", href=True)
            
            for link in headline_links[:30]:  # Limit to 30 links
                href = link.get("href", "")
                text = link.get_text(strip=True)
                
                # Filter for article-like links
                if len(text) > 20 and len(text) < 200:
                    article_url = urljoin(source.url, href)
                    
                    # Skip non-article pages
                    if any(skip in article_url.lower() for skip in ["/category/", "/tag/", "/author/", "/page/"]):
                        continue
                    
                    articles.append({
                        "title": text,
                        "link": article_url,
                        "published": None,
                        "summary": "",
                        "content": "",
                        "author": "",
                        "image_url": ""
                    })
            
            logger.info(f"Found {len(articles)} potential articles from website: {source.name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping website for {source.name}: {e}")
            return []
    
    async def fetch_article_content(self, url: str) -> Optional[Dict]:
        """Fetch full article content from URL."""
        try:
            # Add jitter delay
            await asyncio.sleep(random.uniform(1, 2))
            
            content = await self.fetch_url(url)
            if not content:
                return None
            
            soup = BeautifulSoup(content, "html.parser")
            
            # Extract title
            title = soup.find("h1")
            title_text = title.get_text(strip=True) if title else ""
            
            # Extract content (generic - needs source-specific implementation)
            article_body = soup.find("article") or soup.find("div", class_=lambda x: x and "content" in x.lower())
            content_text = ""
            if article_body:
                paragraphs = article_body.find_all("p")
                content_text = "\n".join([p.get_text(strip=True) for p in paragraphs])
            
            # Extract image
            image = soup.find("img", class_=lambda x: x and ("featured" in x.lower() or "main" in x.lower()))
            image_url = image.get("src", "") if image else ""
            
            return {
                "title": title_text,
                "content": content_text,
                "image_url": image_url
            }
            
        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {e}")
            return None
    
    async def save_article(
        self,
        db_session,
        article_data: Dict,
        source: Source,
        category: Optional[Category] = None
    ) -> Optional[Article]:
        """Save article to database."""
        try:
            # Check if article already exists
            existing = db_session.query(Article).filter(
                Article.source_url == article_data["link"]
            ).first()
            
            if existing:
                return existing
            
            # Generate slug
            slug = generate_slug(article_data["title"])
            
            # Parse published date
            published_at = None
            if article_data.get("published"):
                try:
                    published_at = datetime.fromisoformat(article_data["published"].replace("Z", "+00:00"))
                except:
                    published_at = datetime.now(timezone.utc)
            
            # Create article
            article = Article(
                source_id=source.id,
                category_id=category.id if category else None,
                title=article_data["title"],
                slug=slug,
                summary=article_data.get("summary", "")[:500],
                content=article_data.get("content", ""),
                author=article_data.get("author", ""),
                published_at=published_at,
                image_url=article_data.get("image_url", ""),
                source_url=article_data["link"],
                language=source.language,
                is_active=True
            )
            
            db_session.add(article)
            db_session.commit()
            db_session.refresh(article)
            
            logger.info(f"Saved article: {article.title[:50]}...")
            return article
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error saving article: {e}")
            return None
    
    async def scrape_source(self, source_id: int) -> Tuple[int, int]:
        """Scrape a single source and save articles."""
        db_session = next(get_db_session())
        articles_found = 0
        articles_saved = 0
        
        try:
            source = db_session.query(Source).filter(Source.id == source_id).first()
            if not source or not source.is_active:
                return 0, 0
            
            logger.info(f"Starting scrape for: {source.name}")
            
            # Create scrape log
            scrape_log = ScrapeLog(
                source_id=source.id,
                status="running",
                started_at=datetime.now(timezone.utc)
            )
            db_session.add(scrape_log)
            db_session.commit()
            
            # Try RSS first, then fallback to website scraping
            if source.rss_feed_url:
                articles = await self.scrape_rss_feed(source)
            else:
                articles = await self.scrape_website(source)
            
            articles_found = len(articles)
            
            # Get default category
            default_category = db_session.query(Category).filter(
                Category.slug == "news"
            ).first()
            
            # Save articles
            for article_data in articles:
                saved_article = await self.save_article(
                    db_session, article_data, source, default_category
                )
                if saved_article:
                    articles_saved += 1
            
            # Update source last_scraped_at
            source.last_scraped_at = datetime.now(timezone.utc)
            
            # Update scrape log
            scrape_log.status = "success"
            scrape_log.articles_found = articles_found
            scrape_log.articles_saved = articles_saved
            scrape_log.completed_at = datetime.now(timezone.utc)
            scrape_log.duration_seconds = (scrape_log.completed_at - scrape_log.started_at).total_seconds()
            
            db_session.commit()
            logger.info(f"Completed scrape for {source.name}: {articles_saved}/{articles_found} saved")
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error scraping source {source_id}: {e}")
            
            # Update scrape log with error
            if 'scrape_log' in locals():
                scrape_log.status = "failed"
                scrape_log.error_message = str(e)
                scrape_log.completed_at = datetime.now(timezone.utc)
                db_session.commit()
        
        finally:
            db_session.close()
        
        return articles_found, articles_saved
    
    async def scrape_all_sources(self):
        """Scrape all active sources."""
        db_session = next(get_db_session())
        
        try:
            sources = db_session.query(Source).filter(
                Source.is_active == True
            ).order_by(Source.scrape_priority.desc()).all()
            
            logger.info(f"Starting batch scrape for {len(sources)} sources")
            
            # Scrape sources concurrently with limit
            semaphore = asyncio.Semaphore(3)  # Max 3 concurrent scrapes
            
            async def scrape_with_semaphore(source):
                async with semaphore:
                    return await self.scrape_source(source.id)
            
            tasks = [scrape_with_semaphore(source) for source in sources]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_found = sum(r[0] if isinstance(r, tuple) else 0 for r in results)
            total_saved = sum(r[1] if isinstance(r, tuple) else 0 for r in results)
            
            logger.info(f"Batch scrape completed: {total_saved}/{total_found} articles saved")
            
        except Exception as e:
            logger.error(f"Error in batch scrape: {e}")
        finally:
            db_session.close()


# Global scraper instance
scraper = NewsScraper()


async def run_scrape_job():
    """Job function to run scheduled scraping."""
    logger.info("Running scheduled scrape job")
    await scraper.scrape_all_sources()
