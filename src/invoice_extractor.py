"""
Invoice Extractor - FIND_DOCUMENTS
Extrae datos inteligentes de facturas de emails y adjuntos
"""

import re
import base64
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class InvoiceData:
    """Datos extraídos de una factura"""
    amount: Optional[float] = None
    currency: Optional[str] = None
    vendor: Optional[str] = None
    concept: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    tax_amount: Optional[float] = None
    tax_id: Optional[str] = None
    confidence: float = 0.0
    extraction_method: str = ""
    raw_matches: Dict[str, Any] = None

class InvoiceExtractor:
    """Extractor inteligente de datos de facturas"""
    
    def __init__(self):
        # Patrones de regex para diferentes tipos de datos
        self.patterns = self._initialize_patterns()
        
        # Palabras clave para categorización
        self.category_keywords = self._initialize_categories()
        
        # Configuración de monedas
        self.currency_symbols = {
            '$': 'USD',
            '€': 'EUR', 
            '£': 'GBP',
            '¥': 'JPY',
            'COP': 'COP',
            'MXN': 'MXN'
        }
        
        logger.info("💡 InvoiceExtractor inicializado")
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Inicializa patrones de regex para extracción"""
        return {
            'amount': [
                # Montos con símbolos de moneda
                r'total:?\s*[\$€£¥]?\s*([0-9]{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)',
                r'amount:?\s*[\$€£¥]?\s*([0-9]{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)',
                r'importe:?\s*[\$€£¥]?\s*([0-9]{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)',
                r'valor:?\s*[\$€£¥]?\s*([0-9]{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)',
                r'subtotal:?\s*[\$€£¥]?\s*([0-9]{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)',
                # Patrones específicos por moneda
                r'\$\s*([0-9]{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'€\s*([0-9]{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)',
                r'([0-9]{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)\s*(?:USD|EUR|GBP|COP|MXN)',
                # Patrones en español
                r'pagar:?\s*[\$€£¥]?\s*([0-9]{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)',
                r'cobrar:?\s*[\$€£¥]?\s*([0-9]{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)',
                r'facturar:?\s*[\$€£¥]?\s*([0-9]{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)'
            ],
            'vendor': [
                # Información del proveedor
                r'from:?\s*([^<\n\r]+?)(?:\s*<|$)',
                r'de:?\s*([^\n\r<]+?)(?:\s*<|$)',
                r'empresa:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'company:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'proveedor:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'supplier:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'factura\s+de:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'invoice\s+from:?\s*([^\n\r]+?)(?:\s*\n|$)',
                # Patrones para emails
                r'([a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                # Nombres en headers de email
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ],
            'concept': [
                # Descripción o concepto
                r'concepto:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'descripci[oó]n:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'description:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'servicio:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'service:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'producto:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'product:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'detalle:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'details:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'motivo:?\s*([^\n\r]+?)(?:\s*\n|$)',
                r'reason:?\s*([^\n\r]+?)(?:\s*\n|$)',
                # Patrones para asuntos comunes
                r'subject:?\s*([^\n\r]+?)(?:\s*\n|$)'
            ],
            'invoice_number': [
                # Número de factura
                r'(?:invoice|factura|bill)(?:\s+(?:no\.?|number|#))?:?\s*([A-Z0-9-]+)',
                r'(?:no\.?|number|#)\s*(?:invoice|factura|bill)?:?\s*([A-Z0-9-]+)',
                r'factura\s*(?:no\.?|número|#)?:?\s*([A-Z0-9-]+)',
                r'invoice\s*(?:no\.?|number|#)?:?\s*([A-Z0-9-]+)',
                r'bill\s*(?:no\.?|number|#)?:?\s*([A-Z0-9-]+)',
                r'(?:ref|reference)(?:\s*no\.?|:)?\s*([A-Z0-9-]+)'
            ],
            'invoice_date': [
                # Fecha de factura
                r'(?:invoice|factura)\s+date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:date|fecha):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})',
                r'(\d{1,2}\s+\w+\s+\d{4})',
                r'(\d{4}-\d{1,2}-\d{1,2})'
            ],
            'due_date': [
                # Fecha de vencimiento
                r'(?:due|vencimiento|vence)\s+(?:date)?:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:pay\s+by|pagar\s+antes):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(?:payment\s+due|vencimiento):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            'tax_id': [
                # Números de identificación fiscal
                r'(?:nit|tax\s+id|rfc):?\s*([0-9-]+)',
                r'(?:cuit|cuil):?\s*([0-9-]+)',
                r'(?:rut):?\s*([0-9.-]+)',
                r'(?:ein):?\s*([0-9-]+)'
            ]
        }
    
    def _initialize_categories(self) -> Dict[str, List[str]]:
        """Inicializa palabras clave para categorización"""
        return {
            'utilities': [
                'electric', 'electricity', 'gas', 'water', 'internet', 'phone', 'mobile',
                'eléctrico', 'electricidad', 'agua', 'teléfono', 'móvil', 'celular'
            ],
            'office_supplies': [
                'staples', 'office', 'depot', 'supplies', 'paper', 'printer',
                'suministros', 'oficina', 'papel', 'impresora', 'útiles'
            ],
            'software': [
                'microsoft', 'adobe', 'google', 'aws', 'azure', 'office', 'license',
                'software', 'subscription', 'saas', 'licencia', 'suscripción'
            ],
            'services': [
                'consulting', 'legal', 'accounting', 'marketing', 'design', 'development',
                'consultoría', 'legal', 'contabilidad', 'mercadeo', 'diseño', 'desarrollo'
            ],
            'hosting': [
                'hosting', 'domain', 'server', 'cloud', 'vps', 'dedicated',
                'dominio', 'servidor', 'nube', 'alojamiento'
            ],
            'transportation': [
                'uber', 'taxi', 'transport', 'fuel', 'gas', 'parking',
                'transporte', 'combustible', 'gasolina', 'estacionamiento'
            ]
        }
    
    async def extract_invoice_data(self, email_content: str, attachments: List[Dict] = None) -> Dict[str, Any]:
        """Extrae datos de factura del contenido del email y adjuntos"""
        try:
            logger.info("🔍 Iniciando extracción de datos de factura")
            
            # Combinar todo el texto disponible
            full_text = email_content
            
            # Procesar adjuntos si existen
            if attachments:
                for attachment in attachments:
                    attachment_text = await self._extract_text_from_attachment(attachment)
                    if attachment_text:
                        full_text += f"\n\n--- ADJUNTO: {attachment['filename']} ---\n{attachment_text}"
            
            # Extraer datos usando patrones
            extracted_data = self._extract_using_patterns(full_text)
            
            # Mejorar extracción con análisis contextual
            enhanced_data = self._enhance_with_context(extracted_data, full_text)
            
            # Categorizar el tipo de factura
            category = self._categorize_invoice(enhanced_data, full_text)
            enhanced_data['category'] = category
            
            # Calcular confianza
            confidence = self._calculate_confidence(enhanced_data, full_text)
            enhanced_data['confidence'] = confidence
            
            # Metadatos de extracción
            enhanced_data['extraction_method'] = 'pattern_matching'
            enhanced_data['extracted_at'] = datetime.now().isoformat()
            
            logger.info(f"✅ Extracción completada - Confianza: {confidence:.0%}")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos de factura: {e}")
            return {
                'error': str(e),
                'confidence': 0.0,
                'extraction_method': 'failed'
            }
    
    def _extract_using_patterns(self, text: str) -> Dict[str, Any]:
        """Extrae datos usando patrones de regex"""
        extracted = {}
        
        # Normalizar texto para búsqueda
        text_lower = text.lower()
        
        # Extraer cada tipo de dato
        for data_type, patterns in self.patterns.items():
            matches = []
            
            for pattern in patterns:
                try:
                    found_matches = re.finditer(pattern, text_lower, re.IGNORECASE | re.MULTILINE)
                    for match in found_matches:
                        if match.group(1):
                            matches.append(match.group(1).strip())
                except re.error as e:
                    logger.warning(f"⚠️  Patrón regex inválido para {data_type}: {e}")
                    continue
            
            # Seleccionar el mejor match
            if matches:
                best_match = self._select_best_match(data_type, matches)
                if best_match:
                    extracted[data_type] = best_match
        
        return extracted
    
    def _select_best_match(self, data_type: str, matches: List[str]) -> Optional[str]:
        """Selecciona el mejor match de una lista"""
        if not matches:
            return None
        
        if data_type == 'amount':
            # Para montos, seleccionar el valor más alto (probablemente el total)
            amounts = []
            for match in matches:
                try:
                    # Limpiar y convertir a float
                    clean_amount = re.sub(r'[^\d.,]', '', match)
                    clean_amount = clean_amount.replace(',', '.')
                    if clean_amount:
                        amounts.append(float(clean_amount))
                except ValueError:
                    continue
            
            if amounts:
                return str(max(amounts))
        
        elif data_type == 'vendor':
            # Para proveedor, seleccionar el más específico (no email genérico)
            for match in matches:
                if '@' in match and not any(word in match.lower() for word in ['noreply', 'no-reply', 'donotreply']):
                    return match
                elif len(match) > 3 and not match.isdigit():
                    return match
        
        elif data_type == 'concept':
            # Para concepto, seleccionar el más descriptivo
            longest = max(matches, key=len) if matches else None
            if longest and len(longest) > 10:
                return longest
        
        # Por defecto, devolver el primer match válido
        return matches[0] if matches else None
    
    def _enhance_with_context(self, data: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Mejora los datos extraídos con análisis contextual"""
        enhanced = data.copy()
        
        # Mejorar extracción de monto
        if 'amount' in enhanced:
            enhanced['amount'] = self._parse_amount(enhanced['amount'])
            enhanced['currency'] = self._detect_currency(text)
        
        # Mejorar vendor
        if 'vendor' in enhanced:
            enhanced['vendor'] = self._clean_vendor_name(enhanced['vendor'])
        
        # Mejorar concepto
        if 'concept' in enhanced:
            enhanced['concept'] = self._clean_concept(enhanced['concept'])
        elif not enhanced.get('concept'):
            # Intentar inferir concepto del contexto
            inferred_concept = self._infer_concept_from_context(text)
            if inferred_concept:
                enhanced['concept'] = inferred_concept
        
        # Detectar información adicional
        enhanced['payment_method'] = self._detect_payment_method(text)
        enhanced['language'] = self._detect_language(text)
        
        return enhanced
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parsea y limpia un monto"""
        try:
            # Remover caracteres no numéricos excepto puntos y comas
            clean_amount = re.sub(r'[^\d.,]', '', str(amount_str))
            
            # Manejar diferentes formatos de números
            if ',' in clean_amount and '.' in clean_amount:
                # Formato: 1,234.56 o 1.234,56
                if clean_amount.rfind(',') > clean_amount.rfind('.'):
                    # Formato: 1.234,56
                    clean_amount = clean_amount.replace('.', '').replace(',', '.')
                else:
                    # Formato: 1,234.56
                    clean_amount = clean_amount.replace(',', '')
            elif ',' in clean_amount:
                # Solo comas - podría ser separador de miles o decimal
                comma_pos = clean_amount.rfind(',')
                if len(clean_amount) - comma_pos <= 3:
                    # Probablemente decimal: 1234,56
                    clean_amount = clean_amount.replace(',', '.')
                else:
                    # Probablemente miles: 1,234
                    clean_amount = clean_amount.replace(',', '')
            
            return float(clean_amount)
            
        except (ValueError, TypeError):
            logger.warning(f"⚠️  No se pudo parsear monto: {amount_str}")
            return 0.0
    
    def _detect_currency(self, text: str) -> str:
        """Detecta la moneda del texto"""
        # Buscar símbolos de moneda
        for symbol, currency in self.currency_symbols.items():
            if symbol in text:
                return currency
        
        # Buscar códigos de moneda
        currency_codes = ['USD', 'EUR', 'GBP', 'COP', 'MXN', 'ARS', 'PEN', 'CLP']
        text_upper = text.upper()
        for code in currency_codes:
            if code in text_upper:
                return code
        
        # Detectar por palabras clave
        if any(word in text.lower() for word in ['peso', 'pesos']):
            return 'COP'
        elif any(word in text.lower() for word in ['dollar', 'dollars', 'dólar', 'dólares']):
            return 'USD'
        elif any(word in text.lower() for word in ['euro', 'euros']):
            return 'EUR'
        
        return 'USD'  # Default
    
    def _clean_vendor_name(self, vendor: str) -> str:
        """Limpia y normaliza el nombre del proveedor"""
        if not vendor:
            return vendor
        
        # Remover emails si hay nombre adicional
        vendor = re.sub(r'<[^>]+>', '', vendor).strip()
        
        # Remover caracteres extraños al inicio/final
        vendor = re.sub(r'^[^\w]+|[^\w]+$', '', vendor).strip()
        
        # Limitar longitud
        if len(vendor) > 100:
            vendor = vendor[:100] + "..."
        
        return vendor
    
    def _clean_concept(self, concept: str) -> str:
        """Limpia y normaliza el concepto"""
        if not concept:
            return concept
        
        # Remover saltos de línea y espacios excesivos
        concept = re.sub(r'\s+', ' ', concept).strip()
        
        # Remover caracteres de control
        concept = ''.join(char for char in concept if ord(char) >= 32)
        
        # Limitar longitud
        if len(concept) > 200:
            concept = concept[:200] + "..."
        
        return concept
    
    def _infer_concept_from_context(self, text: str) -> Optional[str]:
        """Infiere el concepto del contexto cuando no se encuentra explícitamente"""
        # Buscar líneas que podrían ser descripción
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 20 and len(line) < 150:
                # Verificar si parece una descripción
                if any(word in line.lower() for word in ['service', 'product', 'subscription', 'servicio', 'producto', 'suscripción']):
                    return line
        
        return None
    
    def _detect_payment_method(self, text: str) -> Optional[str]:
        """Detecta el método de pago mencionado"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['credit card', 'tarjeta', 'visa', 'mastercard']):
            return 'credit_card'
        elif any(word in text_lower for word in ['bank transfer', 'transferencia', 'wire transfer']):
            return 'bank_transfer'
        elif any(word in text_lower for word in ['paypal']):
            return 'paypal'
        elif any(word in text_lower for word in ['cash', 'efectivo', 'contado']):
            return 'cash'
        
        return None
    
    def _detect_language(self, text: str) -> str:
        """Detecta el idioma del texto"""
        text_lower = text.lower()
        
        spanish_words = ['factura', 'importe', 'empresa', 'fecha', 'vencimiento', 'pagar']
        english_words = ['invoice', 'amount', 'company', 'date', 'due', 'payment']
        
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if spanish_count > english_count:
            return 'es'
        else:
            return 'en'
    
    def _categorize_invoice(self, data: Dict[str, Any], text: str) -> str:
        """Categoriza el tipo de factura"""
        text_lower = text.lower()
        vendor = data.get('vendor', '').lower()
        concept = data.get('concept', '').lower()
        
        # Combinar texto para análisis
        combined_text = f"{text_lower} {vendor} {concept}"
        
        # Verificar cada categoría
        for category, keywords in self.category_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return category
        
        return 'miscellaneous'
    
    def _calculate_confidence(self, data: Dict[str, Any], text: str) -> float:
        """Calcula la confianza de la extracción"""
        confidence_factors = []
        
        # Factor por datos encontrados
        if data.get('amount'):
            confidence_factors.append(0.3)
        if data.get('vendor'):
            confidence_factors.append(0.25)
        if data.get('concept'):
            confidence_factors.append(0.2)
        if data.get('invoice_number'):
            confidence_factors.append(0.15)
        if data.get('invoice_date'):
            confidence_factors.append(0.1)
        
        # Factor por palabras clave de factura
        invoice_keywords = ['invoice', 'factura', 'bill', 'payment', 'total', 'amount']
        keyword_count = sum(1 for keyword in invoice_keywords if keyword in text.lower())
        keyword_factor = min(keyword_count * 0.05, 0.2)
        confidence_factors.append(keyword_factor)
        
        # Factor por estructura del texto
        if len(text) > 100:  # Suficiente contenido
            confidence_factors.append(0.1)
        
        # Calcular confianza total
        total_confidence = sum(confidence_factors)
        return min(total_confidence, 1.0)
    
    async def _extract_text_from_attachment(self, attachment: Dict[str, Any]) -> Optional[str]:
        """Extrae texto de adjuntos"""
        try:
            filename = attachment.get('filename', '').lower()
            content_type = attachment.get('content_type', '')
            
            # Solo procesar archivos de texto por ahora
            if content_type.startswith('text/') or filename.endswith(('.txt', '.csv')):
                content = base64.b64decode(attachment['content'])
                return content.decode('utf-8', errors='ignore')
            
            elif filename.endswith('.pdf'):
                # Para PDFs necesitaríamos PyPDF2 o similar
                logger.info(f"📄 PDF detectado: {filename} (extracción de PDF no implementada)")
                return None
            
            elif filename.endswith(('.doc', '.docx')):
                # Para Word necesitaríamos python-docx
                logger.info(f"📄 Documento Word detectado: {filename} (extracción no implementada)")
                return None
            
            else:
                logger.debug(f"📄 Tipo de archivo no soportado: {filename}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️  Error extrayendo texto de adjunto: {e}")
            return None
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> List[str]:
        """Valida los datos extraídos"""
        warnings = []
        
        # Validar monto
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    warnings.append("Monto debe ser mayor a 0")
                elif amount > 1000000:
                    warnings.append("Monto parece excesivamente alto")
            except (ValueError, TypeError):
                warnings.append("Monto no es un número válido")
        
        # Validar vendor
        if 'vendor' in data:
            vendor = str(data['vendor'])
            if len(vendor) < 2:
                warnings.append("Nombre de proveedor muy corto")
            elif len(vendor) > 200:
                warnings.append("Nombre de proveedor muy largo")
        
        # Validar fechas
        for date_field in ['invoice_date', 'due_date']:
            if date_field in data:
                try:
                    # Intentar parsear la fecha
                    date_str = str(data[date_field])
                    # Aquí podrías agregar validación de fecha más específica
                    if len(date_str) < 8:
                        warnings.append(f"{date_field} parece incompleta")
                except Exception:
                    warnings.append(f"{date_field} tiene formato inválido")
        
        return warnings
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del extractor"""
        return {
            'patterns_count': {
                data_type: len(patterns) 
                for data_type, patterns in self.patterns.items()
            },
            'categories_count': len(self.category_keywords),
            'supported_currencies': list(self.currency_symbols.keys()),
            'extraction_capabilities': [
                'email_content',
                'text_attachments',
                'pattern_matching',
                'contextual_analysis',
                'automatic_categorization'
            ]
        }

# Funciones de utilidad
def clean_currency_amount(amount_str: str) -> Tuple[Optional[float], Optional[str]]:
    """Limpia un string de monto y extrae valor y moneda"""
    if not amount_str:
        return None, None
    
    # Detectar moneda
    currency = None
    for symbol in [', '€', '£', '¥']:
        if symbol in amount_str:
            currency = symbol
            break
    
    # Detectar códigos de moneda
    currency_codes = re.findall(r'\b(USD|EUR|GBP|COP|MXN|ARS)\b', amount_str.upper())
    if currency_codes and not currency:
        currency = currency_codes[0]
    
    # Limpiar y extraer número
    clean_str = re.sub(r'[^\d.,]', '', amount_str)
    
    try:
        # Manejar diferentes formatos
        if ',' in clean_str and '.' in clean_str:
            if clean_str.rfind(',') > clean_str.rfind('.'):
                # Formato europeo: 1.234,56
                clean_str = clean_str.replace('.', '').replace(',', '.')
            else:
                # Formato americano: 1,234.56
                clean_str = clean_str.replace(',', '')
        elif ',' in clean_str:
            # Solo comas
            parts = clean_str.split(',')
            if len(parts[-1]) <= 2:
                # Probablemente decimal
                clean_str = clean_str.replace(',', '.')
            else:
                # Probablemente separador de miles
                clean_str = clean_str.replace(',', '')
        
        amount = float(clean_str)
        return amount, currency
        
    except ValueError:
        return None, currency

def categorize_by_vendor(vendor_name: str) -> str:
    """Categoriza basado en el nombre del proveedor"""
    if not vendor_name:
        return 'unknown'
    
    vendor_lower = vendor_name.lower()
    
    # Servicios públicos
    if any(word in vendor_lower for word in ['electric', 'gas', 'water', 'utility']):
        return 'utilities'
    
    # Software y tecnología
    if any(word in vendor_lower for word in ['microsoft', 'adobe', 'google', 'aws', 'github']):
        return 'software'
    
    # Hosting y dominios
    if any(word in vendor_lower for word in ['godaddy', 'namecheap', 'hostgator', 'cloudflare']):
        return 'hosting'
    
    # Telecomunicaciones
    if any(word in vendor_lower for word in ['verizon', 'att', 'sprint', 'tmobile', 'claro', 'movistar']):
        return 'telecommunications'
    
    # Servicios financieros
    if any(word in vendor_lower for word in ['bank', 'credit', 'paypal', 'stripe']):
        return 'financial'
    
    return 'miscellaneous'

def extract_emails_from_text(text: str) -> List[str]:
    """Extrae direcciones de email del texto"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

