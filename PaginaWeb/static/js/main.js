// Variables globales
let networkConditions = {
  bandwidth: 0,
  latency: 0,
  quality: "unknown",
  compression: 16,
}

// Inicialización
document.addEventListener("DOMContentLoaded", () => {
  // La primera actualización se hará desde NetworkSpeedTest
  // pero mantenemos esta función para compatibilidad
  updateNetworkStats()
})

// Actualizar estadísticas de red desde el servidor
async function updateNetworkStats() {
  try {
    const response = await fetch("/api/network")
    const data = await response.json()

    networkConditions = data

    // Actualizar UI
    updateNetworkUI(data)
  } catch (error) {
    console.error("Error actualizando estadísticas de red:", error)
  }
}

// Actualizar interfaz de red
function updateNetworkUI(conditions) {
  const indicator = document.getElementById("networkIndicator")
  const text = document.getElementById("networkText")
  const compressionLevel = document.getElementById("compressionLevel")
  const networkStatus = document.getElementById("networkStatus")

  if (!indicator || !text || !compressionLevel) return

  // Actualizar indicador
  const qualityIcons = {
    good: "fas fa-wifi",
    medium: "fas fa-wifi",
    poor: "fas fa-wifi-slash",
  }

  const qualityColors = {
    good: "#46d160",
    medium: "#ffd635",
    poor: "#ff4500",
  }

  indicator.innerHTML = `<i class="${qualityIcons[conditions.quality]}"></i>`
  indicator.style.color = qualityColors[conditions.quality]

  // Actualizar texto
  text.textContent = `Red ${conditions.quality} - ${conditions.bandwidth.toFixed(1)} Mbps, ${conditions.latency.toFixed(0)}ms`

  // Actualizar nivel de compresión
  compressionLevel.textContent = conditions.compression

  // Actualizar color de fondo de la barra
  networkStatus.style.background = `linear-gradient(135deg, ${qualityColors[conditions.quality]}, ${qualityColors[conditions.quality]}dd)`

  // Actualizar sidebar si existe
  updateSidebarStats(conditions)
}

// Actualizar estadísticas del sidebar
function updateSidebarStats(conditions) {
  const bandwidthValue = document.getElementById("bandwidthValue")
  const latencyValue = document.getElementById("latencyValue")
  const qualityValue = document.getElementById("qualityValue")

  if (bandwidthValue) bandwidthValue.textContent = `${conditions.bandwidth.toFixed(1)} Mbps`
  if (latencyValue) latencyValue.textContent = `${conditions.latency.toFixed(0)} ms`
  if (qualityValue) {
    qualityValue.textContent = conditions.quality.charAt(0).toUpperCase() + conditions.quality.slice(1)
    qualityValue.className = `stat-value quality-${conditions.quality}`
  }
}

// Sistema de votación
async function vote(postId, voteType, itemType, commentId = null) {
  try {
    const response = await fetch("/api/vote", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        post_id: postId,
        comment_id: commentId,
        vote_type: voteType,
      }),
    })

    const data = await response.json()

    if (response.ok) {
      // Actualizar contadores en la UI
      updateVoteUI(postId, commentId, data.upvotes, data.downvotes)

      // Feedback visual
      showVoteFeedback(voteType)
    }
  } catch (error) {
    console.error("Error al votar:", error)
    showNotification("Error al procesar voto", "error")
  }
}

// Actualizar UI de votos
function updateVoteUI(postId, commentId, upvotes, downvotes) {
  let container

  if (commentId) {
    container = document.querySelector(`[data-comment-id="${commentId}"]`)
  } else {
    container = document.querySelector(`[data-post-id="${postId}"]`)
  }

  if (container) {
    const upvoteCount = container.querySelector(".upvote-count")
    const downvoteCount = container.querySelector(".downvote-count")

    if (upvoteCount) upvoteCount.textContent = upvotes
    if (downvoteCount) downvoteCount.textContent = downvotes
  }
}

