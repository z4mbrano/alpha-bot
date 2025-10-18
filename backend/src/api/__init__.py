"""
API Module
Exporta todos os blueprints da API
"""

from .alphabot import alphabot_bp
from .drivebot import drivebot_bp
from .health import health_bp

__all__ = ['alphabot_bp', 'drivebot_bp', 'health_bp']
