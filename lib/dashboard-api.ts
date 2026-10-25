// ============================================================
// lib/dashboard-api.ts
//
// Pengambilan dan perapian data untuk Dashboard utama.
//   - loadBarang() : GET {API_BARANG}/api/projection/latest
//   - loadJasa()   : GET {API_JASA}/forecast
// Tidak ada React di file ini, jadi mudah dites terpisah.
// ============================================================

// ============================================================
// KONFIGURASI
// Set di .env.local (opsional, ada nilai bawaan):
// NEXT_PUBLIC_API_BARANG_URL=http://127.0.0.1:8001
// NEXT_PUBLIC_API_JASA_URL=http://127.0.0.1:8000
// ============================================================

const API_BARANG =
  process.env.NEXT_PUBLIC_API_BARANG_URL ?? "http://127.0.0.1:8001"

const API_JASA =
  process.env.NEXT_PUBLIC_API_JASA_URL ?? "http://127.0.0.1:8000"

const TIMEOUT_MS = 15000
export const POLL_MS = 5000


// ============================================================
// TIPE
// ============================================================

export type Load<T> =
  | { state: "loading" }
  | { state: "error"; message: string }
  | { state: "empty"; message: string; training?: boolean }
  | { state: "ready"; data: T }

export type AttentionRow = {
  material: string
  description: string
  stock: number | null
  coverage: number
  unit: string
  status: "kritis" | "reorder"
}

export type BarangSummary = {
  total: number
  aman: number
  kritis: number
  reorder: number
  avgCoverage: number | null
  attention: AttentionRow[]
  forecastMonth: string | null
  periodStart: string | null
  periodEnd: string | null
}

export type Contributor = {
  name: string
  amount: number
  percentage: number | null
}

export type Bar = {
  label: string
  value: number
  forecast: boolean
}

export type JasaSummary = {
  total: number
  rutin: number
  nonRutin: number
  rutinPct: number
  nonRutinPct: number
  changePct: number | null
  lastLabel: string | null
  bars: Bar[]
  forecastMonth: string | null
  periodStart: string | null
  periodEnd: string | null
  trainedAt: string | null
  training: boolean
  rutinTop: Contributor[]
  nonRutinTop: Contributor[]
}


// ============================================================
// HELPER UMUM
// ============================================================

