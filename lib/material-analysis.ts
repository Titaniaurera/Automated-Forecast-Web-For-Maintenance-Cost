// =====================================================
// MATERIAL ANALYSIS  (rule-based, tanpa LLM)
//
// Input : 1 baris material yang sudah ada di modal (ForecastItem)
// Output: isi 7 kartu analisis, sudah dalam bentuk bullet
//
//   1 Kondisi saat ini        5 Skenario GR terlambat
//   2 Pergerakan GI & GR      6 Risiko
//   3 Forecast GI & GR        7 Rekomendasi
//   4 Dampak terhadap stok
// =====================================================

export type Severity = "high" | "medium" | "low" | "info"

export interface AnalysisInput {
  Material?: string
  Status?: string | null
  Stock?: number | null
  Forecast_GI?: number | null
  Forecast_GR?: number | null
  Projected_Stock?: number | null
  Coverage?: number | null
  Trend_GI?: number[]
  Trend_GR?: number[]
  Trend_Date?: string[]       // label bulan GI
  Trend_Date_GR?: string[]    // opsional: label bulan GR kalau backend kirim
  Has_GI?: boolean
  Has_GR?: boolean
  Has_Stock?: boolean
  History_Count?: number | null
  // opsional (hanya ada kalau page.tsx meneruskannya)
  Low_Confidence?: boolean
  MAPE?: number | null
}

export interface MaterialAnalysis {
  overallSeverity: Severity
  complete: boolean // GI + GR + Stock tersedia

  kondisi: {
    severity: Severity
    status: string | null
    bullets: string[]
    metrics: { label: string; value: string }[]
  }
  historis: {
    gi: { title: string; bullets: string[] }
    gr: { title: string; bullets: string[] } | null
  }
  forecast: { bullets: string[] }
  stok: {
    severity: Severity
    bullets: string[]
    formula: { expr: string; result: string } | null
  }
  skenario: {
    severity: Severity
    headline: string
    bullets: string[]
    note: string
  } | null
  risiko: { severity: Severity; text: string }[]
  rekomendasi: {
    priority: string
    bullets: string[]
    warning: string | null
  }
}

const BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
  "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

const SEV_ORDER: Record<Severity, number> = {
  high: 3, medium: 2, low: 1, info: 0
}

// -----------------------------------------------------
// HELPER
// -----------------------------------------------------
function num(v: unknown): number | null {
  if (typeof v !== "number" || !Number.isFinite(v)) return null
  return v
}

function fmt(v: number | null, unit = ""): string {
  if (v === null) return "-"
  const digits = Math.abs(v) < 100 && !Number.isInteger(v) ? 1 : 0
  const s = v.toLocaleString("id-ID", { maximumFractionDigits: digits })
  return unit ? `${s} ${unit}` : s
}

function fmtBulan(s: string | null | undefined): string {
  if (!s) return "-"
  const m = /^(\d{4})-(\d{1,2})/.exec(s)
  if (!m) return s
  const idx = Number(m[2]) - 1
  return idx >= 0 && idx < 12 ? `${BULAN[idx]} ${m[1]}` : s
}

function cleanSeries(values?: number[], labels?: string[]) {
  const v: number[] = []
  const l: (string | null)[] = []
  ;(values ?? []).forEach((x, i) => {
    const n = num(x)
    if (n === null) return
    v.push(n)
    l.push(labels?.[i] ?? null)
  })
  return { v, l }
}

const mean = (a: number[]) => a.reduce((s, x) => s + x, 0) / a.length

function stdev(a: number[]) {
  const m = mean(a)
  return Math.sqrt(mean(a.map((x) => (x - m) ** 2)))
}

// -----------------------------------------------------
// POLA SERIES (GI & GR)
// -----------------------------------------------------
interface SeriesDesc {
  ok: boolean
  bullets: string[]
  cv: number
  last: number | null
  last3: number | null
  range3: [number, number] | null
  forecastPosition: "di atas" | "di bawah" | "dalam kisaran" | null
}

