import {
  formatMonth,
  type BarangSummary,
  type JasaSummary,
  type Load,
} from "@/lib/dashboard-api"


// ============================================================
// components/dashboard/period-strip.tsx
//
// Strip di bagian bawah Dashboard: untuk barang dan jasa, bulan
// yang diprediksi dan periode data yang dipakai (dari bulan apa
// sampai bulan apa). Untuk jasa ditambah waktu model dilatih.
// ============================================================

function periodRange(start: string | null, end: string | null): string {
  const a = formatMonth(start)
  const b = formatMonth(end)
  if (!a && !b) return "-"
  if (a && b && a !== b) return `${a} s/d ${b}`
  return a ?? b ?? "-"
}

export default function PeriodStrip({
  barang,
  jasa,
}: {
  barang: Load<BarangSummary>
  jasa: Load<JasaSummary>
}) {
  const b = (read: (d: BarangSummary) => string) =>
    barang.state === "ready" ? read(barang.data) : barang.state === "loading" ? "Memuat..." : "-"
  const j = (read: (d: JasaSummary) => string) =>
    jasa.state === "ready" ? read(jasa.data) : jasa.state === "loading" ? "Memuat..." : "-"

  const items = [
    { label: "Barang · Prediksi untuk bulan", value: b((d) => formatMonth(d.forecastMonth) ?? "-") },
    { label: "Barang · Periode data", value: b((d) => periodRange(d.periodStart, d.periodEnd)) },
    {
      label: "Jasa · Prediksi untuk bulan",
      value: j((d) => d.forecastMonth ?? "-"),
      sub: jasa.state === "ready" && jasa.data.trainedAt ? `Model dilatih ${jasa.data.trainedAt}` : undefined,
    },
    { label: "Jasa · Periode data", value: j((d) => periodRange(d.periodStart, d.periodEnd)) },
  ]

  return (
    <section className="grid gap-4 rounded-3xl border border-[#1e3068] bg-[#0d1a3f] px-6 py-5 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => (
        <div key={item.label}>
          <div className="text-xs text-[#b4c2e6]">{item.label}</div>
          <div className="mt-1 text-sm font-bold">{item.value}</div>
          {item.sub && <div className="mt-0.5 text-xs text-[#b4c2e6]">{item.sub}</div>}
        </div>
      ))}
    </section>
  )
}
