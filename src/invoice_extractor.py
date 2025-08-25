#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Invoice Extractor - DOCUFIND
Extrae datos inteligentes de facturas de emails y adjuntos
"""

import re
import base64
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

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
    raw_matches: Dict[str, Any] = field(default_factory=dict)

class InvoiceExtractor:
    """Extractor inteligente de datos de facturas"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el extractor de facturas
        
        Args:
            config: Configuración opcional del extractor
        """
        self.config = config or {}
        
        # Patrones de regex para diferentes tipos de datos
        self.patterns = self._initialize_patterns()
        
        # Palabras clave para categorización
        self.category_keywords = self._initialize_categories()
        
        # Configuración de monedas - usando códigos ASCII y Unicode escapados
        self.currency_symbols = {
            '$': 'USD',
            '\u20AC': 'EUR',  # Euro symbol
            '\u00A3': 'GBP',  # Pound symbol
            '\u00A5': 'JPY',  # Yen symbol
            'COP': 'COP',
            'MXN': 'MXN',
            'ARS': 'ARS',
            'PEN': 'PEN',
            'CLP': 'CLP'
        }
        
        logger.info("🤖 InvoiceExtractor inicializado")
    
    def _initialize_patterns(self) -> Dict[str, List[str]]:
        """Inicializa patrones de regex para extracción"""
        # Usando caracteres Unicode escapados para símbolos de moneda
        currency_pattern = r'[\$\u20AC\u00A3\u00A5]'
        
        return {
            'amount': [
                # Montos con símbolos de moneda
                rf'total:?\s*{currency_pattern}?\s*([0-9]{{1,3}}(?:[,.]?\d{{3}})*(?:[,.]?\d{{2}})?)',
                rf'amount:?\s*{currency_pattern}?\s*([0-9]{{1,3}}(?:[,.]?\d{{3}})*(?:[,.]?\d{{2}})?)',
                rf'importe:?\s*{currency_pattern}?\s*([0-9]{{1,3}}(?:[,.]?\d{{3}})*(?:[,.]?\d{{2}})?)',
                rf'valor:?\s*{currency_pattern}?\s*([0-9]{{1,3}}(?:[,.]?\d{{3}})*(?:[,.]?\d{{2}})?)',
                rf'subtotal:?\s*{currency_pattern}?\s*([0-9]{{1,3}}(?:[,.]?\d{{3}})*(?:[,.]?\d{{2}})?)',
                # Patrones específicos por moneda
                r'\$\s*([0-9]{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'([0-9]{1,3}(?:[,.]?\d{3})*(?:[,.]?\d{2})?)\s*(?:USD|EUR|GBP|COP|MXN|ARS)',
                # Patrones en español
                rf'pagar:?\s*{currency_pattern}?\s*([0-9]{{1,3}}(?:[,.]?\d{{3}})*(?:[,.]?\d{{2}})?)',
                rf'cobrar:?\s*{currency_pattern}?\s*([0-9]{{1,3}}(?:[,.]?\d{{3}})*(?:[,.]?\d{{2}})?)',
                rf'facturar:?\s*{currency_pattern}?\s*([0-9]{{1,3}}(?:[,.]?\d{{3}})*(?:[,.]?\d{{2}})?)'
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
                r'(?:ref|reference)(?:\s*no\.?|:)?\s*([A-Z0-9-]+)',
                r'#\s*([A-Z0-9-]+)',
                r'folio:?\s*([A-Z0-9-]+)'
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
                r'(?:payment\s+due|fecha\s+límite):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ],
            'tax': [
                # Impuestos
                r'(?:tax|iva|impuesto):?\s*([0-9]+(?:[.,]\d{2})?)',
                r'(?:vat|igv):?\s*([0-9]+(?:[.,]\d{2})?)',
                r'(?:taxes|impuestos):?\s*([0-9]+(?:[.,]\d{2})?)'
            ],
            'tax_id': [
                # Identificación fiscal
                r'(?:rfc|nit|rut|cuit|ruc):?\s*([A-Z0-9-]+)',
                r'(?:tax\s+id|id\s+fiscal):?\s*([A-Z0-9-]+)',
                r'(?:vat\s+number|número\s+fiscal):?\s*([A-Z0-9-]+)'
            ]
        }
    
    def _initialize_categories(self) -> Dict[str, List[str]]:
        """Inicializa palabras clave para categorización"""
        return {
            'utilities': ['electricidad', 'gas', 'agua', 'electricity', 'water', 'power', 'utility'],
            'telecommunications': ['internet', 'telefono', 'phone', 'mobile', 'banda ancha', 'broadband'],
            'software': ['software', 'licencia', 'license', 'subscription', 'suscripcion', 'app'],
            'hosting': ['hosting', 'servidor', 'server', 'dominio', 'domain', 'cloud', 'web'],
            'office': ['oficina', 'office', 'papeleria', 'supplies', 'material'],
            'transport': ['transporte', 'transport', 'envio', 'shipping', 'delivery', 'entrega'],
            'food': ['comida', 'food', 'restaurante', 'restaurant', 'cafe', 'almuerzo', 'lunch'],
            'professional': ['servicios', 'services', 'consultoria', 'consulting', 'professional'],
            'rent': ['renta', 'rent', 'alquiler', 'lease', 'arrendamiento'],
            'insurance': ['seguro', 'insurance', 'poliza', 'policy'],
            'financial': ['banco', 'bank', 'credito', 'credit', 'prestamo', 'loan'],
            'miscellaneous': ['otros', 'other', 'misc', 'general']
        }
    
    def extract(self, content: Any) -> Optional[Dict[str, Any]]:
        """
        Extrae datos de factura del contenido
        
        Args:
            content: Contenido a procesar (texto, bytes, o dict)
            
        Returns:
            Diccionario con datos extraídos o None
        """
        try:
            # Convertir contenido a texto si es necesario
            text = self._content_to_text(content)
            
            if not text:
                logger.warning("⚠️ No se pudo obtener texto del contenido")
                return None
            
            # Extraer datos usando patrones
            extracted_data = self._extract_with_patterns(text)
            
            # Mejorar datos con análisis contextual
            enhanced_data = self._enhance_with_context(extracted_data, text)
            
            # Calcular confianza
            enhanced_data['confidence'] = self._calculate_confidence(enhanced_data)
            
            # Categorizar
            enhanced_data['category'] = self._categorize_invoice(enhanced_data, text)
            
            logger.info(f"✅ Datos extraídos con {enhanced_data['confidence']:.0%} de confianza")
            
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ Error extrayendo datos: {e}")
            return None
    
    def _content_to_text(self, content: Any) -> str:
        """Convierte diferentes tipos de contenido a texto"""
        if isinstance(content, str):
            return content
        elif isinstance(content, bytes):
            try:
                return content.decode('utf-8', errors='ignore')
            except:
                return content.decode('latin-1', errors='ignore')
        elif isinstance(content, dict):
            # Si es un dict, buscar campos relevantes
            text_parts = []
            for key in ['text', 'body', 'content', 'subject', 'description']:
                if key in content:
                    text_parts.append(str(content[key]))
            return '\n'.join(text_parts)
        else:
            return str(content)
    
    def _extract_with_patterns(self, text: str) -> Dict[str, Any]:
        """Extrae datos usando patrones regex"""
        extracted = {}
        
        for data_type, patterns in self.patterns.items():
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        # Seleccionar el mejor match
                        best_match = self._select_best_match(matches, data_type)
                        if best_match:
                            extracted[data_type] = best_match
                            break  # Usar el primer patrón que funcione
                except re.error as e:
                    logger.debug(f"Error en patrón regex: {e}")
                    continue
        
        return extracted
    
    def _select_best_match(self, matches: List[str], data_type: str) -> Optional[str]:
        """Selecciona el mejor match de una lista"""
        if not matches:
            return None
        
        # Limpiar matches
        matches = [m.strip() for m in matches if m and m.strip()]
        
        if not matches:
            return None
        
        # Lógica específica por tipo de dato
        if data_type == 'amount':
            # Para montos, seleccionar el más grande (probablemente el total)
            amounts = []
            for match in matches:
                try:
                    clean_amount = re.sub(r'[^\d.,]', '', match)
                    if clean_amount:
                        amounts.append(float(clean_amount.replace(',', '')))
                except ValueError:
                    continue
            
            if amounts:
                max_amount = max(amounts)
                return str(max_amount)
        
        elif data_type == 'vendor':
            # Para proveedor, seleccionar el más específico (no email genérico)
            for match in matches:
                if '@' not in match or not any(word in match.lower() for word in ['noreply', 'no-reply', 'donotreply']):
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
            logger.warning(f"⚠️ No se pudo parsear monto: {amount_str}")
            return 0.0
    
    def _detect_currency(self, text: str) -> str:
        """Detecta la moneda del texto"""
        # Buscar símbolos de moneda usando Unicode escapado
        currency_checks = [
            ('$', 'USD'),
            ('\u20AC', 'EUR'),  # Euro
            ('\u00A3', 'GBP'),  # Libra
            ('\u00A5', 'JPY'),  # Yen
        ]
        
        for symbol, currency in currency_checks:
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
            # Determinar qué tipo de peso
            if 'colombia' in text.lower() or 'cop' in text.upper():
                return 'COP'
            elif 'mexico' in text.lower() or 'mx' in text.lower():
                return 'MXN'
            elif 'argentina' in text.lower() or 'arg' in text.lower():
                return 'ARS'
            return 'COP'  # Default para pesos
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
        
        # Limitar longitud
        if len(concept) > 200:
            concept = concept[:200] + "..."
        
        return concept
    
    def _infer_concept_from_context(self, text: str) -> Optional[str]:
        """Intenta inferir el concepto del contexto"""
        # Buscar líneas que parezcan conceptos
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            # Buscar líneas descriptivas
            if 10 < len(line) < 100:
                # Evitar líneas que sean solo números o emails
                if not re.match(r'^[\d\s.,]+$', line) and '@' not in line:
                    # Verificar que tenga palabras reales
                    words = line.split()
                    if len(words) >= 2 and len(words) <= 15:
                        return line
        
        return None
    
    def _detect_payment_method(self, text: str) -> Optional[str]:
        """Detecta el método de pago"""
        methods = {
            'credit_card': ['tarjeta', 'card', 'visa', 'mastercard', 'amex'],
            'transfer': ['transferencia', 'transfer', 'wire', 'banco'],
            'cash': ['efectivo', 'cash', 'contado'],
            'paypal': ['paypal'],
            'check': ['cheque', 'check']
        }
        
        text_lower = text.lower()
        for method, keywords in methods.items():
            if any(keyword in text_lower for keyword in keywords):
                return method
        
        return None
    
    def _detect_language(self, text: str) -> str:
        """Detecta el idioma del texto"""
        spanish_words = ['factura', 'importe', 'fecha', 'proveedor', 'concepto', 'pagar']
        english_words = ['invoice', 'amount', 'date', 'vendor', 'concept', 'payment']
        
        text_lower = text.lower()
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if spanish_count > english_count:
            return 'es'
        elif english_count > spanish_count:
            return 'en'
        else:
            return 'unknown'
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calcula la confianza de la extracción"""
        confidence = 0.0
        weights = {
            'amount': 0.25,
            'vendor': 0.20,
            'invoice_number': 0.15,
            'concept': 0.15,
            'invoice_date': 0.10,
            'currency': 0.05,
            'tax': 0.05,
            'category': 0.05
        }
        
        for field, weight in weights.items():
            if field in data and data[field]:
                confidence += weight
        
        return min(confidence, 1.0)
    
    def _categorize_invoice(self, data: Dict[str, Any], text: str) -> str:
        """Categoriza la factura basándose en el contenido"""
        text_lower = text.lower()
        vendor_lower = str(data.get('vendor', '')).lower()
        concept_lower = str(data.get('concept', '')).lower()
        
        # Buscar categoría por palabras clave
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword in text_lower or keyword in vendor_lower or keyword in concept_lower:
                    return category
        
        return 'miscellaneous'
    
    def extract_from_attachment(self, attachment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extrae datos de un adjunto"""
        try:
            filename = attachment.get('filename', '').lower()
            content_type = attachment.get('content_type', '')
            
            # Solo procesar archivos de texto por ahora
            if content_type.startswith('text/') or filename.endswith(('.txt', '.csv')):
                content = base64.b64decode(attachment['content'])
                return self.extract(content)
            
            elif filename.endswith('.pdf'):
                # Para PDFs necesitaríamos PyPDF2 o similar
                logger.info(f"📄 PDF detectado: {filename} (extracción de PDF no implementada)")
                return None
            
            elif filename.endswith(('.xml', '.cfdi')):
                # Para XML/CFDI necesitaríamos xml.etree
                logger.info(f"📄 XML/CFDI detectado: {filename} (extracción XML no implementada)")
                return None
            
            elif filename.endswith(('.doc', '.docx')):
                # Para Word necesitaríamos python-docx
                logger.info(f"📄 Documento Word detectado: {filename} (extracción no implementada)")
                return None
            
            else:
                logger.debug(f"📄 Tipo de archivo no soportado: {filename}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Error extrayendo datos de adjunto: {e}")
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
                elif amount > 10000000:
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
    
    # Detectar moneda usando caracteres Unicode escapados
    currency = None
    currency_symbols = [
        ('$', 'USD'),
        ('\u20AC', 'EUR'),  # Euro
        ('\u00A3', 'GBP'),  # Libra  
        ('\u00A5', 'JPY'),  # Yen
    ]
    
    for symbol, curr in currency_symbols:
        if symbol in amount_str:
            currency = curr
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
        r'\+?[0-9]{2,3}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{4}',  # Internacional
        r'\b[0-9]{10}\b',  # 10 dígitos seguidos
    ]
    
    phone_numbers = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        phone_numbers.extend(matches)
    
    return list(set(phone_numbers))  # Eliminar duplicados

# Clase de prueba para desarrollo
class InvoiceExtractorTester:
    """Clase para probar el extractor de facturas"""
    
    def __init__(self):
        self.extractor = InvoiceExtractor()
        
    async def test_extraction(self):
        """Prueba la extracción con datos de ejemplo"""
        sample_emails = [
            {
                'content': '''
                Invoice #INV-2024-001
                From: Tech Services Inc. <billing@techservices.com>
                Date: January 15, 2024
                
                Dear Customer,
                
                Your monthly hosting service invoice is ready.
                
                Description: Monthly hosting service
                Amount Due: $45.99 USD
                Due Date: February 15, 2024
                
                Thank you for your business!
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
            result = self.extractor.extract(sample['content'])
            
            if result:
                print(f"  📊 Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
                print(f"  🎯 Confianza: {result.get('confidence', 0):.0%}")
            else:
                print("  ❌ No se pudieron extraer datos")
            
            results.append(result)
        
        return results

# Main para pruebas
if __name__ == "__main__":
    import asyncio
    
    print("🚀 Probando InvoiceExtractor...")
    print("=" * 60)
    
    tester = InvoiceExtractorTester()
    asyncio.run(tester.test_extraction())
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")