#!/usr/bin/env python3
"""
Script para configurar los modelos de Dyzen
Desarrollado por Grupo 1 - SCM
"""

import os
import shutil
import torch

def setup_model_directory():
    """Crear directorio de modelos y verificar archivos"""
    
    # Crear directorio models si no existe
    models_dir = 'models'
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"Directorio '{models_dir}' creado")
    else:
        print(f"Directorio '{models_dir}' ya existe")
    
    # Lista de modelos esperados
    expected_models = [
        'autoencoder_b8.pt',
        'autoencoder_b16.pt', 
        'autoencoder_b32.pt',
        'espcn_model.pt'
    ]
    
    print("\nVerificando modelos:")
    found_models = []
    missing_models = []
    
    for model_name in expected_models:
        model_path = os.path.join(models_dir, model_name)
        if os.path.exists(model_path):
            # Verificar que el archivo sea válido
            try:
                model = torch.jit.load(model_path, map_location='cpu')
                file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
                print(f"  {model_name} - {file_size:.1f}MB - Válido")
                found_models.append(model_name)
            except Exception as e:
                print(f"  {model_name} - Error: {e}")
                missing_models.append(model_name)
        else:
            print(f"  {model_name} - No encontrado")
            missing_models.append(model_name)
    
    # Resumen
    print(f"\nResumen:")
    print(f"  Modelos encontrados: {len(found_models)}/4")
    print(f"  Modelos faltantes: {len(missing_models)}/4")
    
    if missing_models:
        print(f"\nInstrucciones:")
        print(f"  1. Copia tus modelos a la carpeta '{models_dir}/':")
        for model in missing_models:
            print(f"     - {model}")
        print(f"  2. Asegúrate de que los nombres coincidan exactamente")
        print(f"  3. Los modelos deben estar en formato TorchScript (.pt)")
        
    return len(missing_models) == 0

def test_model_compatibility():
    """Probar que los modelos funcionen correctamente"""
    print("\nProbando compatibilidad de modelos:")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"  Dispositivo: {device}")
    
    # Crear tensor de prueba (imagen RGB 1024x768)
    test_input = torch.randn(1, 3, 1024, 768).to(device)
    print(f"  Tensor de prueba: {test_input.shape}")
    
    success_count = 0
    
    # Probar autoencoders
    for bottleneck in [8, 16, 32]:
        model_path = f'models/autoencoder_b{bottleneck}.pt'
        
        if os.path.exists(model_path):
            try:
                model = torch.jit.load(model_path, map_location=device)
                model.eval()
                
                with torch.no_grad():
                    output = model(test_input)
                
                if output.shape == test_input.shape:
                    print(f"  autoencoder_b{bottleneck}.pt - Funcionando correctamente")
                    success_count += 1
                else:
                    print(f"  autoencoder_b{bottleneck}.pt - Forma incorrecta: {output.shape}")
                    
            except Exception as e:
                print(f"  autoencoder_b{bottleneck}.pt - Error: {e}")
        else:
            print(f"  autoencoder_b{bottleneck}.pt - No encontrado")
    
    # Probar ESPCN (misma entrada 1024x768)
    espcn_path = 'models/espcn_model.pt'
    if os.path.exists(espcn_path):
        try:
            model = torch.jit.load(espcn_path, map_location=device)
            model.eval()
            
            with torch.no_grad():
                output = model(test_input)
            
            if output.shape == test_input.shape:
                print(f"  espcn_model.pt - Funcionando correctamente ({output.shape})")
                success_count += 1
            else:
                print(f"  espcn_model.pt - Forma inesperada: {output.shape}")
                
        except Exception as e:
            print(f"  espcn_model.pt - Error: {e}")
    else:
        print(f"  espcn_model.pt - No encontrado")
    
    print(f"\nResultado: {success_count}/4 modelos funcionando")
    return success_count

def create_readme():
    """Crear README para el directorio de modelos"""
    readme_content = """# Modelos de Dyzen

Este directorio contiene los modelos entrenados para el sistema de compresión adaptativa Dyzen.

## Archivos Requeridos

### Autoencoders
- `autoencoder_b8.pt` - Compresión alta (8 bits) para redes lentas
- `autoencoder_b16.pt` - Compresión media (16 bits) para redes normales  
- `autoencoder_b32.pt` - Compresión baja (32 bits) para redes rápidas

### Super-Resolución
- `espcn_model.pt` - Modelo ESPCN para mejora de imágenes

## Especificaciones Técnicas

### Autoencoders
- **Entrada**: RGB 1024x768 (Alto x Ancho)
- **Salida**: RGB 1024x768 (Alto x Ancho)
- **Formato**: TorchScript (.pt)
- **Arquitectura**: SingleBottleneckAutoencoder

### ESPCN
- **Entrada**: RGB 1024x768 (Alto x Ancho)
- **Salida**: RGB 1024x768 (Alto x Ancho)
- **Formato**: TorchScript (.pt)
- **Arquitectura**: ESPCN con 3 capas convolucionales

## Uso

Los modelos se cargan automáticamente al iniciar el servidor Dyzen.
Si algún modelo no está disponible, el sistema usará fallbacks:
- Autoencoders → Compresión JPEG tradicional
- ESPCN → Filtros de mejora básicos

## Desarrollado por

Grupo 1 - SCM
"""

    readme_path = 'models/README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"README creado: {readme_path}")

def main():
    """Función principal del setup"""
    print("Configuración de Modelos para Dyzen")
    print("=" * 50)
    
    # Configurar directorio
    models_ready = setup_model_directory()
    
    if models_ready:
        # Probar modelos si están todos presentes
        working_models = test_model_compatibility()
        
        if working_models == 4:
            print("\nTodos los modelos están listos!")
            print("   Puedes ejecutar: python app.py")
        else:
            print(f"\nAlgunos modelos tienen problemas")
            print("   El sistema funcionará con fallbacks")
    else:
        print(f"\nCompleta la instalación de modelos y ejecuta este script nuevamente")
    
    # Crear documentación
    create_readme()
    
    print("\nSetup completado")

if __name__ == "__main__":
    main()
