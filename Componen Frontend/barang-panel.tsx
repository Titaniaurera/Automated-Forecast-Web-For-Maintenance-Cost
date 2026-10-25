import Link from "next/link"

import {
  formatNumber,
  type BarangSummary,
  type Load,
} from "@/lib/dashboard-api"
import { CARD, Kpi, PanelHeader, StateBox } from "./shared"


// ============================================================
// components/dashboard/barang-panel.tsx
//
// Panel "Barang" di Dashboard utama: empat kartu KPI status stok
// (total, Aman, Kritis, Reorder), rata-rata coverage, dan tautan
// ke halaman Forecast Barang.
// ============================================================

function pct(part: number, total: number): string {
  if (total <= 0) return "-"
  return `${formatNumber((part / total) * 100, 1)}% dari total`
}

export default function BarangPanel({ load, onRetry }: { load: Load<BarangSummary>; onRetry: () => void }) {
  return (
    <div className={`${CARD} flex flex-col gap-4`}>
      <PanelHeader title="Barang" href="/forecast-barang" linkLabel="Buka Forecast Barang" />

      {load.state !== "ready" ? (
        <StateBox
          state={load.state}
          message={"message" in load ? load.message : undefined}
          onRetry={onRetry}
        />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <Kpi label="Total Material" value={formatNumber(load.data.total)} sub="material aktif" />
            <Kpi label="Aman" value={formatNumber(load.data.aman)} sub={pct(load.data.aman, load.data.total)} valueClass="text-[#6ee7a0]" />
            <Kpi label="Kritis" value={formatNumber(load.data.kritis)} sub={pct(load.data.kritis, load.data.total)} valueClass="text-[#fcd34d]" />
            <Kpi label="Reorder" value={formatNumber(load.data.reorder)} sub={pct(load.data.reorder, load.data.total)} valueClass="text-[#ffa3a3]" />
          </div>

          <div className="flex items-center justify-between rounded-2xl bg-[#14245a] px-4 py-3.5">
            <span className="text-sm text-[#b4c2e6]">Rata-rata coverage</span>
            <span className="text-xl font-extrabold">
              {load.data.avgCoverage === null ? "-" : `${formatNumber(load.data.avgCoverage, 2)} bulan`}
            </span>
          </div>

          <Link href="/forecast-barang" className="text-sm font-semibold text-[#8fb0ff] transition hover:text-white">
            Lihat {formatNumber(load.data.reorder)} material Reorder →
          </Link>
        </>
      )}
    </div>
  )
}