// Feedback visual para votos
function showVoteFeedback(voteType) {
  const color = voteType === "up" ? "#ff8b60" : "#9494ff"
  const icon = voteType === "up" ? "↑" : "↓"

  // Crear elemento de feedback
  const feedback = document.createElement("div")
  feedback.textContent = icon
  feedback.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: ${color};
        color: white;
        padding: 10px 15px;
        border-radius: 50%;
        font-size: 20px;
        font-weight: bold;
        z-index: 1000;
        pointer-events: none;
        animation: voteAnimation 0.6s ease-out;
    `

  // Agregar animación CSS si no existe
  if (!document.getElementById("vote-animation-style")) {
    const style = document.createElement("style")
    style.id = "vote-animation-style"
    style.textContent = `
            @keyframes voteAnimation {
                0% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
                50% { opacity: 1; transform: translate(-50%, -50%) scale(1.5); }
                100% { opacity: 0; transform: translate(-50%, -50%) scale(1); }
            }
        `
    document.head.appendChild(style)
  }

  document.body.appendChild(feedback)

  // Remover después de la animación
  setTimeout(() => {
    if (feedback.parentNode) {
      feedback.parentNode.removeChild(feedback)
    }
  }, 600)
}

// Sistema de notificaciones
function showNotification(message, type = "info") {
  const notification = document.createElement("div")
  notification.className = `notification notification-${type}`
  notification.textContent = message

  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `

  // Colores según tipo
  const colors = {
    success: "#46d160",
    error: "#ff4500",
    warning: "#ffd635",
    info: "#0079d3",
  }

  notification.style.background = colors[type] || colors.info

  document.body.appendChild(notification)

  // Animar entrada
  setTimeout(() => {
    notification.style.transform = "translateX(0)"
  }, 100)

  // Remover después de 3 segundos
  setTimeout(() => {
    notification.style.transform = "translateX(100%)"
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification)
      }
    }, 300)
  }, 3000)
}

// Formatear tamaño de archivo
function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

// Formatear tiempo relativo
function formatTimeAgo(dateString) {
  const now = new Date()
  const date = new Date(dateString)
  const diffInSeconds = Math.floor((now - date) / 1000)

  if (diffInSeconds < 60) return "hace un momento"
  if (diffInSeconds < 3600) return `hace ${Math.floor(diffInSeconds / 60)} minutos`
  if (diffInSeconds < 86400) return `hace ${Math.floor(diffInSeconds / 3600)} horas`
  if (diffInSeconds < 2592000) return `hace ${Math.floor(diffInSeconds / 86400)} días`

  return date.toLocaleDateString()
}

// Lazy loading para imágenes
function initLazyLoading() {
  const images = document.querySelectorAll('img[loading="lazy"]')

  if ("IntersectionObserver" in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const img = entry.target
          img.src = img.dataset.src || img.src
          img.classList.remove("lazy")
          imageObserver.unobserve(img)
        }
      })
    })

    images.forEach((img) => imageObserver.observe(img))
  }
}

// Inicializar funciones cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
  initLazyLoading()

  // Actualizar timestamps cada minuto
  setInterval(() => {
    const timestamps = document.querySelectorAll(".timestamp")
    timestamps.forEach((timestamp) => {
      const dateString = timestamp.dataset.date || timestamp.textContent
      timestamp.textContent = formatTimeAgo(dateString)
    })
  }, 60000)
})

// Funciones de utilidad para debugging
window.DyzenDebug = {
  getCurrentNetwork: () => networkConditions,
  showNotification: showNotification,
  formatFileSize: formatFileSize,
  runSpeedTest: () => {
    if (window.NetworkSpeedTest) {
      window.NetworkSpeedTest.runTest()
      return "Ejecutando prueba de velocidad..."
    }
    return "Sistema de pruebas no disponible"
  },
}
