#!/usr/bin/env python3
"""
Script para crear un archivo de prueba para mediciones de velocidad
"""

import os
import random

def create_test_file(size_mb=1, output_path='static/test/speedtest.jpg'):
    """Crear un archivo de prueba del tamaño especificado"""
    # Asegurarse de que el directorio existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Crear archivo con datos aleatorios
    size_bytes = size_mb * 1024 * 1024
    with open(output_path, 'wb') as f:
        f.write(os.urandom(size_bytes))
    
    print(f"Archivo de prueba creado: {output_path} ({size_mb}MB)")

if __name__ == "__main__":
    create_test_file()
    print("Listo para pruebas de velocidad")
