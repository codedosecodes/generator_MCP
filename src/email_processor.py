#!/usr/bin/env python3
"""
Email Processor - DOCUFIND
Procesador de correos con soporte para Gmail, Outlook y otros
"""

import imaplib
import email
import logging
import base64
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from email.header import decode_header
from email.utils import parsedate_to_datetime
import chardet

logger = logging.getLogger(__name__)

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
        criteria = []
        
        # Filtro de fechas
        if date_from:
            date_str = date_from.strftime("%d-%b-%Y")
            criteria.append(f'SINCE {date_str}')
        
        if date_to:
            date_str = date_to.strftime("%d-%b-%Y")
            criteria.append(f'BEFORE {date_str}')
        
        # Filtro de remitentes
        if senders:
            sender_criteria = []
            for sender in senders:
                sender_criteria.append(f'FROM "{sender}"')
            if len(sender_criteria) == 1:
                criteria.append(sender_criteria[0])
            else:
                # Para múltiples remitentes, usar OR
                criteria.append(f'OR {" OR ".join(sender_criteria)}')
        
        # Filtro de asunto
        if subject_filters:
            subject_criteria = []
            for keyword in subject_filters:
                subject_criteria.append(f'SUBJECT "{keyword}"')
            if len(subject_criteria) == 1:
                criteria.append(subject_criteria[0])
            else:
                # Para múltiples keywords, usar OR
                criteria.append(f'OR {" OR ".join(subject_criteria)}')
        
        # Query adicional
        if query:
            criteria.append(f'TEXT "{query}"')
        
        # Si no hay criterios, buscar todos
        if not criteria:
            return 'ALL'
        
        # Combinar criterios
        if len(criteria) == 1:
            return criteria[0]
        else:
            return f'({" ".join(criteria)})'
    
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
                    # Intentar detectar encoding
                    detected = chardet.detect(part)
                    encoding = detected.get('encoding', 'utf-8')
                    decoded_parts.append(part.decode(encoding, errors='ignore'))
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
    
    def _has_attachments(self, msg: email.message.Message) -> bool:
        """Verifica si el mensaje tiene adjuntos"""
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                return True
        return False
    
    def _get_email_body(self, msg: email.message.Message) -> str:
        """Extrae el cuerpo del email"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if "attachment" not in content_disposition:
                    if content_type == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                        except:
                            pass
                    elif content_type == "text/html" and not body:
                        try:
                            html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            # Remover tags HTML básicos
                            body = re.sub('<[^<]+?>', '', html_body)
                        except:
                            pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                body = str(msg.get_payload())
        
        return body.strip()
    
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