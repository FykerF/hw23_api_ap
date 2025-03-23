import random
import string
from sqlalchemy.orm import Session

from core.config import settings
from api.models.links import Link

def generate_short_code(db: Session) -> str:
    """
    Generate a unique short code for a link.
    
    Args:
        db: Database session
        
    Returns:
        A unique short code string
    """
    while True:
        # Define characters to use for the short code (alphanumeric)
        chars = string.ascii_letters + string.digits
        
        # Generate random short code of the configured length
        short_code = ''.join(random.choice(chars) for _ in range(settings.SHORTCODE_LENGTH))
        
        # Check if the short code already exists in the database
        existing_link = db.query(Link).filter(Link.short_code == short_code).first()
        
        # If the short code is unique, return it
        if not existing_link:
            return short_code

def is_custom_alias_available(db: Session, custom_alias: str) -> bool:
    """
    Check if a custom alias is available for use.
    
    Args:
        db: Database session
        custom_alias: The custom alias to check
        
    Returns:
        True if the alias is available, False otherwise
    """
    existing_link = db.query(Link).filter(Link.short_code == custom_alias).first()
    return existing_link is None

def validate_custom_alias(custom_alias: str) -> bool:
    """
    Validate if a custom alias meets the requirements.
    
    Args:
        custom_alias: The custom alias to validate
        
    Returns:
        True if the alias is valid, False otherwise
    """
    # Check if the alias only contains alphanumeric chars, hyphens, and underscores
    import re
    pattern = r'^[a-zA-Z0-9_-]+$'
    
    # Check if alias is too short or too long (between 3 and 20 chars)
    if not 3 <= len(custom_alias) <= 20:
        return False
        
    # Check if alias matches the pattern
    if not re.match(pattern, custom_alias):
        return False
        
    # Check if alias is a reserved word (e.g., 'api', 'admin', 'links', etc.)
    reserved_words = ['api', 'admin', 'auth', 'links', 'stats', 'search', 'shorten']
    if custom_alias.lower() in reserved_words:
        return False
        
    return True