function describeSeries(
  values: number[] | undefined,
  labels: string[] | undefined,
  forecast: number | null,
  name: string,
  unit: string
): SeriesDesc {
  const { v, l } = cleanSeries(values, labels)

  if (v.length < 3) {
    return {
      ok: false, cv: 0, last: v[v.length - 1] ?? null, last3: null,
      range3: null, forecastPosition: null,
      bullets: [`Data historis ${name} belum cukup untuk membaca pola (${v.length} periode).`]
    }
  }

  const avg = mean(v)
  const cv = avg > 0 ? stdev(v) / avg : 0
  const iMax = v.indexOf(Math.max(...v))
  const iMin = v.indexOf(Math.min(...v))

  const first3 = mean(v.slice(0, 3))
  const tail = v.slice(-3)
  const last3 = mean(tail)
  const ratio = first3 > 0 ? last3 / first3 : null

  const arah =
    ratio === null ? "tidak dapat ditentukan"
      : ratio >= 1.3 ? "naik"
        : ratio <= 0.7 ? "turun"
          : "relatif datar"

  const volat =
    cv >= 0.6 ? "sangat fluktuatif"
      : cv >= 0.3 ? "cukup fluktuatif"
        : "relatif stabil"

  let pos: SeriesDesc["forecastPosition"] = null
  if (forecast !== null && last3 > 0) {
    const r = forecast / last3
    pos = r > 1.2 ? "di atas" : r < 0.8 ? "di bawah" : "dalam kisaran"
  }

  const last = v[v.length - 1]
  // "periode data", bukan "bulan": Trend_Bulan bisa bolong
  return {
    ok: true, cv, last, last3, forecastPosition: pos,
    range3: [Math.min(...tail), Math.max(...tail)],
    bullets: [
      `${name} ${volat}, arah ${arah} pada ${v.length} periode data terakhir.`,
      `Puncak ${fmt(v[iMax], unit)} (${fmtBulan(l[iMax])}), terendah ${fmt(v[iMin], unit)} (${fmtBulan(l[iMin])}).`,
      `Periode terakhir ${fmt(last, unit)} (${fmtBulan(l[l.length - 1])}).`
    ]
  }
}

function pctDiff(now: number, base: number | null): string | null {
  if (base === null || base === 0) return null
  const p = ((now - base) / base) * 100
  return `${p >= 0 ? "+" : "-"}${Math.abs(p).toFixed(0)}%`
}