def extract_phone_numbers(text: str) -> List[str]:
    """Extrae números de teléfono del texto"""
    phone_patterns = [
        r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US
        r'\+?[0-9]{2,3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',  # International
    ]
    
    phones = []
    for pattern in phone_patterns:
        phones.extend(re.findall(pattern, text))
    
    return phones

def normalize_invoice_number(invoice_num: str) -> str:
    """Normaliza números de factura"""
    if not invoice_num:
        return invoice_num
    
    # Remover espacios excesivos
    normalized = re.sub(r'\s+', '', invoice_num.upper())
    
    # Asegurar formato consistente
    normalized = re.sub(r'[^\w-]', '', normalized)
    
    return normalized

# Clase para testing y desarrollo
class InvoiceExtractorTester:
    """Clase de utilidad para probar el extractor"""
    
    def __init__(self):
        self.extractor = InvoiceExtractor()
    
    async def test_with_sample_data(self):
        """Prueba el extractor con datos de muestra"""
        sample_emails = [
            {
                'content': '''
                Invoice #INV-2024-001
                From: Tech Services Inc. <billing@techservices.com>
                Date: January 15, 2024
                
                Description: Monthly hosting service
                Amount: $45.99
                Due Date: February 15, 2024
                
                Please pay by the due date.
                ''',
                'expected': {
                    'amount': 45.99,
                    'vendor': 'Tech Services Inc.',
                    'concept': 'Monthly hosting service',
                    'invoice_number': 'INV-2024-001'
                }
            },
            {
                'content': '''
                FACTURA DE SERVICIOS PÚBLICOS
                Empresa: Electricidad del Caribe S.A.
                Fecha: 15 de enero de 2024
                
                Concepto: Suministro de energía eléctrica
                Valor a pagar: $125.430 COP
                Fecha de vencimiento: 28 de febrero de 2024
                
                NIT: 900123456-1
                ''',
                'expected': {
                    'amount': 125430.0,
                    'vendor': 'Electricidad del Caribe S.A.',
                    'concept': 'Suministro de energía eléctrica',
                    'currency': 'COP'
                }
            }
        ]
        
        results = []
        for i, sample in enumerate(sample_emails):
            print(f"\n🧪 Probando muestra {i + 1}:")
            result = await self.extractor.extract_invoice_data(sample['content'])
            
            print(f"  📊 Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
            print(f"  🎯 Confianza: {result.get('confidence', 0):.0%}")
            
            results.append(result)
        
        return results