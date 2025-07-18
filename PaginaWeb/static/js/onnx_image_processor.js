/**
 * Procesador de imágenes usando modelos ONNX en el cliente
 * Dyzen - Sistema de compresión adaptativa
 */

// Import ONNX.js
const ort = window.ort

class ONNXImageProcessor {
  constructor() {
    this.session = null
    this.isLoading = false
    this.loadedModels = new Map()
    this.modelInfo = null
    this.canvas = document.createElement("canvas")
    this.ctx = this.canvas.getContext("2d")

    // Inicializar ONNX.js
    this.initONNX()
  }

  async initONNX() {
    try {
      // Cargar información de modelos
      const response = await fetch("/static/models/models_info.json")
      this.modelInfo = await response.json()
      console.log("Información de modelos cargada:", this.modelInfo)
    } catch (error) {
      console.error("Error cargando información de modelos:", error)
    }
  }

  /**
   * Cargar modelo ONNX específico
   */
  async loadModel(modelType, compressionLevel = null) {
    const modelKey = compressionLevel ? `${modelType}_${compressionLevel}` : modelType

    if (this.loadedModels.has(modelKey)) {
      return this.loadedModels.get(modelKey)
    }

    try {
      this.isLoading = true
      let modelPath

      if (modelType === "autoencoder") {
        modelPath = `/static/models/autoencoder_b${compressionLevel}.onnx`
      } else if (modelType === "espcn") {
        modelPath = `/static/models/espcn_model.onnx`
      } else {
        throw new Error(`Tipo de modelo desconocido: ${modelType}`)
      }

      console.log(`Cargando modelo: ${modelPath}`)

      // Cargar modelo ONNX
      const session = await ort.InferenceSession.create(modelPath)

      this.loadedModels.set(modelKey, session)
      console.log(`Modelo cargado: ${modelKey}`)

      this.isLoading = false
      return session
    } catch (error) {
      this.isLoading = false
      console.error(`Error cargando modelo ${modelKey}:`, error)
      throw error
    }
  }

  /**
   * Convertir imagen a tensor para ONNX
   */
  imageToTensor(imageElement) {
    // Configurar canvas con dimensiones del modelo
    this.canvas.width = 768 // Ancho
    this.canvas.height = 1024 // Alto

    // Dibujar imagen redimensionada
    this.ctx.drawImage(imageElement, 0, 0, 768, 1024)

    // Obtener datos de imagen
    const imageData = this.ctx.getImageData(0, 0, 768, 1024)
    const { data } = imageData

    // Convertir a tensor [1, 3, 1024, 768] (NCHW)
    const tensor = new Float32Array(1 * 3 * 1024 * 768)

    for (let i = 0; i < 1024 * 768; i++) {
      const pixelIndex = i * 4
      // Normalizar a [0, 1] y organizar por canales
      tensor[i] = data[pixelIndex] / 255.0 // R
      tensor[1024 * 768 + i] = data[pixelIndex + 1] / 255.0 // G
      tensor[2 * 1024 * 768 + i] = data[pixelIndex + 2] / 255.0 // B
    }

    return new ort.Tensor("float32", tensor, [1, 3, 1024, 768])
  }

  /**
   * Convertir tensor a imagen
   */
  tensorToImage(tensor) {
    const [batch, channels, height, width] = tensor.dims
    const data = tensor.data

    // Crear ImageData
    const imageData = new ImageData(width, height)
    const pixels = imageData.data

    for (let i = 0; i < height * width; i++) {
      const pixelIndex = i * 4
      // Desnormalizar y reorganizar canales
      pixels[pixelIndex] = Math.min(255, Math.max(0, data[i] * 255)) // R
      pixels[pixelIndex + 1] = Math.min(255, Math.max(0, data[height * width + i] * 255)) // G
      pixels[pixelIndex + 2] = Math.min(255, Math.max(0, data[2 * height * width + i] * 255)) // B
      pixels[pixelIndex + 3] = 255 // A
    }

    // Dibujar en canvas
    this.canvas.width = width
    this.canvas.height = height
    this.ctx.putImageData(imageData, 0, 0)

    return this.canvas.toDataURL("image/jpeg", 0.95)
  }

  /**
   * Comprimir imagen usando autoencoder ONNX
   */
  async compressImage(imageFile, compressionLevel) {
    try {
      console.log(`Comprimiendo imagen con nivel ${compressionLevel}...`)

      // Cargar modelo autoencoder
      const session = await this.loadModel("autoencoder", compressionLevel)

      // Cargar imagen
      const img = await this.loadImageFromFile(imageFile)

      // Convertir a tensor
      const inputTensor = this.imageToTensor(img)

      // Ejecutar inferencia
      const feeds = { input: inputTensor }
      const results = await session.run(feeds)

      // Convertir resultado a imagen
      const outputTensor = results.output
      const compressedDataUrl = this.tensorToImage(outputTensor)

      // Convertir a blob
      const blob = await this.dataUrlToBlob(compressedDataUrl)

      console.log(`✅ Imagen comprimida con autoencoder ${compressionLevel}b`)

      return {
        blob: blob,
        dataUrl: compressedDataUrl,
        originalSize: imageFile.size,
        compressedSize: blob.size,
        compressionLevel: compressionLevel,
        compressionRatio: (((imageFile.size - blob.size) / imageFile.size) * 100).toFixed(1),
        method: "onnx_autoencoder",
      }
    } catch (error) {
      console.error("Error en compresión ONNX:", error)
      throw error
    }
  }

