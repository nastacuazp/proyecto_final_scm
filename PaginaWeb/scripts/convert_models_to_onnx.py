#!/usr/bin/env python3
"""
Script para convertir modelos PyTorch a formato ONNX
Para ejecución en el navegador del cliente
"""

import torch
import torch.onnx
import os
import numpy as np

def convert_autoencoder_to_onnx(model_path, output_path, bottleneck_size):
    """Convertir autoencoder PyTorch a ONNX"""
    try:
        print(f"Convirtiendo {model_path} a ONNX")
        
        # Cargar modelo PyTorch
        model = torch.jit.load(model_path, map_location='cpu')
        model.eval()
        
        # Crear tensor de ejemplo (1, 3, 1024, 768)
        dummy_input = torch.randn(1, 3, 1024, 768)
        
        # Convertir a ONNX
        torch.onnx.export(
            model,
            dummy_input,
            output_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )
        
        print(f"✅ Autoencoder {bottleneck_size}b convertido: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error convirtiendo autoencoder {bottleneck_size}b: {e}")
        return False

def convert_espcn_to_onnx(model_path, output_path):
    """Convertir modelo ESPCN a ONNX"""
    try:
        print(f"Convirtiendo ESPCN {model_path} a ONNX...")
        
        # Cargar modelo PyTorch
        model = torch.jit.load(model_path, map_location='cpu')
        model.eval()
        
        # Crear tensor de ejemplo (1, 3, 1024, 768)
        dummy_input = torch.randn(1, 3, 1024, 768)
        
        # Convertir a ONNX
        torch.onnx.export(
            model,
            dummy_input,
            output_path,
            export_params=True,
            opset_version=11,
            do_constant_folding=True,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={
                'input': {0: 'batch_size'},
                'output': {0: 'batch_size'}
            }
        )
        
        print(f"✅ ESPCN convertido: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error convirtiendo ESPCN: {e}")
        return False

def verify_onnx_model(onnx_path):
    """Verificar que el modelo ONNX funcione"""
    try:
        import onnx
        import onnxruntime as ort
        
        # Cargar y verificar modelo ONNX
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)
        
        # Probar inferencia
        session = ort.InferenceSession(onnx_path)
        input_name = session.get_inputs()[0].name
        
        # Crear datos de prueba
        test_input = np.random.randn(1, 3, 1024, 768).astype(np.float32)
        
        # Ejecutar inferencia
        result = session.run(None, {input_name: test_input})
        
        print(f"✅ Modelo ONNX verificado: {onnx_path}")
        print(f"   Entrada: {test_input.shape}")
        print(f"   Salida: {result[0].shape}")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando modelo ONNX: {e}")
        return False

def main():
    """Función principal de conversión"""
    print("🔄 Iniciando conversión de modelos PyTorch a ONNX")
    print("=" * 60)
    
    # Crear directorio para modelos ONNX
    onnx_dir = 'static/models'
    os.makedirs(onnx_dir, exist_ok=True)
    
    models_converted = 0
    total_models = 4
    
    # Convertir autoencoders
    for bottleneck in [8, 16, 32]:
        pytorch_path = f'models/autoencoder_b{bottleneck}.pt'
        onnx_path = f'{onnx_dir}/autoencoder_b{bottleneck}.onnx'
        
        if os.path.exists(pytorch_path):
            if convert_autoencoder_to_onnx(pytorch_path, onnx_path, bottleneck):
                if verify_onnx_model(onnx_path):
                    models_converted += 1
        else:
            print(f"⚠️  Modelo no encontrado: {pytorch_path}")
    
    # Convertir ESPCN
    espcn_pytorch_path = 'models/espcn_model.pt'
    espcn_onnx_path = f'{onnx_dir}/espcn_model.onnx'
    
    if os.path.exists(espcn_pytorch_path):
        if convert_espcn_to_onnx(espcn_pytorch_path, espcn_onnx_path):
            if verify_onnx_model(espcn_onnx_path):
                models_converted += 1
    else:
        print(f"⚠️  Modelo ESPCN no encontrado: {espcn_pytorch_path}")
    
    print("\n" + "=" * 60)
    print(f"📊 Resumen de conversión:")
    print(f"   Modelos convertidos: {models_converted}/{total_models}")
    print(f"   Directorio ONNX: {onnx_dir}")
    
    if models_converted == total_models:
        print("🎉 ¡Todos los modelos convertidos exitosamente!")
        print("   Los clientes ahora pueden usar los modelos en el navegador")
    else:
        print("⚠️  Algunos modelos no se pudieron convertir")
        print("   Verifica que los archivos .pt estén en la carpeta 'models/'")
    
    # Crear archivo de información
    create_model_info_file(onnx_dir, models_converted)

def create_model_info_file(onnx_dir, models_converted):
    """Crear archivo JSON con información de los modelos"""
    model_info = {
        "version": "1.0",
        "converted_at": "2024-01-15",
        "total_models": models_converted,
        "models": {
            "autoencoders": {
                "8": {
                    "file": "autoencoder_b8.onnx",
                    "compression": "high",
                    "quality": "low",
                    "use_case": "slow_networks"
                },
                "16": {
                    "file": "autoencoder_b16.onnx", 
                    "compression": "medium",
                    "quality": "medium",
                    "use_case": "normal_networks"
                },
                "32": {
                    "file": "autoencoder_b32.onnx",
                    "compression": "low", 
                    "quality": "high",
                    "use_case": "fast_networks"
                }
            },
            "enhancement": {
                "espcn": {
                    "file": "espcn_model.onnx",
                    "type": "super_resolution",
                    "use_case": "image_enhancement"
                }
            }
        },
        "input_shape": [1, 3, 1024, 768],
        "output_shape": [1, 3, 1024, 768],
        "format": "ONNX",
        "opset_version": 11
    }
    
    info_path = f'{onnx_dir}/models_info.json'
    import json
    with open(info_path, 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print(f"📄 Información de modelos guardada: {info_path}")

if __name__ == "__main__":
    main()
