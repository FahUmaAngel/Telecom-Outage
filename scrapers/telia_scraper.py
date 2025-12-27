"""
Telia Scraper with Automatic Fallback
Primary: Selenium V3 (faster, more reliable)
Fallback: Playwright (if Selenium fails)
"""
import json
import logging
from typing import Dict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_telia_with_fallback() -> Dict:
    """
    Scrape Telia outages with automatic fallback.
    
    Strategy:
    1. Try Selenium V3 first (faster, more reliable)
    2. If Selenium fails, fallback to Playwright
    3. Return results from whichever method succeeds
    
    Returns:
        Dict with outages, method used, and success status
    """
    logger.info("="*60)
    logger.info("Telia Scraper with Automatic Fallback")
    logger.info("="*60)
    
    result = {
        'outages': [],
        'timestamp': datetime.now().isoformat(),
        'success': False,
        'method': None,
        'fallback_used': False,
        'errors': []
    }
    
    # Method 1: Try Selenium V3 first
    logger.info("\n[Primary] Attempting Selenium V3...")
    try:
        from telia_selenium_v3 import scrape_with_selenium_v3
        
        selenium_result = scrape_with_selenium_v3()
        
        if selenium_result.get('success') and len(selenium_result.get('outages', [])) > 0:
            logger.info(f"✓ Selenium V3 succeeded: {len(selenium_result['outages'])} outages")
            result['outages'] = selenium_result['outages']
            result['success'] = True
            result['method'] = 'selenium_v3'
            result['fallback_used'] = False
            return result
        else:
            error_msg = f"Selenium returned no data: {selenium_result.get('error', 'Unknown error')}"
            logger.warning(f"⚠ {error_msg}")
            result['errors'].append({'method': 'selenium_v3', 'error': error_msg})
            
    except ImportError as e:
        error_msg = f"Selenium not available: {e}"
        logger.warning(f"⚠ {error_msg}")
        result['errors'].append({'method': 'selenium_v3', 'error': error_msg})
    except Exception as e:
        error_msg = f"Selenium failed: {e}"
        logger.error(f"✗ {error_msg}")
        result['errors'].append({'method': 'selenium_v3', 'error': str(e)})
    
    # Method 2: Fallback to Playwright
    logger.info("\n[Fallback] Attempting Playwright...")
    try:
        from telia_playwright import scrape_with_playwright
        
        playwright_result = scrape_with_playwright()
        
        if playwright_result.get('success') and len(playwright_result.get('outages', [])) > 0:
            logger.info(f"✓ Playwright succeeded: {len(playwright_result['outages'])} outages")
            result['outages'] = playwright_result['outages']
            result['success'] = True
            result['method'] = 'playwright'
            result['fallback_used'] = True
            return result
        else:
            error_msg = f"Playwright returned no data: {playwright_result.get('error', 'Unknown error')}"
            logger.warning(f"⚠ {error_msg}")
            result['errors'].append({'method': 'playwright', 'error': error_msg})
            
    except ImportError as e:
        error_msg = f"Playwright not available: {e}"
        logger.warning(f"⚠ {error_msg}")
        result['errors'].append({'method': 'playwright', 'error': error_msg})
    except Exception as e:
        error_msg = f"Playwright failed: {e}"
        logger.error(f"✗ {error_msg}")
        result['errors'].append({'method': 'playwright', 'error': str(e)})
    
    # Both methods failed
    logger.error("\n✗ Both methods failed!")
    logger.error(f"Errors: {json.dumps(result['errors'], indent=2)}")
    
    return result


if __name__ == "__main__":
    # Run scraper with fallback
    results = scrape_telia_with_fallback()
    
    # Save results
    output_file = "telia_scraper_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Display summary
    logger.info("\n" + "="*60)
    logger.info("SCRAPING SUMMARY")
    logger.info("="*60)
    logger.info(f"Status: {'✓ SUCCESS' if results['success'] else '✗ FAILED'}")
    logger.info(f"Method Used: {results['method']}")
    logger.info(f"Fallback Used: {'Yes' if results['fallback_used'] else 'No'}")
    logger.info(f"Outages Found: {len(results['outages'])}")
    
    if results['errors']:
        logger.info(f"\nErrors Encountered: {len(results['errors'])}")
        for err in results['errors']:
            logger.info(f"  - {err['method']}: {err['error'][:100]}")
    
    logger.info(f"\n✓ Results saved to: {output_file}")
    
    if results['outages']:
        logger.info(f"\n📊 Sample outages (showing first 5):")
        for i, outage in enumerate(results['outages'][:5], 1):
            logger.info(f"  {i}. {outage['incident_id']}")
        
        if len(results['outages']) > 5:
            logger.info(f"  ... and {len(results['outages']) - 5} more")
    
    # Exit with appropriate code
    exit(0 if results['success'] else 1)
