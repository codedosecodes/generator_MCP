"""
Email Processor Module - FIND_DOCUMENTS
Maneja conexiones email, filtrado y extracción de contenido
"""

import imaplib
import email
import ssl
import base64
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class EmailCredentials:
    """Credenciales para conexión email"""
    server: str
    port: int
    username: str
    password: str

@dataclass
class EmailFilter:
    """Filtros para búsqueda de emails"""
    start_date: str
    end_date: str
    keywords: List[str]
    sender_filter: Optional[List[str]] = None
    subject_filter: Optional[List[str]] = None
    has_attachments: Optional[bool] = None

@dataclass
class EmailMessage:
    """Estructura de mensaje de email procesado"""
    id: str
    subject: str
    from_addr: str
    to_addr: str
    date: str
    content: str
    attachments: List[Dict[str, Any]]
    has_attachments: bool
    raw_date: datetime

class EmailConnectionError(Exception):
    """Error de conexión de email"""
    pass

class EmailProcessor:
    """Procesador principal de emails con filtros avanzados"""
    
    def __init__(self, credentials: EmailCredentials):
        self.credentials = credentials
        self.connection = None
        self.is_connected = False
        
        # Configuraciones por defecto para proveedores
        self.provider_configs = {
            'gmail.com': {
                'imap_server': 'imap.gmail.com',
                'imap_port': 993,
                'ssl_required': True
            },
            'outlook.com': {
                'imap_server': 'outlook.office365.com', 
                'imap_port': 993,
                'ssl_required': True
            },
            'yahoo.com': {
                'imap_server': 'imap.mail.yahoo.com',
                'imap_port': 993,
                'ssl_required': True
            }
        }
        
        logger.info(f"📧 EmailProcessor inicializado para {credentials.username}")
    
    async def connect(self) -> bool:
        """Establece conexión con el servidor de email"""
        try:
            logger.info(f"🔌 Conectando a {self.credentials.server}:{self.credentials.port}")
            
            # Crear contexto SSL
            context = ssl.create_default_context()
            
            # Conectar con IMAP SSL
            self.connection = imaplib.IMAP4_SSL(
                self.credentials.server,
                self.credentials.port,
                ssl_context=context
            )
            
            # Autenticar
            self.connection.login(self.credentials.username, self.credentials.password)
            
            # Seleccionar INBOX
            status, count = self.connection.select('INBOX')
            if status != 'OK':
                raise EmailConnectionError(f"No se pudo seleccionar INBOX: {status}")
            
            total_emails = int(count[0].decode())
            logger.info(f"✅ Conectado exitosamente. INBOX tiene {total_emails} emails")
            
            self.is_connected = True
            return True
            
        except imaplib.IMAP4.error as e:
            logger.error(f"❌ Error de autenticación IMAP: {e}")
            raise EmailConnectionError(f"Error de autenticación: {e}")
        except ssl.SSLError as e:
            logger.error(f"❌ Error SSL: {e}")
            raise EmailConnectionError(f"Error SSL: {e}")
        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            raise EmailConnectionError(f"Error de conexión: {e}")
    
    async def disconnect(self):
        """Cierra la conexión del email"""
        try:
            if self.connection and self.is_connected:
                self.connection.logout()
                self.is_connected = False
                logger.info("🔌 Conexión cerrada")
        except Exception as e:
            logger.warning(f"⚠️  Advertencia al cerrar conexión: {e}")
    
    async def search_emails(self, filters: EmailFilter) -> List[EmailMessage]:
        """Busca emails con filtros específicos"""
        if not self.is_connected:
            await self.connect()
        
        try:
            logger.info(f"🔍 Buscando emails del {filters.start_date} al {filters.end_date}")
            
            # Construir criterios de búsqueda IMAP
            search_criteria = self._build_search_criteria(filters)
            logger.debug(f"Criterio de búsqueda: {search_criteria}")
            
            # Ejecutar búsqueda
            status, messages = self.connection.search(None, search_criteria)
            
            if status != 'OK':
                raise Exception(f"Error en búsqueda: {status}")
            
            email_ids = messages[0].split() if messages[0] else []
            logger.info(f"📧 Encontrados {len(email_ids)} emails candidatos")
            
            if not email_ids:
                return []
            
            # Procesar cada email
            processed_emails = []
            total_emails = len(email_ids)
            
            for idx, email_id in enumerate(email_ids):
                try:
                    progress = ((idx + 1) / total_emails) * 100
                    logger.info(f"📊 Procesando email {idx + 1}/{total_emails} ({progress:.1f}%)")
                    
                    email_message = await self._fetch_and_process_email(
                        email_id.decode(), filters
                    )
                    
                    if email_message:
                        processed_emails.append(email_message)
                        
                except Exception as e:
                    logger.warning(f"⚠️  Error procesando email {email_id}: {e}")
                    continue
            
            logger.info(f"✅ Procesados {len(processed_emails)} emails que cumplen criterios")
            return processed_emails
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda de emails: {e}")
            raise
    
    def _build_search_criteria(self, filters: EmailFilter) -> str:
        """Construye criterios de búsqueda IMAP"""
        criteria_parts = []
        
        # Filtro por fechas
        try:
            start_date = datetime.strptime(filters.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(filters.end_date, "%Y-%m-%d")
            
            # Formato IMAP para fechas: DD-Mon-YYYY
            start_date_str = start_date.strftime("%d-%b-%Y")
            end_date_str = end_date.strftime("%d-%b-%Y")
            
            criteria_parts.append(f'SINCE "{start_date_str}"')
            criteria_parts.append(f'BEFORE "{end_date_str}"')
            
        except ValueError as e:
            logger.warning(f"⚠️  Error en formato de fechas: {e}")
        
        # Filtro por remitente
        if filters.sender_filter:
            sender_criteria = []
            for sender in filters.sender_filter:
                sender_criteria.append(f'FROM "{sender}"')
            if sender_criteria:
                criteria_parts.append(f"({' OR '.join(sender_criteria)})")
        
        # Filtro por asunto
        if filters.subject_filter:
            subject_criteria = []
            for subject in filters.subject_filter:
                subject_criteria.append(f'SUBJECT "{subject}"')
            if subject_criteria:
                criteria_parts.append(f"({' OR '.join(subject_criteria)})")
        
        # Criterio combinado
        if criteria_parts:
            return f"({' AND '.join(criteria_parts)})"
        else:
            return 'ALL'
    
    async def _fetch_and_process_email(self, email_id: str, filters: EmailFilter) -> Optional[EmailMessage]:
        """Obtiene y procesa un email específico"""
        try:
            # Obtener email completo
            status, msg_data = self.connection.fetch(email_id, '(RFC822)')
            
            if status != 'OK' or not msg_data or not msg_data[0]:
                return None
            
            # Parsear mensaje
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Extraer información básica
            subject = self._decode_header(email_message.get('Subject', ''))
            from_addr = self._decode_header(email_message.get('From', ''))
            to_addr = self._decode_header(email_message.get('To', ''))
            date_str = email_message.get('Date', '')
            
            # Parsear fecha
            try:
                parsed_date = email.utils.parsedate_tz(date_str)
                if parsed_date:
                    email_date = datetime.fromtimestamp(
                        email.utils.mktime_tz(parsed_date)
                    )
                else:
                    email_date = datetime.now()
            except:
                email_date = datetime.now()
            
            # Extraer contenido
            content = self._extract_email_content(email_message)
            
            # Verificar si cumple con palabras clave
            if not self._matches_keywords(subject, content, filters.keywords):
                return None
            
            # Extraer adjuntos
            attachments = self._extract_attachments(email_message)
            
            # Aplicar filtro de adjuntos si está especificado
            if filters.has_attachments is not None:
                if filters.has_attachments and not attachments:
                    return None
                elif not filters.has_attachments and attachments:
                    return None
            
            # Crear objeto EmailMessage
            processed_email = EmailMessage(
                id=email_id,
                subject=subject,
                from_addr=from_addr,
                to_addr=to_addr,
                date=date_str,
                content=content,
                attachments=attachments,
                has_attachments=len(attachments) > 0,
                raw_date=email_date
            )
            
            return processed_email
            
        except Exception as e:
            logger.error(f"❌ Error procesando email {email_id}: {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """Decodifica headers de email con encoding especial"""
        if not header:
            return ""
        
        try:
            decoded_parts = email.header.decode_header(header)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding, errors='ignore')
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            
            return decoded_string.strip()
            
        except Exception as e:
            logger.warning(f"⚠️  Error decodificando header: {e}")
            return str(header)
    
    def _extract_email_content(self, email_message) -> str:
        """Extrae el contenido de texto del email"""
        content_parts = []
        
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    
                    if content_type in ['text/plain', 'text/html']:
                        try:
                            charset = part.get_content_charset() or 'utf-8'
                            part_content = part.get_payload(decode=True)
                            
                            if part_content:
                                decoded_content = part_content.decode(charset, errors='ignore')
                                
                                # Si es HTML, extraer texto básico
                                if content_type == 'text/html':
                                    decoded_content = self._extract_text_from_html(decoded_content)
                                
                                content_parts.append(decoded_content)
                                
                        except Exception as e:
                            logger.warning(f"⚠️  Error extrayendo contenido de parte: {e}")
                            continue
            else:
                try:
                    charset = email_message.get_content_charset() or 'utf-8'
                    payload = email_message.get_payload(decode=True)
                    
                    if payload:
                        content = payload.decode(charset, errors='ignore')
                        
                        # Si es HTML, extraer texto
                        if email_message.get_content_type() == 'text/html':
                            content = self._extract_text_from_html(content)
                        
                        content_parts.append(content)
                        
                except Exception as e:
                    logger.warning(f"⚠️  Error extrayendo contenido principal: {e}")
        
        except Exception as e:
            logger.warning(f"⚠️  Error general extrayendo contenido: {e}")
        
        # Unir y limpiar contenido
        full_content = '\n'.join(content_parts)
        return self._clean_text_content(full_content)
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extrae texto básico de HTML"""
        try:
            # Importar BeautifulSoup solo si es necesario
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                return soup.get_text(separator=' ', strip=True)
            except ImportError:
                # Fallback: regex básico para quitar tags HTML
                import re
                clean_text = re.sub(r'<[^>]+>', ' ', html_content)
                clean_text = re.sub(r'\s+', ' ', clean_text)
                return clean_text.strip()
                
        except Exception as e:
            logger.warning(f"⚠️  Error extrayendo texto de HTML: {e}")
            return html_content
    
    def _clean_text_content(self, content: str) -> str:
        """Limpia y normaliza el contenido de texto"""
        if not content:
            return ""
        
        # Normalizar espacios en blanco
        content = re.sub(r'\s+', ' ', content)
        
        # Quitar caracteres de control
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
        
        # Limitar longitud
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length] + "... [contenido truncado]"
        
        return content.strip()
    
    def _extract_attachments(self, email_message) -> List[Dict[str, Any]]:
        """Extrae información de adjuntos"""
        attachments = []
        
        try:
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename:
                        try:
                            # Decodificar nombre del archivo
                            filename = self._decode_header(filename)
                            
                            # Obtener contenido
                            content = part.get_payload(decode=True)
                            content_type = part.get_content_type()
                            
                            if content:
                                attachment_info = {
                                    'filename': filename,
                                    'content': base64.b64encode(content).decode('utf-8'),
                                    'size': len(content),
                                    'content_type': content_type or 'application/octet-stream'
                                }
                                
                                # Validar que el archivo no sea demasiado grande (50MB max)
                                max_size = 50 * 1024 * 1024  # 50MB
                                if len(content) <= max_size:
                                    attachments.append(attachment_info)
                                else:
                                    logger.warning(f"⚠️  Adjunto {filename} demasiado grande: {len(content)} bytes")
                                    
                        except Exception as e:
                            logger.warning(f"⚠️  Error extrayendo adjunto {filename}: {e}")
                            continue
        
        except Exception as e:
            logger.warning(f"⚠️  Error general extrayendo adjuntos: {e}")
        
        return attachments
    
    def _matches_keywords(self, subject: str, content: str, keywords: List[str]) -> bool:
        """Verifica si el email contiene las palabras clave"""
        if not keywords:
            return True
        
        # Combinar asunto y contenido para búsqueda
        text_to_search = f"{subject} {content}".lower()
        
        # Verificar si alguna palabra clave coincide
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            
            if not keyword_lower:
                continue
            
            # Búsqueda simple de substring
            if keyword_lower in text_to_search:
                logger.debug(f"✓ Palabra clave encontrada: '{keyword}'")
                return True
            
            # Búsqueda con regex para palabras completas
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            if re.search(pattern, text_to_search):
                logger.debug(f"✓ Palabra clave encontrada (palabra completa): '{keyword}'")
                return True
        
        return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Obtiene información de la conexión actual"""
        return {
            'server': self.credentials.server,
            'port': self.credentials.port,
            'username': self.credentials.username,
            'is_connected': self.is_connected,
            'connection_type': 'IMAP4_SSL'
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Prueba la conexión sin buscar emails"""
        try:
            await self.connect()
            
            # Obtener información básica
            status, count = self.connection.select('INBOX', readonly=True)
            total_emails = int(count[0].decode()) if status == 'OK' else 0
            
            await self.disconnect()
            
            return {
                'success': True,
                'total_emails_in_inbox': total_emails,
                'server_info': f"{self.credentials.server}:{self.credentials.port}",
                'test_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'test_time': datetime.now().isoformat()
            }

# Funciones de utilidad
def validate_email_credentials(credentials: EmailCredentials) -> List[str]:
    """Valida credenciales de email"""
    errors = []
    
    if not credentials.server:
        errors.append("Servidor IMAP requerido")
    
    if not credentials.username:
        errors.append("Nombre de usuario requerido")
    
    if not credentials.password:
        errors.append("Contraseña requerida")
    
    if credentials.port not in [993, 143, 587, 25]:
        errors.append("Puerto debe ser 993 (IMAPS), 143 (IMAP), 587 o 25")
    
    return errors

def get_provider_config(email_address: str) -> Optional[Dict[str, Any]]:
    """Obtiene configuración automática basada en dominio del email"""
    domain = email_address.split('@')[-1].lower() if '@' in email_address else ''
    
    configs = {
        'gmail.com': {
            'server': 'imap.gmail.com',
            'port': 993,
            'ssl': True,
            'note': 'Requiere App Password con 2FA habilitado'
        },
        'outlook.com': {
            'server': 'outlook.office365.com',
            'port': 993,
            'ssl': True
        },
        'hotmail.com': {
            'server': 'outlook.office365.com',
            'port': 993,
            'ssl': True
        },
        'yahoo.com': {
            'server': 'imap.mail.yahoo.com',
            'port': 993,
            'ssl': True,
            'note': 'Requiere App Password'
        }
    }
    
    return configs.get(domain)