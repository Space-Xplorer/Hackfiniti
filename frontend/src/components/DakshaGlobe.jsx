import { useEffect, useRef } from 'react'

const WORLD_MAP = [
  '0000000000000000000000000000000000000000000000000000000000000000',
  '0000000000000000000000000000000000000000000000000000000000000000',
  '0000000111111100000000000011111111111100000000000000000000000000',
  '0000011111111111000000000111111111111111100000000000000000000000',
  '0000111111111111100000001111111111111111110000000000000000000000',
  '0000011111111111000000000111111111111111111000000000000000000000',
  '0000001111111100000000000011111111111111111100000000000000000000',
  '0000000111111000000000000001111111111111111100000000000000000000',
  '0000000011100000000000000000111111111111111000000001110000000000',
  '0000000011100000000000000000011111111111100000000011111000000000',
  '0000000001100000000000000000001111111110000000000011100000000000',
  '0000000001100000000000000000000111111000000000000011100000000000',
  '0000000000100000000000000000000011100000000000000000000000000000',
  '0000000000100000000000000000000001000000000000000000000000000000',
  '0000000000000000000000000000000000000000000000000000000000000000',
  '0000000000000000000000000000000000000000000000000000000000000000',
]

export default function DakshaGlobe() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let width = canvas.clientWidth || window.innerWidth
    let height = canvas.clientHeight || Math.round(window.innerHeight * 0.8)
    canvas.width = width
    canvas.height = height

    const dpr = window.devicePixelRatio || 1
    canvas.width = Math.floor(width * dpr)
    canvas.height = Math.floor(height * dpr)
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    const points = []
    const latLines = 50
    const lonLines = 100
    const sphereRadius = width < 768 ? width * 0.6 : width * 0.4
    const focalLength = 1500
    const zOffset = 2200

    for (let i = 0; i <= latLines; i++) {
      const theta = (i / latLines) * Math.PI
      const mapRowIndex = Math.min(WORLD_MAP.length - 1, Math.floor((i / latLines) * (WORLD_MAP.length - 1)))

      for (let j = 0; j <= lonLines; j++) {
        const phi = (j / lonLines) * Math.PI * 2
        const row = WORLD_MAP[mapRowIndex] || ''
        const mapColIndex = row.length > 0
          ? Math.min(row.length - 1, Math.floor((j / lonLines) * (row.length - 1)))
          : 0

        const isLand = row[mapColIndex] === '1'
        const isNode = isLand && Math.random() > 0.95

        const x = sphereRadius * Math.sin(theta) * Math.cos(phi)
        const y = sphereRadius * Math.sin(theta) * Math.sin(phi)
        const z = sphereRadius * Math.cos(theta)

        points.push({ x, y, z, isLand, isNode })
      }
    }

    let globalRotation = 0
    let mouseOffsetX = 0
    let mouseOffsetY = 0
    let currentOffsetX = 0
    let currentOffsetY = 0
    let rafId = 0

    const handleMouseMove = (e) => {
      mouseOffsetX = ((e.clientX / window.innerWidth) - 0.5) * Math.PI * 0.65
      mouseOffsetY = ((e.clientY / window.innerHeight) - 0.5) * 0.12
    }

    const handleResize = () => {
      width = canvas.clientWidth || window.innerWidth
      height = canvas.clientHeight || Math.round(window.innerHeight * 0.8)
      canvas.width = Math.floor(width * dpr)
      canvas.height = Math.floor(height * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('resize', handleResize)

    const animate = () => {
      ctx.clearRect(0, 0, width, height)

      globalRotation -= 0.002

      currentOffsetX += (mouseOffsetX - currentOffsetX) * 0.05
      currentOffsetY += (mouseOffsetY - currentOffsetY) * 0.05

      const finalAngleY = globalRotation + currentOffsetX
      const finalAngleX = 0.05 + currentOffsetY
      const finalAngleZ = currentOffsetX * 0.05

      const cosY = Math.cos(finalAngleY)
      const sinY = Math.sin(finalAngleY)
      const cosX = Math.cos(finalAngleX)
      const sinX = Math.sin(finalAngleX)
      const cosZ = Math.cos(finalAngleZ)
      const sinZ = Math.sin(finalAngleZ)
      const halfWidth = width / 2

      for (let i = 0; i < points.length; i++) {
        const point = points[i]

        let rot1X = point.x * cosY - point.z * sinY
        let rot1Z = point.x * sinY + point.z * cosY
        let rot1Y = point.y

        const rot2Y = rot1Y * cosX - rot1Z * sinX
        const rot2Z = rot1Y * sinX + rot1Z * cosX
        const rot2X = rot1X

        const finalX = rot2X * cosZ - rot2Y * sinZ
        const finalY = rot2X * sinZ + rot2Y * cosZ
        const finalZ = rot2Z

        if (finalZ < 0) {
          const scale = focalLength / (zOffset + finalZ)
          const px = halfWidth + finalX * scale
          const py = height + finalY * scale

          if (py < height && py > 0 && px > 0 && px < width) {
            if (point.isNode) {
              ctx.beginPath()
              ctx.fillStyle = `rgba(0, 91, 82, ${Math.min(0.95, 0.8 + scale * 0.2)})`
              ctx.arc(px, py, Math.max(1, 4 * scale), 0, Math.PI * 2)
              ctx.fill()
            } else {
              ctx.font = `bold ${Math.max(6, 14 * scale)}px monospace`
              ctx.textAlign = 'center'
              ctx.textBaseline = 'middle'

              if (point.isLand) {
                ctx.fillStyle = `rgba(0, 91, 82, ${Math.min(1, 0.5 + scale * 0.5)})`
                ctx.fillText('#', px, py)
              } else {
                ctx.fillStyle = `rgba(0, 91, 82, ${Math.min(0.3, 0.05 + scale * 0.1)})`
                ctx.fillText('#', px, py)
              }
            }
          }
        }
      }

      rafId = requestAnimationFrame(animate)
    }

    rafId = requestAnimationFrame(animate)

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('resize', handleResize)
      cancelAnimationFrame(rafId)
    }
  }, [])

  return (
    <div className="relative w-full h-[72vh] md:h-[78vh] opacity-90">
      <canvas ref={canvasRef} className="w-full h-full" />
    </div>
  )
}
