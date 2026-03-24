import { useEffect, useRef, useCallback, useMemo } from 'react'

// Canvas rendering constants
const MATRIX_WIDTH = 64
const MATRIX_HEIGHT = 32
const ROTATION_SPEED = 0.0075
const LERP_FACTOR = 0.06
const RADIUS_SCALE = 0.35
const CENTER_Y_OFFSET = 0.54
const MOUSE_X_INFLUENCE = 0.24
const MOUSE_Y_INFLUENCE = 0.2
const DEPTH_CULLING = -0.36
const DEPTH_SCALE = 1.65
const DEPTH_MAX = 2.35
const MIN_ALPHA = 0.16
const ALPHA_DEPTH_FACTOR = 0.52
const ASCII_SCALE = '.,-:=+*#%@'
const CONTINENT_THRESHOLD = 0.82
const CONTINENT_BRIGHTNESS_OFFSET = 0.68

// Memoized function to build point cloud only once per component lifetime
function buildPointCloud() {
  const points = []

  for (let row = 0; row < MATRIX_HEIGHT; row += 1) {
    for (let col = 0; col < MATRIX_WIDTH; col += 1) {
      const u = col / (MATRIX_WIDTH - 1)
      const v = row / (MATRIX_HEIGHT - 1)
      const lon = (u - 0.5) * Math.PI * 2
      const lat = (0.5 - v) * Math.PI

      // Continent mask using sine/cosine noise
      const continentMask =
        Math.abs(Math.sin(lon * 1.6) * Math.cos(lat * 2.4)) +
        0.55 * Math.abs(Math.sin((lon + lat) * 2.1))

      if (continentMask < CONTINENT_THRESHOLD) {
        continue
      }

      points.push({
        x: Math.cos(lat) * Math.cos(lon),
        y: Math.sin(lat),
        z: Math.cos(lat) * Math.sin(lon),
        brightness: Math.min(1, continentMask - CONTINENT_BRIGHTNESS_OFFSET),
      })
    }
  }

  return points
}

export default function AsciiGlobeCanvas({ 
  isBackground = false,
  baseColor = { r: 4, g: 90, b: 74 },
  accentColor = { r: 0, g: 91, b: 82 },
} = {}) {
  const canvasRef = useRef(null)
  const mouseTargetRef = useRef({ x: 0, y: 0 })
  const mouseLerpRef = useRef({ x: 0, y: 0 })
  
  // Memoize point cloud so it's only built once
  const points = useMemo(() => buildPointCloud(), [])

  // Create memoized event handlers
  const handleMove = useCallback((event) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = (event.clientX - rect.left) / rect.width
    const y = (event.clientY - rect.top) / rect.height
    mouseTargetRef.current = {
      x: (x - 0.5) * 2,
      y: (y - 0.5) * 2,
    }
  }, [])

  const handleLeave = useCallback(() => {
    mouseTargetRef.current = { x: 0, y: 0 }
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) {
      return undefined
    }

    const ctx = canvas.getContext('2d', { alpha: true })
    if (!ctx) {
      return undefined
    }

    let width = 0
    let height = 0
    let rafId = 0
    let rotation = 0

    const resize = () => {
      const rect = canvas.getBoundingClientRect()
      const dpr = window.devicePixelRatio || 1
      width = Math.max(1, rect.width)
      height = Math.max(1, rect.height)
      canvas.width = Math.floor(width * dpr)
      canvas.height = Math.floor(height * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.font = '11px ui-monospace, SFMono-Regular, Menlo, monospace'
    }

    const drawFrame = () => {
      rotation += ROTATION_SPEED

      const lerpPoint = mouseLerpRef.current
      const targetPoint = mouseTargetRef.current
      lerpPoint.x += (targetPoint.x - lerpPoint.x) * LERP_FACTOR
      lerpPoint.y += (targetPoint.y - lerpPoint.y) * LERP_FACTOR

      ctx.clearRect(0, 0, width, height)

      const radius = Math.min(width, height) * RADIUS_SCALE
      const centerX = width * 0.5
      const centerY = height * CENTER_Y_OFFSET
      const cos = Math.cos(rotation)
      const sin = Math.sin(rotation)

      // Render each point of the globe
      points.forEach((point) => {
        // 3D rotation around Y axis
        const rx = point.x * cos - point.z * sin
        const rz = point.x * sin + point.z * cos
        const ry = point.y

        // Cull back-facing points
        if (rz < DEPTH_CULLING) {
          return
        }

        // Perspective projection
        const depth = DEPTH_SCALE / (DEPTH_MAX - rz)
        const px = centerX + (rx + lerpPoint.x * MOUSE_X_INFLUENCE) * radius * depth
        const py = centerY + (ry + lerpPoint.y * MOUSE_Y_INFLUENCE) * radius * depth

        // Calculate visual properties based on depth
        const depthNorm = Math.max(0, Math.min(1, (rz + 1) / 2))
        const alpha = Math.max(MIN_ALPHA, depthNorm * ALPHA_DEPTH_FACTOR * point.brightness)
        
        // Interpolate colors based on depth for gradient effect
        const green = Math.round(baseColor.g + depthNorm * (accentColor.g - baseColor.g))
        const blue = Math.round(baseColor.b + depthNorm * (accentColor.b - baseColor.b))
        
        const charIndex = Math.min(ASCII_SCALE.length - 1, Math.floor(depthNorm * ASCII_SCALE.length))

        // Render ASCII character
        ctx.fillStyle = `rgba(${baseColor.r}, ${green}, ${blue}, ${alpha})`
        ctx.fillText(ASCII_SCALE[charIndex], px, py)
      })

      rafId = window.requestAnimationFrame(drawFrame)
    }

    resize()
    drawFrame()

    window.addEventListener('resize', resize)
    canvas.addEventListener('mousemove', handleMove)
    canvas.addEventListener('mouseleave', handleLeave)

    return () => {
      window.removeEventListener('resize', resize)
      canvas.removeEventListener('mousemove', handleMove)
      canvas.removeEventListener('mouseleave', handleLeave)
      window.cancelAnimationFrame(rafId)
    }
  }, [points, handleMove, handleLeave, baseColor, accentColor])

  return (
    <canvas
      ref={canvasRef}
      className={
        isBackground
          ? 'h-full w-full'
          : 'h-[440px] w-full rounded-[2rem] border border-[#04221f]/10 bg-white/80 shadow-2xl shadow-[#005b52]/20'
      }
    />
  )
}
