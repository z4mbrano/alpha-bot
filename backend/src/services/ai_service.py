"""
AI Service
Gerencia comunicação com Google Gemini AI
"""

from typing import Any, Dict, List, Optional
import google.generativeai as genai

from ..config.settings import DRIVEBOT_API_KEY, ALPHABOT_API_KEY
from ..prompts import ALPHABOT_SYSTEM_PROMPT, DRIVEBOT_SYSTEM_PROMPT


class AIService:
    """Serviço para interações com Google Gemini AI."""
    
    def __init__(self, bot_type: str = 'drivebot'):
        """
        Inicializa o serviço de IA.
        
        Args:
            bot_type: Tipo do bot ('drivebot' ou 'alphabot')
        
        Raises:
            ValueError: Se bot_type for inválido
            RuntimeError: Se a API key não estiver configurada
        """
        self.bot_type = bot_type.lower()
        
        if self.bot_type not in ('drivebot', 'alphabot'):
            raise ValueError(f"Bot type inválido: {bot_type}. Use 'drivebot' ou 'alphabot'.")
        
        # Configurar API key apropriada
        self.api_key = DRIVEBOT_API_KEY if self.bot_type == 'drivebot' else ALPHABOT_API_KEY
        
        if not self.api_key:
            raise RuntimeError(
                f"API key não configurada para {self.bot_type}. "
                f"Defina {'DRIVEBOT_API_KEY' if self.bot_type == 'drivebot' else 'ALPHABOT_API_KEY'} "
                "no arquivo .env"
            )
        
        genai.configure(api_key=self.api_key)
        
        # Configurar system prompt apropriado
        self.system_prompt = DRIVEBOT_SYSTEM_PROMPT if self.bot_type == 'drivebot' else ALPHABOT_SYSTEM_PROMPT
        
        # Criar modelo
        self.model = self._create_model()
    
    def _create_model(self) -> genai.GenerativeModel:
        """
        Cria instância do modelo Gemini com configurações apropriadas.
        
        Returns:
            Modelo configurado do Gemini
        """
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            },
        ]
        
        # Selecionar modelo por bot, com fallback seguro
        preferred_models = []
        if self.bot_type == 'alphabot':
            # Pedido do usuário: usar Gemini 2.5 Flash para AlphaBot
            preferred_models = [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-1.5-flash",
            ]
        else:
            # DriveBot permanece estável para evitar mudanças inesperadas
            preferred_models = [
                "gemini-1.5-flash",
                "gemini-2.0-flash",
                "gemini-2.5-flash",
            ]

        last_error = None
        for model_name in preferred_models:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    system_instruction=self.system_prompt,
                )
                # Tentativa leve: contar tokens de uma string curta para validar compatibilidade
                try:
                    _ = model.count_tokens("ping")
                except Exception:
                    # Mesmo que count falhe em versões antigas, ainda tentaremos usar o modelo
                    pass
                print(f"[AIService] ✅ Modelo configurado para {self.bot_type}: {model_name}")
                return model
            except Exception as e:
                last_error = e
                print(f"[AIService] ⚠️ Falha ao configurar modelo {model_name} para {self.bot_type}: {e}")

        # Se todos falharem, propagar erro com contexto
        raise RuntimeError(f"Não foi possível configurar nenhum modelo válido para {self.bot_type}. Último erro: {last_error}")
    
    def generate_response(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Gera resposta do modelo para uma mensagem.
        
        Args:
            message: Mensagem do usuário
            history: Histórico de conversa (opcional)
                     Lista de dicts com 'role' ('user' ou 'model') e 'parts'
        
        Returns:
            Resposta gerada pelo modelo
        
        Raises:
            Exception: Se houver erro na geração
        """
        try:
            if history:
                # Usar chat com histórico
                chat = self.model.start_chat(history=self._format_history(history))
                response = chat.send_message(message)
            else:
                # Mensagem única
                response = self.model.generate_content(message)
            
            return response.text
        
        except Exception as error:
            raise Exception(f"Erro ao gerar resposta do {self.bot_type}: {error}") from error
    
    def generate_response_stream(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None
    ):
        """
        Gera resposta em streaming (para respostas longas).
        
        Args:
            message: Mensagem do usuário
            history: Histórico de conversa (opcional)
        
        Yields:
            Chunks de texto da resposta
        
        Raises:
            Exception: Se houver erro na geração
        """
        try:
            if history:
                chat = self.model.start_chat(history=self._format_history(history))
                response = chat.send_message(message, stream=True)
            else:
                response = self.model.generate_content(message, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        
        except Exception as error:
            raise Exception(f"Erro ao gerar resposta em streaming: {error}") from error
    
    def start_chat(self, history: Optional[List[Dict[str, str]]] = None):
        """
        Inicia uma sessão de chat.
        
        Args:
            history: Histórico de conversa (opcional)
        
        Returns:
            Objeto de chat do Gemini
        """
        formatted_history = self._format_history(history) if history else []
        return self.model.start_chat(history=formatted_history)
    
    @staticmethod
    def _format_history(history: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Formata histórico de conversa para o formato esperado pelo Gemini.
        
        Args:
            history: Lista de mensagens com 'role' e 'content'
        
        Returns:
            Histórico formatado para o Gemini
        """
        formatted = []
        
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Gemini usa 'user' e 'model' como roles
            gemini_role = 'model' if role in ('assistant', 'model', 'bot') else 'user'
            
            formatted.append({
                'role': gemini_role,
                'parts': [content]
            })
        
        return formatted
    
    def count_tokens(self, text: str) -> int:
        """
        Conta o número de tokens em um texto.
        
        Args:
            text: Texto para contar tokens
        
        Returns:
            Número de tokens
        """
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception:
            # Estimativa grosseira se falhar: ~4 caracteres por token
            return len(text) // 4


def get_ai_service(bot_type: str = 'drivebot') -> AIService:
    """
    Factory function para obter instância do AIService.
    
    Args:
        bot_type: Tipo do bot ('drivebot' ou 'alphabot')
    
    Returns:
        Instância configurada do AIService
    """
    return AIService(bot_type=bot_type)
