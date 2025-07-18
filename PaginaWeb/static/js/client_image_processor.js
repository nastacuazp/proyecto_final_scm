/**
 * Procesador de imágenes del lado del cliente
 * Dyzen - Sistema de compresión adaptativa
 */

class ClientImageProcessor {
  constructor() {
    this.canvas = document.createElement("canvas")
    this.ctx = this.canvas.getContext("2d")
    this.isProcessing = false
  }

  /**
   * Comprimir imagen usando Canvas API
   */
  async compressImage(file, compressionLevel = 16, targetSize = { width: 1024, height: 768 }) {
    return new Promise((resolve, reject) => {
      if (this.isProcessing) {
        reject(new Error("Ya hay una compresión en proceso"))
        return
      }

      this.isProcessing = true
      const img = new Image()

      img.onload = () => {
        try {
          // Configurar canvas
          this.canvas.width = targetSize.width
          this.canvas.height = targetSize.height

          // Limpiar canvas
          this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height)

          // Dibujar imagen redimensionada
          this.ctx.drawImage(img, 0, 0, targetSize.width, targetSize.height)

          // Aplicar compresión según el nivel
          const quality = this.getQualityFromLevel(compressionLevel)

          // Convertir a blob
          this.canvas.toBlob(
            (blob) => {
              if (blob) {
                this.isProcessing = false
                resolve({
                  blob: blob,
                  dataUrl: this.canvas.toDataURL("image/jpeg", quality),
                  originalSize: file.size,
                  compressedSize: blob.size,
                  compressionRatio: (((file.size - blob.size) / file.size) * 100).toFixed(1),
                  quality: quality,
                })
              } else {
                this.isProcessing = false
                reject(new Error("Error al comprimir imagen"))
              }
            },
            "image/jpeg",
            quality,
          )
        } catch (error) {
          this.isProcessing = false
          reject(error)
        }
      }

      img.onerror = () => {
        this.isProcessing = false
        reject(new Error("Error al cargar imagen"))
      }

      img.src = URL.createObjectURL(file)
    })
  }

  /**
   * Recortar imagen al centro para hacerla cuadrada
   */
  async cropToSquare(file, size = 400) {
    return new Promise((resolve, reject) => {
      const img = new Image()

      img.onload = () => {
        try {
          // Determinar el lado más corto
          const minDimension = Math.min(img.width, img.height)

          // Calcular coordenadas para recortar desde el centro
          const startX = (img.width - minDimension) / 2
          const startY = (img.height - minDimension) / 2

          // Configurar canvas para imagen cuadrada
          this.canvas.width = size
          this.canvas.height = size

          // Limpiar canvas
          this.ctx.clearRect(0, 0, size, size)

          // Dibujar la parte central de la imagen
          this.ctx.drawImage(
            img,
            startX,
            startY,
            minDimension,
            minDimension, // Área de origen
            0,
            0,
            size,
            size, // Área de destino
          )

          // Convertir a blob
          this.canvas.toBlob(
            (blob) => {
              if (blob) {
                resolve({
                  blob: blob,
                  dataUrl: this.canvas.toDataURL("image/jpeg", 0.9),
                  size: size,
                })
              } else {
                reject(new Error("Error al recortar imagen"))
              }
            },
            "image/jpeg",
            0.9,
          )
        } catch (error) {
          reject(error)
        }
      }

      img.onerror = () => reject(new Error("Error al cargar imagen"))
      img.src = URL.createObjectURL(file)
    })
  }

  /**
   * Aplicar filtros de mejora básicos
   */
  // async enhanceImage(imageData, filters = {}) {
  //   return new Promise((resolve, reject) => {
  //     try {
  //       const { brightness = 1.0, contrast = 1.0, saturation = 1.0, sharpness = 0.0 } = filters

  //       const img = new Image()

  //       img.onload = () => {
  //         // Configurar canvas
  //         this.canvas.width = img.width
  //         this.canvas.height = img.height

  //         // Aplicar filtros CSS
  //         this.ctx.filter = `
  //           brightness(${brightness}) 
  //           contrast(${contrast}) 
  //           saturate(${saturation})
  //         `

  //         // Dibujar imagen con filtros
  //         this.ctx.drawImage(img, 0, 0)

  //         // Aplicar nitidez si se especifica
  //         if (sharpness > 0) {
  //           this.applySharpenFilter(sharpness)
  //         }

  //         // Convertir a blob
  //         this.canvas.toBlob(
  //           (blob) => {
  //             if (blob) {
  //               resolve({
  //                 blob: blob,
  //                 dataUrl: this.canvas.toDataURL("image/jpeg", 0.95),
  //               })
  //             } else {
  //               reject(new Error("Error al mejorar imagen"))
  //             }
  //           },
  //           "image/jpeg",
  //           0.95,
  //         )
  //       }

  //       img.onerror = () => reject(new Error("Error al cargar imagen"))

  //       if (typeof imageData === "string") {
  //         img.src = imageData
  //       } else {
  //         img.src = URL.createObjectURL(imageData)
  //       }
  //     } catch (error) {
  //       reject(error)
  //     }
  //   })
  // }

  /**
   * Aplicar filtro de nitidez usando convolución
   */
  // applySharpenFilter(intensity = 0.5) {
  //   const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height)
  //   const data = imageData.data
  //   const width = this.canvas.width
  //   const height = this.canvas.height

  //   // Kernel de nitidez
  //   const kernel = [0, -intensity, 0, -intensity, 1 + 4 * intensity, -intensity, 0, -intensity, 0]

  //   const output = new Uint8ClampedArray(data.length)

  //   for (let y = 1; y < height - 1; y++) {
  //     for (let x = 1; x < width - 1; x++) {
  //       for (let c = 0; c < 3; c++) {
  //         // RGB channels
  //         let sum = 0
  //         for (let ky = -1; ky <= 1; ky++) {
  //           for (let kx = -1; kx <= 1; kx++) {
  //             const idx = ((y + ky) * width + (x + kx)) * 4 + c
  //             const kernelIdx = (ky + 1) * 3 + (kx + 1)
  //             sum += data[idx] * kernel[kernelIdx]
  //           }
  //         }
  //         const outputIdx = (y * width + x) * 4 + c
  //         output[outputIdx] = Math.max(0, Math.min(255, sum))
  //       }
  //       // Copiar canal alpha
  //       const alphaIdx = (y * width + x) * 4 + 3
  //       output[alphaIdx] = data[alphaIdx]
  //     }
  //   }

  //   // Aplicar resultado
  //   const newImageData = new ImageData(output, width, height)
  //   this.ctx.putImageData(newImageData, 0, 0)
  // }

  /**
   * Mapear nivel de compresión a calidad JPEG
   */
  getQualityFromLevel(compressionLevel) {
    const qualityMap = {
      8: 0.3, // Alta compresión, baja calidad
      16: 0.6, // Compresión media
      32: 0.85, // Baja compresión, alta calidad
      0: 0.95, // Sin compresión
    }
    return qualityMap[compressionLevel] || 0.6
  }

  /**
   * Procesar imagen completa: recortar, comprimir y crear miniatura
   */
  async processImageComplete(file, compressionLevel = 16) {
    try {
      console.log("Iniciando procesamiento completo de imagen...")

      // 1. Crear versión cuadrada (thumbnail)
      const square = await this.cropToSquare(file, 400)
      console.log("Imagen recortada a cuadrado")

      // 2. Comprimir imagen original
      const compressed = await this.compressImage(file, compressionLevel)
      console.log("Imagen comprimida")

      // 3. Comprimir thumbnail
      const thumbnailCompressed = await this.compressImage(square.blob, compressionLevel, { width: 400, height: 400 })
      console.log("Thumbnail comprimido")

      return {
        original: {
          file: file,
          size: file.size,
        },
        compressed: {
          blob: compressed.blob,
          dataUrl: compressed.dataUrl,
          size: compressed.compressedSize,
          quality: compressed.quality,
          compressionRatio: compressed.compressionRatio,
        },
        thumbnail: {
          blob: thumbnailCompressed.blob,
          dataUrl: thumbnailCompressed.dataUrl,
          size: thumbnailCompressed.compressedSize,
        },
        square: {
          blob: square.blob,
          dataUrl: square.dataUrl,
          size: square.blob.size,
        },
      }
    } catch (error) {
      console.error("Error en procesamiento completo:", error)
      throw error
    }
  }
}

// Crear instancia global
const clientImageProcessor = new ClientImageProcessor()

// Exportar para uso global
window.ClientImageProcessor = ClientImageProcessor
window.imageProcessor = clientImageProcessor

console.log("🖼️ Procesador de imágenes del cliente cargado")
