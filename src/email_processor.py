#!/usr/bin/env python3
# 
# ===========================================================
# email_processor.py
# Part of the DOCUFIND Project (MCP-based Document Processor)
#
# Author: Gabriel Mauricio Cortés
# Created on: 24/12/2024
# License: MIT
# Description:
#   This module is part of an academic extracurricular project
#   that demonstrates the use of Model Context Protocol (MCP)
#   for intelligent document processing and cloud integration.
# ===========================================================

"""
Email Processor - DOCUFIND
Procesador de correos con soporte para Gmail, Outlook y otros
"""

import imaplib
import email
from email.message import Message
from email.header import decode_header
from email.utils import parsedate_to_datetime
import logging
import base64
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class EmailCredentials:
    """Credenciales para el servidor de email"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Inicializa las credenciales desde un diccionario
        
        Args:
            config_dict: Diccionario con las credenciales
        """
        self.server = config_dict.get('server', 'imap.gmail.com')
        self.port = config_dict.get('port', 993)
        self.username = config_dict.get('username', '')
        self.password = config_dict.get('password', '')
        
        # Compatibilidad con diferentes nombres de campos
        if not self.server and 'imap_server' in config_dict:
            self.server = config_dict['imap_server']
        if not self.port and 'imap_port' in config_dict:
            self.port = config_dict['imap_port']

class EmailConfig:
    """Configuración para el procesador de email"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Inicializa la configuración desde un diccionario
        
        Args:
            config_dict: Diccionario con la configuración
        """
        self.username = config_dict.get('username', '')
        self.password = config_dict.get('password', '')
        self.imap_server = config_dict.get('imap_server', 'imap.gmail.com')
        self.imap_port = config_dict.get('imap_port', 993)
        self.use_ssl = config_dict.get('use_ssl', True)
        self.folder = config_dict.get('folder', 'INBOX')
        self.mark_as_read = config_dict.get('mark_as_read', False)
        self.download_attachments = config_dict.get('download_attachments', True)
        self.max_results = config_dict.get('max_results', 100)
        self.senders = config_dict.get('senders', [])
        self.subject_filters = config_dict.get('subject_filters', [])
        self.has_attachments = config_dict.get('has_attachments', True)
        self.provider = config_dict.get('provider', 'gmail')

