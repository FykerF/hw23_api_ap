from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from core.config import get_base_url

class Link(Base):
    __tablename__ = "links"

    id = Column(String, primary_key=True, index=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String, unique=True, index=True, nullable=False)
    custom_alias = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # User relationship (can be null for anonymous links)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="links")

    # Create an index on original_url for faster searches
    __table_args__ = (
        Index('idx_original_url', original_url),
    )

    @property
    def short_url(self):
        """Generate the full short URL"""
        return f"{get_base_url()}/{self.short_code}"
        
    @property
    def is_expired(self):
        """Check if the link is expired"""
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        # Make sure we use UTC timezone for both
        now = datetime.now(timezone.utc)
        return now > self.expires_at
        
    def to_dict(self):
        """Convert link to dictionary representation"""
        return {
            "id": self.id,
            "short_code": self.short_code,
            "short_url": self.short_url,
            "original_url": self.original_url,
            "custom_alias": self.custom_alias,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "access_count": self.access_count,
            "is_active": self.is_active,
            "user_id": self.user_id
        }
        
    def to_stats_dict(self):
        """Convert link to stats dictionary"""
        return {
            "short_code": self.short_code,
            "original_url": self.original_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "access_count": self.access_count,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None
        }