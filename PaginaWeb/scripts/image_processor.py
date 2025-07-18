#!/usr/bin/env python3
"""
Procesador de imágenes para Dyzen
Funciones para recortar, comprimir y mejorar imágenes
"""

from PIL import Image, ImageOps
import os
import math

def crop_center_square(image_path, output_path=None):
    """
    Recorta una imagen desde el centro para hacerla cuadrada
    
    Args:
        image_path: Ruta a la imagen original
        output_path: Ruta donde guardar la imagen recortada (opcional)
        
    Returns:
        Ruta a la imagen recortada
    """
    try:
        with Image.open(image_path) as img:
            # Obtener dimensiones
            width, height = img.size
            
            # Determinar el lado más corto
            size = min(width, height)
            
            # Calcular coordenadas para recortar desde el centro
            left = (width - size) / 2
            top = (height - size) / 2
            right = (width + size) / 2
            bottom = (height + size) / 2
            
            # Recortar la imagen
            cropped_img = img.crop((left, top, right, bottom))
            
            # Si no se especifica ruta de salida, crear una
            if not output_path:
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                dir_name = os.path.dirname(image_path)
                output_path = os.path.join(dir_name, f"{base_name}_square.jpg")
            
            # Guardar imagen recortada
            cropped_img.save(output_path, quality=95)
            
            print(f"Imagen recortada guardada en: {output_path}")
            return output_path
            
    except Exception as e:
        print(f"Error recortando imagen: {e}")
        return image_path

def create_thumbnail(image_path, size=(400, 400), output_path=None):
    """
    Crea una miniatura cuadrada de la imagen
    
    Args:
        image_path: Ruta a la imagen original
        size: Tamaño de la miniatura (ancho, alto)
        output_path: Ruta donde guardar la miniatura (opcional)
        
    Returns:
        Ruta a la miniatura
    """
    try:
        with Image.open(image_path) as img:
            # Convertir a RGB si es necesario
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Recortar al centro y redimensionar
            thumb = ImageOps.fit(img, size, Image.LANCZOS, centering=(0.5, 0.5))
            
            # Si no se especifica ruta de salida, crear una
            if not output_path:
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                dir_name = os.path.dirname(image_path)
                output_path = os.path.join(dir_name, f"{base_name}_thumb.jpg")
            
            # Guardar miniatura
            thumb.save(output_path, 'JPEG', quality=85)
            
            print(f"Miniatura guardada en: {output_path}")
            return output_path
            
    except Exception as e:
        print(f"Error creando miniatura: {e}")
        return image_path

def process_upload_image(image_path, create_thumb=True):
    """
    Procesa una imagen recién subida: recorta al centro y crea miniatura
    
    Args:
        image_path: Ruta a la imagen original
        create_thumb: Si se debe crear una miniatura
        
    Returns:
        Dict con rutas a las imágenes procesadas
    """
    result = {
        'original': image_path,
        'square': None,
        'thumbnail': None
    }
    
    try:
        # Recortar al centro
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        dir_name = os.path.dirname(image_path)
        square_path = os.path.join(dir_name, f"{base_name}_square.jpg")
        
        result['square'] = crop_center_square(image_path, square_path)
        
        # Crear miniatura si se solicita
        if create_thumb:
            thumb_path = os.path.join(dir_name, f"{base_name}_thumb.jpg")
            result['thumbnail'] = create_thumbnail(result['square'], (400, 400), thumb_path)
            
        return result
        
    except Exception as e:
        print(f"Error procesando imagen: {e}")
        return result

if __name__ == "__main__":
    # Prueba simple
    import sys
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        print(f"Procesando imagen: {input_path}")
        
        result = process_upload_image(input_path)
        print("Resultado:")
        for key, path in result.items():
            print(f"  {key}: {path}")
    else:
        print("Uso: python image_processor.py ruta/a/imagen.jpg")
