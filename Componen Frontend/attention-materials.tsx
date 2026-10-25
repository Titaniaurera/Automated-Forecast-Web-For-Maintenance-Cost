import Link from "next/link"

import {
  formatNumber,
  type BarangSummary,
  type Load,
} from "@/lib/dashboard-api"
import { CARD, StateBox } from "./shared"


// ============================================================
// components/dashboard/attention-materials.tsx
//
// Kartu "Material yang perlu perhatian": sampai lima material
// berstatus Kritis atau Reorder dengan coverage paling rendah
// (data sudah diurutkan oleh loadBarang di lib/dashboard-api.ts).
// ============================================================

export default function AttentionMaterials({ load }: { load: Load<BarangSummary> }) {
  return (
    <div className={`${CARD} flex flex-col gap-3`}>
      <h2 className="text-lg font-bold">Material yang perlu perhatian</h2>
      <p className="text-sm text-[#b4c2e6]">Coverage paling rendah, urut dari yang paling mendesak.</p>

      {load.state !== "ready" ? (
        <StateBox state={load.state} message={"message" in load ? load.message : undefined} />
      ) : load.data.attention.length === 0 ? (
        <p className="py-6 text-sm text-[#b4c2e6]">Tidak ada material berstatus Kritis atau Reorder.</p>
      ) : (
        load.data.attention.map((row) => (
          <div key={row.material} className="flex items-center gap-3 rounded-xl bg-[#14245a] px-4 py-3">
            <div className="min-w-0 flex-1">
              <div className="text-sm font-bold">{row.material}</div>
              <div className="truncate text-xs text-[#b4c2e6]" title={row.description}>{row.description}</div>
            </div>
            <div className="text-right text-xs text-[#b4c2e6]">
              stok {formatNumber(row.stock)}{row.unit ? ` ${row.unit}` : ""}
              <br />
              coverage {formatNumber(row.coverage, 2)}
            </div>
            <span
              className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                row.status === "reorder" ? "bg-[#4a1d27] text-[#ffa3a3]" : "bg-[#4a3a12] text-[#fcd34d]"
              }`}
            >
              {row.status === "reorder" ? "Reorder" : "Kritis"}
            </span>
          </div>
        ))
      )}

      <Link href="/forecast-barang" className="mt-1 text-sm font-semibold text-[#8fb0ff] transition hover:text-white">
        Lihat semua di Stock Availability →
      </Link>
    </div>
  )
}
