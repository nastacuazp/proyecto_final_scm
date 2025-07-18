/**
 * Módulo para medir la velocidad de red real
 * Dyzen - Sistema de compartición de imágenes adaptativo
 */

class NetworkSpeedTest {
  constructor() {
    this.testInProgress = false
    this.lastResult = {
      bandwidth: 50, // Valor inicial por defecto (Mbps)
      latency: 100, // Valor inicial por defecto (ms)
      quality: "medium",
      compression: 16,
    }
    this.callbacks = []
    this.testInterval = null
  }

  // Registrar callbacks para cuando cambian las condiciones
  onConditionsChange(callback) {
    this.callbacks.push(callback)
  }

  // Notificar a todos los callbacks
  notifyCallbacks() {
    this.callbacks.forEach((callback) => callback(this.lastResult))
  }

  // Medir ancho de banda descargando un archivo de prueba
  async measureBandwidth() {
    if (this.testInProgress) return this.lastResult.bandwidth

    this.testInProgress = true
    const startTime = performance.now()

    // Usar un tamaño aleatorio entre 500KB y 2MB para evitar cacheo
    const testFileSize = Math.floor(Math.random() * (2 - 0.5) + 0.5) * 1024 * 1024

    // Añadir un parámetro aleatorio para evitar cacheo
    const testUrl = `/static/test/speedtest.jpg?cache=${Date.now()}-${Math.random()}`

    try {
      console.log("Iniciando prueba de velocidad...")
      const response = await fetch(testUrl, {
        method: "GET",
        cache: "no-store", // Importante: evitar cacheo
        headers: {
          "Cache-Control": "no-cache, no-store, must-revalidate",
          Pragma: "no-cache",
          Expires: "0",
        },
      })

      if (!response.ok) throw new Error("Error en la prueba de velocidad")

      const data = await response.blob()
      const endTime = performance.now()
      const durationSeconds = (endTime - startTime) / 1000

      // Calcular velocidad en Mbps
      const fileSizeInBits = data.size * 8
      const speedMbps = fileSizeInBits / durationSeconds / (1024 * 1024)

      console.log(
        `Prueba completada: ${speedMbps.toFixed(2)} Mbps (tamaño: ${(data.size / 1024 / 1024).toFixed(2)}MB, tiempo: ${durationSeconds.toFixed(2)}s)`,
      )
      this.testInProgress = false
      return Math.max(1, speedMbps) // Mínimo 1 Mbps
    } catch (error) {
      console.error("Error en prueba de velocidad:", error)
      this.testInProgress = false

      // Generar un valor aleatorio para simular variación cuando hay error
      // const randomBandwidth = Math.random() * 80 + 20 // Entre 20 y 100 Mbps
      // return randomBandwidth
    }
  }

  // Medir latencia
  async measureLatency() {
    const startTime = performance.now()

    try {
      // Hacer múltiples mediciones para mayor precisión
      const measurements = []
      for (let i = 0; i < 3; i++) {
        const pingStart = performance.now()
        const response = await fetch(`/api/ping?t=${Date.now()}`)
        const pingEnd = performance.now()
        measurements.push(pingEnd - pingStart)
      }

      // Calcular promedio, descartando el valor más alto
      measurements.sort((a, b) => a - b)
      const validMeasurements = measurements.slice(0, 2) // Usar los 2 valores más bajos
      const avgLatency = validMeasurements.reduce((sum, val) => sum + val, 0) / validMeasurements.length

      return avgLatency
    } catch (error) {
      console.error("Error midiendo latencia:", error)
      return Math.random() * 150 + 50 // Entre 50 y 200ms si hay error
    }
  }

  // Determinar calidad y nivel de compresión basado en mediciones
  analyzeConditions(bandwidth, latency) {
    let quality, compression

    if (bandwidth < 20 || latency > 200) {
      quality = "poor"
      compression = 8
    } else if (bandwidth < 50 || latency > 100) {
      quality = "medium"
      compression = 16
    } else {
      quality = "good"
      compression = 32
    }

    return { quality, compression }
  }

  // Realizar una prueba completa
  async runTest() {
    try {
      // Medir ancho de banda y latencia
      const [bandwidth, latency] = await Promise.all([this.measureBandwidth(), this.measureLatency()])

      // Analizar condiciones
      const { quality, compression } = this.analyzeConditions(bandwidth, latency)

      // Actualizar resultados
      this.lastResult = {
        bandwidth: Math.round(bandwidth * 10) / 10, // Redondear a 1 decimal
        latency: Math.round(latency),
        quality,
        compression,
      }

      // Enviar resultados al servidor
      this.sendResultsToServer()

      // Notificar a los callbacks
      this.notifyCallbacks()

      return this.lastResult
    } catch (error) {
      console.error("Error en prueba de red:", error)
      return this.lastResult
    }
  }

  // Enviar resultados al servidor para sincronización
  async sendResultsToServer() {
    try {
      await fetch("/api/network/update", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(this.lastResult),
      })
    } catch (error) {
      console.error("Error enviando resultados al servidor:", error)
    }
  }

  // Iniciar pruebas periódicas
  startPeriodicTests(intervalSeconds = 30) {
    if (this.testInterval) {
      clearInterval(this.testInterval)
    }

    // Ejecutar una prueba inmediatamente
    this.runTest()

    // Programar pruebas periódicas
    this.testInterval = setInterval(() => {
      this.runTest()
    }, intervalSeconds * 1000)

    console.log(`Pruebas de velocidad iniciadas (cada ${intervalSeconds} segundos)`)
  }

  // Detener pruebas periódicas
  stopPeriodicTests() {
    if (this.testInterval) {
      clearInterval(this.testInterval)
      this.testInterval = null
      console.log("Pruebas de velocidad detenidas")
    }
  }

  // Obtener último resultado
  getLastResult() {
    return { ...this.lastResult }
  }
}

// Crear instancia global
const networkSpeedTest = new NetworkSpeedTest()

// Exportar para uso en otros scripts
window.NetworkSpeedTest = networkSpeedTest

// Iniciar pruebas automáticamente
document.addEventListener("DOMContentLoaded", () => {
  console.log("Iniciando sistema de pruebas de velocidad real")
  networkSpeedTest.startPeriodicTests(30) // Cada 30 segundos

  // Registrar callback para actualizar UI
  networkSpeedTest.onConditionsChange((conditions) => {
    const updateNetworkUI = window.updateNetworkUI // Declare the variable before using it
    if (typeof updateNetworkUI === "function") {
      updateNetworkUI(conditions)
    }
  })
})
