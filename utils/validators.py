import re
import validators

def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL
    
    Args:
        url: The URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Use validators library for URL validation
    return validators.url(url)

def validate_email(email: str) -> bool:
    """
    Validate if a string is a valid email
    
    Args:
        email: The email to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Use validators library for email validation
    return validators.email(email)

def validate_username(username: str) -> bool:
    """
    Validate if a string is a valid username
    
    Args:
        username: The username to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Username must be 3-20 characters and contain only alphanumeric, underscore, or hyphen
    pattern = r'^[a-zA-Z0-9_-]{3,20}$'
    return bool(re.match(pattern, username))

def validate_password(password: str) -> bool:
    """
    Validate if a string is a valid password
    
    Args:
        password: The password to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Password must be at least 8 characters
    return len(password) >= 8