class EmailProcessor:
    """Procesador principal de correos electrónicos"""
    
    def __init__(self, config: Union[Dict[str, Any], EmailConfig]):
        """
        Inicializa el procesador de email
        
        Args:
            config: Configuración del procesador (dict o EmailConfig)
        """
        # Convertir dict a EmailConfig si es necesario
        if isinstance(config, dict):
            self.config = EmailConfig(config)
        else:
            self.config = config
            
        self.connection = None
        self.connected = False
        
        logger.info(f"📧 EmailProcessor inicializado para: {self.config.username}")
    
    def connect(self) -> bool:
        """
        Establece conexión con el servidor IMAP
        
        Returns:
            True si la conexión fue exitosa
        """
        try:
            # Crear conexión IMAP
            if self.config.use_ssl:
                self.connection = imaplib.IMAP4_SSL(
                    self.config.imap_server,
                    self.config.imap_port
                )
            else:
                self.connection = imaplib.IMAP4(
                    self.config.imap_server,
                    self.config.imap_port
                )
            
            # Login
            self.connection.login(self.config.username, self.config.password)
            self.connected = True
            
            logger.info(f"✅ Conectado exitosamente a {self.config.imap_server}")
            return True
            
        except imaplib.IMAP4.error as e:
            logger.error(f"❌ Error de autenticación IMAP: {e}")
            logger.error("Verifica tu usuario y contraseña")
            if 'gmail' in self.config.imap_server.lower():
                logger.error("Para Gmail, asegúrate de usar una App Password")
            return False
        except Exception as e:
            logger.error(f"❌ Error conectando al servidor: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión con el servidor IMAP"""
        if self.connection and self.connected:
            try:
                self.connection.close()
                self.connection.logout()
                self.connected = False
                logger.info("📧 Desconectado del servidor de email")
            except:
                pass
    
    def search_emails(self,
                     date_from: Optional[datetime] = None,
                     date_to: Optional[datetime] = None,
                     query: Optional[str] = None,
                     senders: Optional[List[str]] = None,
                     subject_filters: Optional[List[str]] = None,
                     has_attachments: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Busca correos según los criterios especificados
        
        Args:
            date_from: Fecha inicial
            date_to: Fecha final
            query: Query adicional de búsqueda
            senders: Lista de remitentes específicos
            subject_filters: Palabras clave en el asunto
            has_attachments: Solo correos con adjuntos
            
        Returns:
            Lista de correos encontrados
        """
        if not self.connected:
            if not self.connect():
                return []
        
        try:
            # Seleccionar carpeta
            self.connection.select(self.config.folder)
            
            # Construir query de búsqueda
            search_criteria = self._build_search_criteria(
                date_from, date_to, query,
                senders or self.config.senders,
                subject_filters or self.config.subject_filters,
                has_attachments if has_attachments is not None else self.config.has_attachments
            )
            
            logger.info(f"🔍 Buscando correos con criterio: {search_criteria}")
            
            # Ejecutar búsqueda
            typ, data = self.connection.search(None, search_criteria)
            
            if typ != 'OK':
                logger.error("❌ Error en la búsqueda")
                return []
            
            email_ids = data[0].split()
            
            if not email_ids:
                logger.info("📭 No se encontraron correos con los criterios especificados")
                return []
            
            logger.info(f"📬 Se encontraron {len(email_ids)} correos")
            
            # Limitar resultados si es necesario
            if self.config.max_results and len(email_ids) > self.config.max_results:
                email_ids = email_ids[-self.config.max_results:]
                logger.info(f"📊 Limitando a los últimos {self.config.max_results} correos")
            
            # Procesar cada email
            emails = []
            for idx, email_id in enumerate(email_ids, 1):
                if idx % 10 == 0:
                    logger.info(f"  Procesando {idx}/{len(email_ids)}...")
                
                email_data = self._fetch_email(email_id)
                if email_data:
                    emails.append(email_data)
            
            logger.info(f"✅ {len(emails)} correos procesados exitosamente")
            return emails
            
        except Exception as e:
            logger.error(f"❌ Error buscando emails: {e}")
            return []
    
    def _build_search_criteria(self,
                               date_from: Optional[datetime],
                               date_to: Optional[datetime],
                               query: Optional[str],
                               senders: List[str],
                               subject_filters: List[str],
                               has_attachments: bool) -> str:
        """
        Construye el criterio de búsqueda IMAP
        
        Returns:
            String con el criterio de búsqueda
        """
        criteria_parts = []
        
        # Filtro de fechas
        if date_from:
            date_str = date_from.strftime("%d-%b-%Y")
            criteria_parts.append(f'SINCE {date_str}')
        
        if date_to:
            date_str = date_to.strftime("%d-%b-%Y")
            criteria_parts.append(f'BEFORE {date_str}')
        
        # Para Gmail, podemos usar X-GM-RAW para búsquedas más complejas
        if 'gmail' in self.config.imap_server.lower():
            # Usar sintaxis específica de Gmail
            gmail_query_parts = []
            
            # Agregar filtros de asunto con OR
            if subject_filters:
                subject_query = ' OR '.join([f'subject:{keyword}' for keyword in subject_filters])
                gmail_query_parts.append(f'({subject_query})')
            
            # Agregar remitentes con OR
            if senders:
                sender_query = ' OR '.join([f'from:{sender}' for sender in senders])
                gmail_query_parts.append(f'({sender_query})')
            
            # Agregar query adicional
            if query:
                gmail_query_parts.append(query)
            
            # Si hay query de Gmail, agregarlo
            if gmail_query_parts:
                gmail_query = ' '.join(gmail_query_parts)
                criteria_parts.append(f'X-GM-RAW "{gmail_query}"')
        else:
            # Para otros servidores IMAP, usar sintaxis estándar más simple
            # IMAP estándar no soporta OR complejos, así que buscaremos todo y filtraremos después
            
            # Si hay múltiples keywords, buscar el primero más común
            if subject_filters:
                # Tomar solo el primer filtro para servidores no-Gmail
                criteria_parts.append(f'SUBJECT "{subject_filters[0]}"')
            
            # Para remitentes, usar solo el primero
            if senders:
                criteria_parts.append(f'FROM "{senders[0]}"')
            
            # Query adicional
            if query:
                criteria_parts.append(f'TEXT "{query}"')
        
        # Si no hay criterios, buscar todos
        if not criteria_parts:
            return 'ALL'
        
        # Para Gmail con X-GM-RAW
        if any('X-GM-RAW' in part for part in criteria_parts):
            # Separar las partes de fecha de las de Gmail
            date_parts = [p for p in criteria_parts if 'SINCE' in p or 'BEFORE' in p]
            gmail_parts = [p for p in criteria_parts if 'X-GM-RAW' in p]
            
            if date_parts and gmail_parts:
                return f'{" ".join(date_parts)} {" ".join(gmail_parts)}'
            elif gmail_parts:
                return ' '.join(gmail_parts)
            else:
                return ' '.join(date_parts) if date_parts else 'ALL'
        
        # Para otros servidores
        return ' '.join(criteria_parts)
    
    def _fetch_email(self, email_id: bytes) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos de un email específico
        
        Args:
            email_id: ID del email
            
        Returns:
            Diccionario con los datos del email
        """
        try:
            # Fetch email data
            typ, data = self.connection.fetch(email_id, '(RFC822)')
            
            if typ != 'OK':
                return None
            
            # Parse email
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extraer información básica
            email_data = {
                'id': email_id.decode(),
                'subject': self._decode_header(msg.get('Subject', '')),
                'sender': self._decode_header(msg.get('From', '')),
                'date': self._parse_date(msg.get('Date', '')),
                'to': self._decode_header(msg.get('To', '')),
                'message_id': msg.get('Message-ID', ''),
                'has_attachments': self._has_attachments(msg),
                'body': self._get_email_body(msg),
                'attachments': []
            }
            
            # Marcar como leído si está configurado
            if self.config.mark_as_read:
                self.connection.store(email_id, '+FLAGS', '\\Seen')
            
            return email_data
            
        except Exception as e:
            logger.error(f"❌ Error procesando email {email_id}: {e}")
            return None
    
    def get_attachments(self, email_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene los adjuntos de un email
        
        Args:
            email_id: ID del email
            
        Returns:
            Lista de adjuntos con su contenido
        """
        if not self.connected:
            if not self.connect():
                return []
        
        try:
            # Fetch email
            typ, data = self.connection.fetch(email_id.encode(), '(RFC822)')
            
            if typ != 'OK':
                return []
            
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            attachments = []
            
            # Procesar cada parte del mensaje
            for part in msg.walk():
                # Skip non-attachment parts
                if part.get_content_disposition() != 'attachment':
                    continue
                
                # Get filename
                filename = part.get_filename()
                if not filename:
                    continue
                
                # Decode filename if needed
                filename = self._decode_header(filename)
                
                # Get content
                content = part.get_payload(decode=True)
                
                if content:
                    attachments.append({
                        'filename': filename,
                        'content': content,
                        'content_type': part.get_content_type(),
                        'size': len(content)
                    })
                    
                    logger.info(f"  📎 Adjunto extraído: {filename} ({len(content)} bytes)")
            
            return attachments
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo adjuntos: {e}")
            return []
    
    def _decode_header(self, header: str) -> str:
        """Decodifica un header de email"""
        if not header:
            return ""
        
        decoded_parts = []
        for part, encoding in decode_header(header):
            if isinstance(part, bytes):
                if encoding:
                    try:
                        decoded_parts.append(part.decode(encoding))
                    except:
                        decoded_parts.append(part.decode('utf-8', errors='ignore'))
                else:
                    # Intentar con diferentes encodings comunes
                    for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252']:
                        try:
                            decoded_parts.append(part.decode(enc))
                            break
                        except:
                            continue
                    else:
                        # Si ninguno funciona, usar utf-8 con ignore
                        decoded_parts.append(part.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(str(part))
        
        return ' '.join(decoded_parts)
    
    def _parse_date(self, date_str: str) -> str:
        """Parsea la fecha del email"""
        try:
            dt = parsedate_to_datetime(date_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return date_str
    
    def _has_attachments(self, msg: Message) -> bool:
        """Verifica si el mensaje tiene adjuntos"""
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                return True
        return False
    
    #def _get_email_body(self, msg: Message) -> str:
    #    """Extrae el cuerpo del email"""
    #    body = ""
    #    
    #    if msg.is_multipart():
    #        for part in msg.walk():
    #            content_type = part.get_content_type()
    #            content_disposition = str(part.get("Content-Disposition"))
    #            
    #            if "attachment" not in content_disposition:
    #                if content_type == "text/plain":
    #                    try:
    #                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
    #                        break
    #                    except:
    #                        pass
    #                elif content_type == "text/html" and not body:
    #                    try:
    #                        html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
    #                        # Remover tags HTML básicos
    #                        body = re.sub('<[^<]+?>', '', html_body)
    #                    except:
    #                        pass
    #    else:
    #        try:
    #            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
    #        except:
    #            body = str(msg.get_payload())
    #    
    #    return body.strip()
    #
    
    
    
    
    def _get_email_body(self, msg: Message) -> str:
        """
        🔧 MÉTODO MEJORADO: Extrae TODO el contenido del cuerpo del email
        """
        body_parts = []
        
        try:
            if msg.is_multipart():
                # Email con múltiples partes - procesar todas
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    
                    # Solo procesar contenido que no sea adjunto
                    if "attachment" not in content_disposition:
                        
                        # 1. Contenido texto plano
                        if content_type == "text/plain":
                            try:
                                text_content = part.get_payload(decode=True)
                                if text_content:
                                    decoded = text_content.decode('utf-8', errors='ignore')
                                    if decoded.strip():
                                        body_parts.append(decoded.strip())
                            except Exception as e:
                                logger.debug(f"Error decodificando text/plain: {e}")
                        
                        # 2. Contenido HTML convertido a texto
                        elif content_type == "text/html":
                            try:
                                html_content = part.get_payload(decode=True)
                                if html_content:
                                    decoded_html = html_content.decode('utf-8', errors='ignore')
                                    # Convertir HTML a texto básico
                                    import re
                                    # Eliminar scripts y styles
                                    clean_html = re.sub(r'<script[^>]*>.*?</script>', '', decoded_html, flags=re.DOTALL)
                                    clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL)
                                    # Reemplazar algunos tags con espacios/saltos
                                    clean_html = re.sub(r'</(div|p|br|h[1-6])>', '\n', clean_html)
                                    clean_html = re.sub(r'<br[^>]*>', '\n', clean_html)
                                    # Eliminar todos los tags HTML restantes
                                    text_from_html = re.sub(r'<[^>]+>', ' ', clean_html)
                                    # Decodificar entidades HTML básicas
                                    text_from_html = text_from_html.replace('&nbsp;', ' ')
                                    text_from_html = text_from_html.replace('&amp;', '&')
                                    text_from_html = text_from_html.replace('&lt;', '<')
                                    text_from_html = text_from_html.replace('&gt;', '>')
                                    # Limpiar espacios extra
                                    text_from_html = ' '.join(text_from_html.split())
                                    
                                    if text_from_html.strip():
                                        body_parts.append(text_from_html.strip())
                            except Exception as e:
                                logger.debug(f"Error procesando HTML: {e}")
                        
                        # 3. Otros tipos de contenido de texto
                        elif content_type.startswith("text/"):
                            try:
                                other_content = part.get_payload(decode=True)
                                if other_content:
                                    decoded = other_content.decode('utf-8', errors='ignore')
                                    if decoded.strip():
                                        body_parts.append(decoded.strip())
                            except Exception as e:
                                logger.debug(f"Error decodificando {content_type}: {e}")
            
            else:
                # Email de una sola parte
                try:
                    content_type = msg.get_content_type()
                    
                    if content_type == "text/html":
                        # Es HTML, convertir a texto
                        html_content = msg.get_payload(decode=True)
                        if html_content:
                            decoded_html = html_content.decode('utf-8', errors='ignore')
                            # Mismo proceso de limpieza HTML
                            import re
                            clean_html = re.sub(r'<script[^>]*>.*?</script>', '', decoded_html, flags=re.DOTALL)
                            clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.DOTALL)
                            clean_html = re.sub(r'</(div|p|br|h[1-6])>', '\n', clean_html)
                            clean_html = re.sub(r'<br[^>]*>', '\n', clean_html)
                            text_from_html = re.sub(r'<[^>]+>', ' ', clean_html)
                            text_from_html = text_from_html.replace('&nbsp;', ' ')
                            text_from_html = text_from_html.replace('&amp;', '&')
                            text_from_html = ' '.join(text_from_html.split())
                            body_parts.append(text_from_html.strip())
                    else:
                        # Texto plano o otro tipo
                        body_content = msg.get_payload(decode=True)
                        if body_content:
                            decoded = body_content.decode('utf-8', errors='ignore')
                            body_parts.append(decoded.strip())
                        else:
                            # Fallback: contenido sin decodificar
                            raw_content = str(msg.get_payload())
                            body_parts.append(raw_content.strip())
                            
                except Exception as e:
                    logger.debug(f"Error procesando email simple: {e}")
                    # Último fallback
                    try:
                        fallback_content = str(msg.get_payload())
                        body_parts.append(fallback_content.strip())
                    except:
                        pass
            
            # Combinar todas las partes del contenido
            if body_parts:
                # Unir con separadores y limpiar
                complete_body = '\n\n--- CONTENIDO ---\n\n'.join(body_parts)
                
                # Limpiar espacios excesivos y líneas vacías
                import re
                complete_body = re.sub(r'\n{3,}', '\n\n', complete_body)
                complete_body = re.sub(r' {2,}', ' ', complete_body)
                
                logger.debug(f"Contenido completo extraído: {len(complete_body)} caracteres")
                return complete_body.strip()
            
            # Si no se encontró contenido
            logger.debug("No se pudo extraer contenido del email")
            return ""
            
        except Exception as e:
            logger.error(f"Error extrayendo cuerpo del email: {e}")
            return ""
        
        
    def send_notification(self, recipient: str, subject: str, body: str) -> bool:
        """
        Envía una notificación por email
        
        Args:
            recipient: Email del destinatario
            subject: Asunto del correo
            body: Cuerpo del correo
            
        Returns:
            True si se envió exitosamente
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.username
            msg['To'] = recipient
            
            # Agregar cuerpo HTML
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Determinar servidor SMTP
            smtp_server = self.config.imap_server.replace('imap', 'smtp')
            smtp_port = 587  # TLS port
            
            # Enviar email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(self.config.username, self.config.password)
                server.send_message(msg)
            
            logger.info(f"✅ Notificación enviada a: {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")
            return False

# Funciones de utilidad
def test_connection(config: Dict[str, Any]) -> bool:
    """
    Prueba la conexión con el servidor de email
    
    Args:
        config: Configuración del email
        
    Returns:
        True si la conexión es exitosa
    """
    processor = EmailProcessor(config)
    success = processor.connect()
    processor.disconnect()
    return success

if __name__ == "__main__":
    # Prueba básica
    print("🧪 Probando EmailProcessor...")
    
    # Configuración de prueba
    test_config = {
        'username': 'test@gmail.com',
        'password': 'test_password',
        'imap_server': 'imap.gmail.com',
        'imap_port': 993,
        'use_ssl': True
    }
    
    processor = EmailProcessor(test_config)
    print(f"✅ EmailProcessor creado para: {processor.config.username}")