const MONTHS = [
  "Januari", "Februari", "Maret", "April", "Mei", "Juni",
  "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

const MONTHS_SHORT = [
  "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
  "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
]

function num(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function parsePeriod(value: unknown): { y: number; m: number } | null {
  if (typeof value !== "string") return null
  const match = value.match(/^(\d{4})-(\d{1,2})/)
  if (!match) return null
  const m = Number(match[2])
  if (m < 1 || m > 12) return null
  return { y: Number(match[1]), m }
}

export function formatMonth(value: unknown): string | null {
  if (value === null || value === undefined || value === "") return null
  const p = parsePeriod(value)
  if (p) return `${MONTHS[p.m - 1]} ${p.y}`
  return String(value)
}

export function formatMonthShort(value: unknown): string {
  const p = parsePeriod(value)
  if (p) return `${MONTHS_SHORT[p.m - 1]} ${String(p.y).slice(2)}`
  return String(value ?? "")
}

function monthKey(value: unknown): string | null {
  const p = parsePeriod(value)
  if (!p) return null
  return `${p.y}-${String(p.m).padStart(2, "0")}`
}

export function formatNumber(value: number | null, digits = 0): string {
  if (value === null) return "-"
  return new Intl.NumberFormat("id-ID", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value)
}

export function formatRupiahShort(value: number): string {
  const abs = Math.abs(value)
  const fmt = (n: number) =>
    new Intl.NumberFormat("id-ID", { maximumFractionDigits: 1 }).format(n)
  if (abs >= 1e12) return `Rp ${fmt(value / 1e12)} T`
  if (abs >= 1e9) return `Rp ${fmt(value / 1e9)} M`
  if (abs >= 1e6) return `Rp ${fmt(value / 1e6)} jt`
  return `Rp ${formatNumber(value)}`
}

export function formatRupiahFull(value: number): string {
  return `Rp ${formatNumber(value)}`
}

function formatTrainedAt(value: unknown): string | null {
  if (!value) return null
  const date = new Date(String(value))
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat("id-ID", {
    dateStyle: "long",
    timeZone: "Asia/Jakarta",
  }).format(date)
}

function errMessage(err: unknown): string {
  if (err instanceof Error) {
    if (err.message === "Failed to fetch") {
      return "Tidak dapat terhubung ke backend. Pastikan server sudah berjalan."
    }
    return err.message
  }
  return "Terjadi kesalahan saat mengambil data."
}

async function fetchJson(url: string): Promise<any> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const response = await fetch(url, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    })
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`)
    }
    return await response.json()
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("Backend tidak merespons (timeout).")
    }
    throw err
  } finally {
    clearTimeout(timer)
  }
}


// ============================================================
// LOAD BARANG
// Sumber: GET /api/projection/latest (sama dengan Forecast Barang)
// Aturan status & coverage disamakan dengan KPI Stock Availability.
// ============================================================

function normalizeStatus(value: unknown): "aman" | "kritis" | "reorder" | null {
  const s = String(value ?? "").trim().toLowerCase()
  if (s === "aman" || s === "normal" || s === "normal stock") return "aman"
  if (s === "kritis" || s === "stock out risk") return "kritis"
  if (s === "reorder") return "reorder"
  return null
}

export async function loadBarang(): Promise<Load<BarangSummary>> {
  try {
    const json = await fetchJson(`${API_BARANG}/api/projection/latest`)
    const rows: any[] = Array.isArray(json?.data) ? json.data : []

    if (!json?.exists || rows.length === 0) {
      return {
        state: "empty",
        message:
          json?.message ??
          "Data forecast barang belum tersedia. Upload data di menu Forecast Barang.",
      }
    }

    let aman = 0
    let kritis = 0
    let reorder = 0
    const coverages: number[] = []
    const attention: AttentionRow[] = []
    const forecastMonths = new Map<string, number>()
    let periodStart: string | null = null
    let periodEnd: string | null = null

    for (const row of rows) {
      const status = normalizeStatus(row.Status)
      if (status === "aman") aman++
      if (status === "kritis") kritis++
      if (status === "reorder") reorder++

      const coverage = num(row.Coverage)
      if (coverage !== null) coverages.push(coverage)

      if ((status === "kritis" || status === "reorder") && coverage !== null) {
        attention.push({
          material: String(row.Material ?? ""),
          description: String(row["Material Description"] ?? ""),
          stock: num(row.Stock),
          coverage,
          unit: row.Unit ? String(row.Unit) : "",
          status,
        })
      }

      const fm = monthKey(row.Forecast_Bulan ?? row.Bulan)
      if (fm) forecastMonths.set(fm, (forecastMonths.get(fm) ?? 0) + 1)

      if (Array.isArray(row.Trend_Bulan)) {
        for (const item of row.Trend_Bulan) {
          const k = monthKey(item)
          if (!k) continue
          if (periodStart === null || k < periodStart) periodStart = k
          if (periodEnd === null || k > periodEnd) periodEnd = k
        }
      }
    }

    attention.sort((a, b) => a.coverage - b.coverage)

    let forecastMonth: string | null = null
    let best = 0
    forecastMonths.forEach((count, key) => {
      if (count > best) {
        best = count
        forecastMonth = key
      }
    })

    return {
      state: "ready",
      data: {
        total: rows.length,
        aman,
        kritis,
        reorder,
        avgCoverage:
          coverages.length > 0
            ? coverages.reduce((a, b) => a + b, 0) / coverages.length
            : null,
        attention: attention.slice(0, 5),
        forecastMonth,
        periodStart,
        periodEnd,
      },
    }
  } catch (err) {
    return { state: "error", message: errMessage(err) }
  }
}


// ============================================================
// LOAD JASA
// Sumber: GET /forecast (sama dengan Forecast Jasa)
// ============================================================

function toContributors(list: unknown): Contributor[] {
  if (!Array.isArray(list)) return []
  return list.slice(0, 3).map((item: any) => ({
    name: String(item?.short_text ?? "-"),
    amount: num(item?.amount) ?? 0,
    percentage: num(item?.percentage),
  }))
}

function combineHistorical(json: any): { period: string; total: number }[] {
  const map = new Map<string, number>()
  for (const group of [json?.rutin?.historical, json?.non_rutin_ovh?.historical]) {
    if (!Array.isArray(group)) continue
    for (const row of group) {
      const period = row?.period
      if (!period) continue
      map.set(String(period), (map.get(String(period)) ?? 0) + (num(row?.actual) ?? 0))
    }
  }
  return Array.from(map.entries())
    .map(([period, total]) => ({ period, total }))
    .sort((a, b) => a.period.localeCompare(b.period))
}

export async function loadJasa(): Promise<Load<JasaSummary>> {
  try {
    const json = await fetchJson(`${API_JASA}/forecast`)
    const training = json?.status === "training"

    if (json?.status === "empty") {
      return {
        state: "empty",
        message: "Forecast jasa belum tersedia. Upload data di menu Forecast Jasa.",
      }
    }

    if (!json?.rutin && !json?.non_rutin_ovh) {
      if (training) {
        return {
          state: "empty",
          training: true,
          message: "Model jasa sedang dilatih. Data akan muncul otomatis.",
        }
      }
      throw new Error("Format respons forecast jasa tidak dikenali.")
    }

    const rutin = num(json.rutin?.forecast) ?? 0
    const nonRutin = num(json.non_rutin_ovh?.forecast) ?? 0
    const total = num(json.total_forecast) ?? rutin + nonRutin

    const history = combineHistorical(json)
    const last = history.length > 0 ? history[history.length - 1] : null

    const changePct =
      last && last.total > 0 ? ((total - last.total) / last.total) * 100 : null

    const forecastLabel =
      json.forecast_month_label ??
      json.rutin?.forecast_month_label ??
      json.non_rutin_ovh?.forecast_month_label ??
      null

    const bars: Bar[] = history.slice(-6).map((row) => ({
      label: formatMonthShort(row.period),
      value: row.total,
      forecast: false,
    }))
    bars.push({ label: "Prediksi", value: total, forecast: true })

    return {
      state: "ready",
      data: {
        total,
        rutin,
        nonRutin,
        rutinPct: total > 0 ? (rutin / total) * 100 : 0,
        nonRutinPct: total > 0 ? (nonRutin / total) * 100 : 0,
        changePct,
        lastLabel: last ? formatMonthShort(last.period) : null,
        bars,
        forecastMonth: formatMonth(forecastLabel),
        periodStart: history.length > 0 ? history[0].period : null,
        periodEnd: history.length > 0 ? history[history.length - 1].period : null,
        trainedAt: formatTrainedAt(
          json.trained_at ?? json.rutin?.trained_at ?? json.non_rutin_ovh?.trained_at
        ),
        training,
        rutinTop: toContributors(json.rutin?.contributors),
        nonRutinTop: toContributors(json.non_rutin_ovh?.contributors),
      },
    }
  } catch (err) {
    return { state: "error", message: errMessage(err) }
  }
}
