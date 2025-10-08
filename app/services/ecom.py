"""
Extractor específico para productos de e-commerce.
Extrae información de productos desde schema.org, microdata y contenido HTML.
"""
import logging
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from app.services.utils import TextUtils

logger = logging.getLogger(__name__)


class EcommerceExtractor:
    """Extractor especializado para productos de e-commerce."""
    
    def __init__(self):
        self.text_utils = TextUtils()
    
    def extract_products(self, parsed_data: Dict[str, Any], base_url: str) -> List[Dict[str, Any]]:
        """
        Extrae productos de los datos parseados.
        
        Args:
            parsed_data: Datos parseados del HTML
            base_url: URL base para resolver enlaces relativos
            
        Returns:
            Lista de productos extraídos
        """
        products = []
        
        try:
            # Extraer de schema.org
            schema_products = self._extract_from_schema(parsed_data)
            products.extend(schema_products)
            
            # Extraer de microdata
            microdata_products = self._extract_from_microdata(parsed_data)
            products.extend(microdata_products)
            
            # Extraer de contenido HTML (fallback)
            html_products = self._extract_from_html_content(parsed_data, base_url)
            products.extend(html_products)
            
            # Limpiar y deduplicar productos
            cleaned_products = self._clean_and_deduplicate_products(products)
            
            logger.info(f"Extraídos {len(cleaned_products)} productos únicos")
            return cleaned_products
            
        except Exception as e:
            logger.error(f"Error extrayendo productos: {e}")
            return []
    
    def _extract_from_schema(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrae productos de datos schema.org JSON-LD."""
        products = []
        
        try:
            schema_data = parsed_data.get('schema_data', {})
            json_ld_items = schema_data.get('json_ld', [])
            
            for item in json_ld_items:
                if isinstance(item, dict):
                    # Producto individual
                    if item.get('@type') == 'Product':
                        product = self._parse_schema_product(item)
                        if product:
                            products.append(product)
                    
                    # Lista de productos
                    elif item.get('@type') == 'ItemList':
                        item_list = item.get('itemListElement', [])
                        for list_item in item_list:
                            if isinstance(list_item, dict):
                                product_data = list_item.get('item', {})
                                if product_data.get('@type') == 'Product':
                                    product = self._parse_schema_product(product_data)
                                    if product:
                                        products.append(product)
                    
                    # Lista de elementos
                    elif isinstance(item, list):
                        for sub_item in item:
                            if isinstance(sub_item, dict) and sub_item.get('@type') == 'Product':
                                product = self._parse_schema_product(sub_item)
                                if product:
                                    products.append(product)
            
            logger.debug(f"Extraídos {len(products)} productos de schema.org")
            return products
            
        except Exception as e:
            logger.warning(f"Error extrayendo productos de schema.org: {e}")
            return []
    
    def _extract_from_microdata(self, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrae productos de microdata."""
        products = []
        
        try:
            schema_data = parsed_data.get('schema_data', {})
            microdata_items = schema_data.get('microdata', [])
            
            for item in microdata_items:
                if 'Product' in item.get('type', ''):
                    product = self._parse_microdata_product(item)
                    if product:
                        products.append(product)
            
            logger.debug(f"Extraídos {len(products)} productos de microdata")
            return products
            
        except Exception as e:
            logger.warning(f"Error extrayendo productos de microdata: {e}")
            return []
    
    def _extract_from_html_content(self, parsed_data: Dict[str, Any], base_url: str) -> List[Dict[str, Any]]:
        """Extrae productos del contenido HTML usando selectores comunes."""
        products = []
        
        try:
            # Esta función requeriría acceso al HTML parser original
            # Por ahora retornamos lista vacía, se puede implementar después
            # si se necesita extracción adicional desde HTML puro
            
            logger.debug("Extracción HTML no implementada aún")
            return products
            
        except Exception as e:
            logger.warning(f"Error extrayendo productos de HTML: {e}")
            return []
    
    def _parse_schema_product(self, product_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parsea un producto de schema.org."""
        try:
            product = {
                'nombre': '',
                'categoria': None,
                'marca': None,
                'precio': None,
                'moneda': None,
                'descripcion': None,
                'imagen': None,
                'url': None,
                'disponibilidad': None,
                'sku': None
            }
            
            # Nombre
            name = product_data.get('name', '')
            if name:
                product['nombre'] = name.strip()
            else:
                return None  # Producto sin nombre no es válido
            
            # Descripción
            description = product_data.get('description', '')
            if description:
                product['descripcion'] = description.strip()
            
            # Categoría
            category = product_data.get('category', '')
            if category:
                if isinstance(category, str):
                    product['categoria'] = category.strip()
                elif isinstance(category, dict):
                    product['categoria'] = category.get('name', '').strip()
            
            # Marca
            brand = product_data.get('brand', '')
            if brand:
                if isinstance(brand, str):
                    product['marca'] = brand.strip()
                elif isinstance(brand, dict):
                    product['marca'] = brand.get('name', '').strip()
            
            # SKU
            sku = product_data.get('sku', '')
            if sku:
                product['sku'] = sku.strip()
            
            # Imagen
            image = product_data.get('image', '')
            if image:
                if isinstance(image, str):
                    product['imagen'] = image.strip()
                elif isinstance(image, list) and image:
                    product['imagen'] = image[0].strip()
                elif isinstance(image, dict):
                    product['imagen'] = image.get('url', '').strip()
            
            # URL del producto
            url = product_data.get('url', '')
            if url:
                product['url'] = url.strip()
            
            # Disponibilidad
            availability = product_data.get('availability', '')
            if availability:
                product['disponibilidad'] = availability.strip()
            
            # Precio y ofertas
            offers = product_data.get('offers', {})
            if offers:
                price_info = self._extract_price_from_offers(offers)
                if price_info:
                    product['precio'] = price_info['precio']
                    product['moneda'] = price_info['moneda']
            
            return product
            
        except Exception as e:
            logger.warning(f"Error parseando producto schema.org: {e}")
            return None
    
    def _parse_microdata_product(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parsea un producto de microdata."""
        try:
            properties = item.get('properties', {})
            
            product = {
                'nombre': '',
                'categoria': None,
                'marca': None,
                'precio': None,
                'moneda': None,
                'descripcion': None,
                'imagen': None,
                'url': None,
                'disponibilidad': None,
                'sku': None
            }
            
            # Nombre
            name = properties.get('name', '')
            if name:
                product['nombre'] = name.strip()
            else:
                return None  # Producto sin nombre no es válido
            
            # Descripción
            description = properties.get('description', '')
            if description:
                product['descripcion'] = description.strip()
            
            # Categoría
            category = properties.get('category', '')
            if category:
                product['categoria'] = category.strip()
            
            # Marca
            brand = properties.get('brand', '')
            if brand:
                product['marca'] = brand.strip()
            
            # SKU
            sku = properties.get('sku', '')
            if sku:
                product['sku'] = sku.strip()
            
            # Imagen
            image = properties.get('image', '')
            if image:
                product['imagen'] = image.strip()
            
            # URL del producto
            url = properties.get('url', '')
            if url:
                product['url'] = url.strip()
            
            # Disponibilidad
            availability = properties.get('availability', '')
            if availability:
                product['disponibilidad'] = availability.strip()
            
            # Precio
            price = properties.get('price', '')
            if price:
                price_info = self.text_utils.extract_price(price)
                if price_info:
                    product['precio'] = price_info['price']
                    product['moneda'] = price_info['currency']
            
            return product
            
        except Exception as e:
            logger.warning(f"Error parseando producto microdata: {e}")
            return None
    
    def _extract_price_from_offers(self, offers: Any) -> Optional[Dict[str, Any]]:
        """Extrae precio de ofertas de schema.org."""
        try:
            if isinstance(offers, dict):
                # Oferta individual
                price = offers.get('price', '')
                currency = offers.get('priceCurrency', 'EUR')
                
                if price:
                    if isinstance(price, (int, float)):
                        return {'precio': float(price), 'moneda': currency}
                    elif isinstance(price, str):
                        price_info = self.text_utils.extract_price(price)
                        if price_info:
                            return {'precio': price_info['price'], 'moneda': price_info['currency']}
            
            elif isinstance(offers, list) and offers:
                # Lista de ofertas, tomar la primera
                first_offer = offers[0]
                if isinstance(first_offer, dict):
                    price = first_offer.get('price', '')
                    currency = first_offer.get('priceCurrency', 'EUR')
                    
                    if price:
                        if isinstance(price, (int, float)):
                            return {'precio': float(price), 'moneda': currency}
                        elif isinstance(price, str):
                            price_info = self.text_utils.extract_price(price)
                            if price_info:
                                return {'precio': price_info['price'], 'moneda': price_info['currency']}
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extrayendo precio de ofertas: {e}")
            return None
    
    def _clean_and_deduplicate_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Limpia y elimina productos duplicados."""
        if not products:
            return []
        
        # Eliminar productos sin nombre
        valid_products = [p for p in products if p.get('nombre', '').strip()]
        
        # Eliminar duplicados por nombre (case insensitive)
        seen_names = set()
        unique_products = []
        
        for product in valid_products:
            name_lower = product['nombre'].lower().strip()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_products.append(product)
        
        # Ordenar por nombre para consistencia
        unique_products.sort(key=lambda x: x['nombre'].lower())
        
        logger.debug(f"Deduplicación: {len(products)} -> {len(unique_products)} productos")
        return unique_products
    
    def extract_categories(self, products: List[Dict[str, Any]]) -> List[str]:
        """
        Extrae categorías únicas de una lista de productos.
        
        Args:
            products: Lista de productos
            
        Returns:
            Lista de categorías únicas
        """
        categories = set()
        
        for product in products:
            categoria = product.get('categoria')
            if categoria and categoria.strip():
                categories.add(categoria.strip())
        
        return sorted(list(categories))
    
    def extract_brands(self, products: List[Dict[str, Any]]) -> List[str]:
        """
        Extrae marcas únicas de una lista de productos.
        
        Args:
            products: Lista de productos
            
        Returns:
            Lista de marcas únicas
        """
        brands = set()
        
        for product in products:
            marca = product.get('marca')
            if marca and marca.strip():
                brands.add(marca.strip())
        
        return sorted(list(brands))
    
    def get_price_range(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula rango de precios de una lista de productos.
        
        Args:
            products: Lista de productos
            
        Returns:
            Diccionario con información de precios
        """
        prices = []
        currencies = set()
        
        for product in products:
            precio = product.get('precio')
            moneda = product.get('moneda')
            
            if precio is not None and precio > 0:
                prices.append(precio)
                if moneda:
                    currencies.add(moneda)
        
        if not prices:
            return {
                'min_price': None,
                'max_price': None,
                'avg_price': None,
                'currency': None,
                'count': 0
            }
        
        return {
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': sum(prices) / len(prices),
            'currency': list(currencies)[0] if currencies else None,
            'count': len(prices)
        }

