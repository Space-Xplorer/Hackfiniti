import { useEffect, useRef } from 'react'

const MATRIX_WIDTH = 64
const MATRIX_HEIGHT = 32

function buildPointCloud() {
  const points = []

  for (let row = 0; row < MATRIX_HEIGHT; row += 1) {
    for (let col = 0; col < MATRIX_WIDTH; col += 1) {
      const u = col / (MATRIX_WIDTH - 1)
      const v = row / (MATRIX_HEIGHT - 1)
      const lon = (u - 0.5) * Math.PI * 2
      const lat = (0.5 - v) * Math.PI

      const continentMask =
        Math.abs(Math.sin(lon * 1.6) * Math.cos(lat * 2.4)) +
        0.55 * Math.abs(Math.sin((lon + lat) * 2.1))

      if (continentMask < 0.82) {
        continue
      }

      points.push({
        x: Math.cos(lat) * Math.cos(lon),
        y: Math.sin(lat),
        z: Math.cos(lat) * Math.sin(lon),
        brightness: Math.min(1, continentMask - 0.68),
      })
    }
  }

  return points
}

export default function AsciiGlobeCanvas() {
  const canvasRef = useRef(null)
  const mouseTargetRef = useRef({ x: 0, y: 0 })
  const mouseLerpRef = useRef({ x: 0, y: 0 })

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) {
      return undefined
    }

    const ctx = canvas.getContext('2d', { alpha: true })
    if (!ctx) {
      return undefined
    }

    const points = buildPointCloud()
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

    const handleMove = (event) => {
      const rect = canvas.getBoundingClientRect()
      const x = (event.clientX - rect.left) / rect.width
      const y = (event.clientY - rect.top) / rect.height
      mouseTargetRef.current = {
        x: (x - 0.5) * 2,
        y: (y - 0.5) * 2,
      }
    }

    const handleLeave = () => {
      mouseTargetRef.current = { x: 0, y: 0 }
    }

    const drawFrame = () => {
      rotation += 0.0075

      const lerpPoint = mouseLerpRef.current
      const targetPoint = mouseTargetRef.current
      lerpPoint.x += (targetPoint.x - lerpPoint.x) * 0.06
      lerpPoint.y += (targetPoint.y - lerpPoint.y) * 0.06

      ctx.clearRect(0, 0, width, height)
      ctx.fillStyle = 'rgba(4, 34, 31, 0.16)'
      ctx.fillRect(0, 0, width, height)

      const radius = Math.min(width, height) * 0.35
      const centerX = width * 0.5
      const centerY = height * 0.54
      const cos = Math.cos(rotation)
      const sin = Math.sin(rotation)
      const asciiScale = '.,-:=+*#%@'

      points.forEach((point) => {
        const rx = point.x * cos - point.z * sin
        const rz = point.x * sin + point.z * cos
        const ry = point.y

        if (rz < -0.36) {
          return
        }

        const depth = 1.65 / (2.35 - rz)
        const px = centerX + (rx + lerpPoint.x * 0.24) * radius * depth
        const py = centerY + (ry + lerpPoint.y * 0.2) * radius * depth

        const depthNorm = Math.max(0, Math.min(1, (rz + 1) / 2))
        const alpha = Math.max(0.18, depthNorm * 0.75 * point.brightness)
        const shade = Math.round(200 + depthNorm * 55)
        const charIndex = Math.min(asciiScale.length - 1, Math.floor(depthNorm * asciiScale.length))

        ctx.fillStyle = `rgba(${shade}, 242, 198, ${alpha})`
        ctx.fillText(asciiScale[charIndex], px, py)
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
  }, [])

  return <canvas ref={canvasRef} className="h-[440px] w-full rounded-[2rem] border border-white/10 bg-[#04221f]/40 shadow-2xl shadow-[#005b52]/30" />
}