  /**
   * Procesar imagen completa: comprimir y opcionalmente mejorar
   */
  async processImageComplete(imageFile, compressionLevel, enhanceWithESPCN = false) {
    try {
      console.log("🔄 Iniciando procesamiento completo con ONNX...")

      const result = {
        original: {
          file: imageFile,
          size: imageFile.size,
        },
      }

      // Resolver nivel de compresión si es "auto"
      let actualCompressionLevel = compressionLevel
      if (compressionLevel === 'auto') {
        // Obtener condiciones de red actuales
        try {
          const networkResponse = await fetch('/api/network')
          const networkData = await networkResponse.json()
          actualCompressionLevel = networkData.compression
          console.log(`🔄 Modo auto: usando nivel ${actualCompressionLevel} basado en red ${networkData.quality}`)
        } catch (error) {
          console.warn('Error obteniendo condiciones de red, usando nivel por defecto:', error)
          actualCompressionLevel = 16 // Valor por defecto
        }
      }

      // 1. Comprimir con autoencoder
      if (actualCompressionLevel > 0) {
        result.compressed = await this.compressImage(imageFile, actualCompressionLevel)
      } else {
        // Sin compresión, solo redimensionar
        const resized = await this.resizeImage(imageFile, 768, 1024)
        result.compressed = {
          blob: resized.blob,
          dataUrl: resized.dataUrl,
          originalSize: imageFile.size,
          compressedSize: resized.blob.size,
          compressionLevel: actualCompressionLevel,
          compressionRatio: "0",
          method: "resize_only",
        }
      }

      // 2. Crear thumbnail
      result.thumbnail = await this.createThumbnail(result.compressed.blob, 400)

      // 3. Mejorar con ESPCN si se solicita
      // if (enhanceWithESPCN) {
      //   result.enhanced = await this.enhanceImage(result.compressed.dataUrl)
      // }

      // Guardar el nivel de compresión resuelto en el resultado
      result.resolvedCompressionLevel = actualCompressionLevel
      result.wasAutoResolved = compressionLevel === 'auto'

      console.log("✅ Procesamiento completo finalizado")
      return result
    } catch (error) {
      console.error("Error en procesamiento completo:", error)
      throw error
    }
  }

  /**
   * Funciones auxiliares
   */
  loadImageFromFile(file) {
    return new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = reject
      img.src = URL.createObjectURL(file)
    })
  }

  loadImageFromDataUrl(dataUrl) {
    return new Promise((resolve, reject) => {
      const img = new Image()
      img.onload = () => resolve(img)
      img.onerror = reject
      img.src = dataUrl
    })
  }

  async dataUrlToBlob(dataUrl) {
    const response = await fetch(dataUrl)
    return response.blob()
  }

  async resizeImage(file, width, height) {
    const img = await this.loadImageFromFile(file)

    this.canvas.width = width
    this.canvas.height = height
    this.ctx.drawImage(img, 0, 0, width, height)

    const dataUrl = this.canvas.toDataURL("image/jpeg", 0.95)
    const blob = await this.dataUrlToBlob(dataUrl)

    return { blob, dataUrl }
  }

  async createThumbnail(imageBlob, size) {
    const img = await this.loadImageFromFile(imageBlob)

    // Crear thumbnail cuadrado
    const minDim = Math.min(img.width, img.height)
    const startX = (img.width - minDim) / 2
    const startY = (img.height - minDim) / 2

    this.canvas.width = size
    this.canvas.height = size

    this.ctx.drawImage(img, startX, startY, minDim, minDim, 0, 0, size, size)

    const dataUrl = this.canvas.toDataURL("image/jpeg", 0.85)
    const blob = await this.dataUrlToBlob(dataUrl)

    return { blob, dataUrl, size }
  }

  /**
   * Verificar disponibilidad de modelos
   */
  async checkModelAvailability() {
    const availability = {
      autoencoders: {},
      espcn: false,
      onnxSupported: typeof ort !== "undefined",
    }

    if (!availability.onnxSupported) {
      console.warn("ONNX.js no está disponible")
      return availability
    }

    // Verificar autoencoders
    for (const level of [8, 16, 32]) {
      try {
        const response = await fetch(`/static/models/autoencoder_b${level}.onnx`, { method: "HEAD" })
        availability.autoencoders[level] = response.ok
      } catch {
        availability.autoencoders[level] = false
      }
    }

    // Verificar ESPCN
    try {
      const response = await fetch("/static/models/espcn_model.onnx", { method: "HEAD" })
      availability.espcn = response.ok
    } catch {
      availability.espcn = false
    }

    console.log("📊 Disponibilidad de modelos:", availability)
    return availability
  }
}

// Crear instancia global
const onnxProcessor = new ONNXImageProcessor()

// Exportar para uso global
window.ONNXImageProcessor = ONNXImageProcessor
window.onnxProcessor = onnxProcessor

console.log("🧠 Procesador ONNX cargado")
