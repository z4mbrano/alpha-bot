"""
Health Check API Routes
Endpoint para verificação de saúde do sistema
"""

from flask import Blueprint, jsonify

# Criar blueprint
health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health():
    """
    Endpoint de health check.
    
    Retorna status do sistema.
    
    Returns:
        JSON com status 'ok'
    """
    return jsonify({"status": "ok"}), 200
