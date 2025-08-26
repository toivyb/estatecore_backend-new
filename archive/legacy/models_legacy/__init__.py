# estatecore_backend/models/__init__.py
# Fixed to use the single db instance from estatecore_backend

from estatecore_backend import db

from .user import User
from .rent import Rent
# Import any other models here
