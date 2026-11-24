// 下载 14 个 Lean 压缩包分片。串行，避免被服务器限速。
import fs from "node:fs"
import path from "node:path"

import { fileURLToPath } from "node:url"
const dir = path.dirname(fileURLToPath(import.meta.url))
fs.mkdirSync(dir, { recursive: true })

const N = 14
const t0 = Date.now()
let total = 0

for (let i = 1; i <= N; i++) {
  const name = `lean.tar.gz.part${String(i).padStart(2, "0")}`
  const out = path.join(dir, name)

  if (fs.existsSync(out) && fs.statSync(out).size === 18_000_000) {
    console.log(`[${i}/${N}] ${name} 已存在，跳过`)
    total += 18_000_000
    continue
  }

  const ts = Date.now()
  const r = await fetch(`https://alpo.ge/${name}`, {
    headers: { "User-Agent": "Mozilla/5.0" },
  })
  if (!r.ok) {
    console.log(`[${i}/${N}] ${name} HTTP ${r.status}，停`)
    break
  }

  const ws = fs.createWriteStream(out)
  let got = 0
  for await (const chunk of r.body) {
    ws.write(chunk)
    got += chunk.length
  }
  ws.end()
  await new Promise((res) => ws.on("finish", res))

  total += got
  const sec = (Date.now() - ts) / 1000
  const elapsed = (Date.now() - t0) / 1000
  console.log(
    `[${i}/${N}] ${name} ${(got / 1048576).toFixed(1)} MB  ${sec.toFixed(1)}s  ` +
      `累计 ${(total / 1048576).toFixed(0)} MB / ${(elapsed / 60).toFixed(1)} 分钟`,
  )
}

console.log(`\n完成：${(total / 1048576).toFixed(1)} MB，用时 ${((Date.now() - t0) / 60000).toFixed(1)} 分钟`)
