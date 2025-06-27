# This file has been deprecated. 
# All User model functionality has been moved to src/models/database.py
# This file is kept for backward compatibility and can be removed in future versions.

from src.models.database import User, db

# Re-export for backward compatibility
__all__ = ['User', 'db']
