/**
 * Generates PNG icons from public/icons/icon.svg.
 * Run once: node generate-icons.mjs
 * Requires: npm install -D sharp
 */
import sharp from 'sharp'
import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dir = dirname(fileURLToPath(import.meta.url))
const svgPath = resolve(__dir, 'public/icons/icon.svg')
const svg = readFileSync(svgPath)

const sizes = [16, 32, 64, 144, 180, 192, 512]

for (const size of sizes) {
  const name = size === 180 ? 'apple-touch-icon' : `icon-${size}x${size}`
  const out = resolve(__dir, `public/icons/${name}.png`)
  await sharp(svg).resize(size, size).png().toFile(out)
  console.log(`✓ ${name}.png (${size}×${size})`)
}

console.log('\nAll icons generated. Also copy icon-32x32.png → favicon.ico manually if needed.')