// -----------------------------------------------------
// MAIN
// -----------------------------------------------------
export function buildMaterialAnalysis(
  row: AnalysisInput,
  unit = "kg"
): MaterialAnalysis {
  const stock = num(row.Stock)
  const fGI = num(row.Forecast_GI)
  const fGR = num(row.Forecast_GR)
  const proj = num(row.Projected_Stock)
  const cov = num(row.Coverage)
  const status = row.Status && row.Status !== "-" ? row.Status : null

  const hasGI = row.Has_GI !== false
  const hasGR = row.Has_GR === true
  const hasStock = row.Has_Stock === true
  const complete = hasGI && hasGR && hasStock && fGI !== null && fGR !== null

  const giDesc = describeSeries(row.Trend_GI, row.Trend_Date, fGI, "GI", unit)
  const grDesc = hasGR
    ? describeSeries(row.Trend_GR, row.Trend_Date_GR ?? row.Trend_Date, fGR, "GR", unit)
    : null

  // ---------- 1. KONDISI ----------
  let kondisi: MaterialAnalysis["kondisi"]
  if (!(hasGI && hasGR && hasStock)) {
    const missing = [
      !hasGI && "GI", !hasGR && "GR", !hasStock && "Stock"
    ].filter(Boolean).join(", ")
    kondisi = {
      severity: "info", status, metrics: [],
      bullets: [`Analisis belum lengkap karena data ${missing} belum tersedia untuk material ini.`]
    }
  } else {
    const sev: Severity =
      status === "Aman" ? "low"
        : status === "Kritis" ? "medium"
          : status === "Reorder" ? "high" : "info"
    const covTxt = cov === null
      ? "-"
      : cov.toLocaleString("id-ID", { maximumFractionDigits: 2 })
    const bullets = [
      `Material berstatus ${status ?? "-"} dengan coverage ${covTxt} periode.`,
      `Stok saat ini ${fmt(stock, unit)} terhadap forecast GI ${fmt(fGI, unit)}.`
    ]
    if ((stock ?? 0) <= 0) {
      bullets.push("Belum ada persediaan yang dapat digunakan untuk memenuhi kebutuhan GI periode berikutnya.")
    }
    kondisi = {
      severity: sev, status, bullets,
      metrics: [
        { label: "Coverage", value: `${covTxt} periode` },
        { label: "Stok Saat Ini", value: fmt(stock, unit) }
      ]
    }
  }

  // ---------- 2. HISTORIS ----------
  const historis: MaterialAnalysis["historis"] = {
    gi: { title: "GI (Pemakaian)", bullets: giDesc.bullets },
    gr: grDesc ? { title: "GR (Penerimaan)", bullets: grDesc.bullets } : null
  }

  // ---------- 3. FORECAST vs HISTORIS ----------
  const fcBullets: string[] = []
  if (fGI !== null && giDesc.ok && giDesc.last3 !== null) {
    const d = pctDiff(fGI, giDesc.last3)
    fcBullets.push(
      `Forecast GI ${fmt(fGI, unit)} berada ${giDesc.forecastPosition} rata-rata 3 periode terakhir ` +
      `(${fmt(giDesc.last3, unit)})${d ? `, selisih ${d}` : ""}.`
    )
  }
  if (fGR !== null && grDesc?.ok && grDesc.range3 && grDesc.last !== null) {
    const [lo, hi] = grDesc.range3
    const rel = fGR < grDesc.last ? "lebih rendah dari" : fGR > grDesc.last ? "lebih tinggi dari" : "sama dengan"
    const kisaran = fGR < lo ? "di bawah" : fGR > hi ? "di atas" : "di dalam"
    fcBullets.push(
      `Forecast GR ${fmt(fGR, unit)} ${rel} penerimaan periode terakhir (${fmt(grDesc.last, unit)}), ` +
      `${kisaran} kisaran 3 periode terakhir (${fmt(lo)}–${fmt(hi, unit)}).`
    )
  }
  if (!fcBullets.length) {
    fcBullets.push("Data historis belum cukup untuk membandingkan forecast dengan pola terbaru.")
  }

  // ---------- 4. DAMPAK STOK ----------
  let stokSev: Severity = "info"
  let stokBullets: string[] = []
  let formula: MaterialAnalysis["stok"]["formula"] = null
  if (complete && stock !== null) {
    const f_gi = fGI as number
    const f_gr = fGR as number
    const net = f_gr - f_gi
    stokBullets = [
      `Forecast GR ${fmt(f_gr, unit)} vs forecast GI ${fmt(f_gi, unit)}: ${net >= 0 ? "surplus" : "defisit"} ${fmt(Math.abs(net), unit)}.`,
      `Projected stock ${fmt(proj, unit)} bila GR terealisasi sesuai forecast.`
    ]
    if (stock < f_gi && (proj ?? 0) >= 0) {
      stokBullets.push(
        `Selama GR belum masuk, stok aktual tetap ${fmt(stock, unit)}` +
        `${status ? ` dan status tetap ${status}` : ""}.`
      )
    }
    stokSev = (proj ?? 0) < 0 ? "high" : "info"
    formula = {
      expr: `${fmt(stock)} + ${fmt(f_gr)} − ${fmt(f_gi)}`,
      result: `= ${fmt(proj, unit)}`
    }
  } else {
    stokBullets = ["Projected stock belum dapat dihitung karena data GI, GR, atau Stock belum lengkap."]
  }

  // ---------- 5. SKENARIO GR TERLAMBAT ----------
  // Data bulanan -> urutan tanggal GR vs GI tidak bisa dibaca.
  // Yang bisa dihitung jujur: kalau GR belum masuk, stok cukup tidak?
  const risks: MaterialAnalysis["risiko"] = []
  const recs: string[] = []
  let skenario: MaterialAnalysis["skenario"] = null
  let priority = "Monitoring rutin"

  if (complete && stock !== null) {
    const f_gi = fGI as number
    const f_gr = fGR as number
    const stockOnly = stock - f_gi
    const NOTE = "Urutan tanggal GR dan GI belum dapat dipastikan karena data masih bulanan."

    if (stockOnly >= 0) {
      skenario = {
        severity: "low",
        headline: "Stok cukup tanpa GR",
        note: NOTE,
        bullets: [
          `Stok ${fmt(stock, unit)} masih menutup GI forecast ${fmt(f_gi, unit)}; sisa ${fmt(stockOnly, unit)}.`,
          "Keterlambatan GR tidak langsung menyebabkan stockout."
        ]
      }
    } else {
      const sev: Severity = stock <= 0 ? "high" : "medium"
      skenario = {
        severity: sev,
        headline: "Berisiko stockout sementara bila GR terlambat",
        note: NOTE,
        bullets: [
          stock <= 0
            ? `Tidak ada stok untuk memenuhi GI forecast ${fmt(f_gi, unit)}.`
            : `Stok ${fmt(stock, unit)} hanya menutup sebagian GI forecast ${fmt(f_gi, unit)}.`,
          `Kekurangan ${fmt(-stockOnly, unit)} sampai GR masuk.`
        ]
      }
      risks.push({
        severity: sev,
        text: `Ketergantungan pada realisasi GR ${fmt(f_gr, unit)}: stok saat ini tidak cukup untuk GI forecast, kekurangan ${fmt(-stockOnly, unit)} bila GR tidak masuk.`
      })
      recs.push(`Pastikan GR ${fmt(f_gr, unit)} terealisasi sesuai jadwal (konfirmasi ke purchasing/vendor).`)
      priority = "Monitoring penerimaan GR"
    }

    if ((proj ?? 0) < 0) {
      risks.push({
        severity: "high",
        text: `Projected stock negatif (${fmt(proj, unit)}) meski GR forecast terealisasi.`
      })
      recs.push(`Pertimbangkan pengadaan tambahan minimal ${fmt(-(proj as number), unit)}.`)
      priority = "Pengadaan tambahan"
    } else if (f_gr < f_gi) {
      risks.push({
        severity: "medium",
        text: "Forecast GR lebih kecil dari forecast GI; stok akan terkuras walau projected stock masih positif."
      })
    } else {
      recs.push("Belum ada indikasi kebutuhan tambahan selama GR terealisasi sesuai estimasi dan GI tidak meningkat signifikan.")
    }
  }

  // ---------- RISIKO TAMBAHAN ----------
  if (giDesc.ok && giDesc.forecastPosition === "di atas") {
    risks.push({
      severity: "medium",
      text: "Forecast GI lebih tinggi dari rata-rata terbaru; perlu diwaspadai kebutuhan di atas pola penggunaan."
    })
    recs.push("Monitor realisasi GI karena forecast menunjukkan kebutuhan lebih tinggi dari pola penggunaan terbaru.")
  }
  if (grDesc?.ok && grDesc.cv >= 0.6) {
    risks.push({
      severity: "medium",
      text: "Penerimaan GR historis sangat fluktuatif, jumlah GR sulit dipastikan."
    })
  }

  // keandalan forecast
  const q: string[] = []
  if (row.Low_Confidence) q.push("model menandai forecast GI ini low confidence")
  const mape = num(row.MAPE)
  if (mape !== null && mape > 100) q.push(`MAPE GI ${mape.toFixed(0)}%`)
  const hc = num(row.History_Count)
  if (hc !== null && hc < 12) q.push(`histori data hanya ${hc} periode`)
  if (giDesc.ok && giDesc.cv >= 0.6) q.push("pola GI sangat fluktuatif")
  if (q.length) {
    risks.push({
      severity: "medium",
      text: `Forecast perlu dibaca hati-hati: ${q.join("; ")}.`
    })
  }

  risks.sort((a, b) => SEV_ORDER[b.severity] - SEV_ORDER[a.severity])
  if (!risks.length && complete) {
    risks.push({ severity: "low", text: "Tidak ada risiko signifikan dari data saat ini." })
  }
  if (!recs.length && complete) {
    recs.push("Lanjutkan monitoring rutin; belum ada tindakan khusus.")
  }

  return {
    overallSeverity: risks[0]?.severity ?? "info",
    complete,
    kondisi,
    historis,
    forecast: { bullets: fcBullets },
    stok: { severity: stokSev, bullets: stokBullets, formula },
    skenario,
    risiko: risks,
    rekomendasi: {
      priority,
      bullets: recs,
      warning: complete
        ? "Evaluasi kembali bila GR terlambat, realisasi GR lebih rendah dari forecast, atau GI aktual meningkat."
        : null
    }
  }
}
