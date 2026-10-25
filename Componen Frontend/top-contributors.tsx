import {
  formatNumber,
  formatRupiahShort,
  type Contributor,
  type JasaSummary,
  type Load,
} from "@/lib/dashboard-api"
import { CARD, StateBox } from "./shared"


// ============================================================
// components/dashboard/top-contributors.tsx
//
// Kartu "Kontributor jasa terbesar": tiga pos biaya teratas
// untuk Rutin dan tiga untuk Non Rutin + OVH pada bulan forecast,
// lengkap dengan nilai Rupiah dan persentasenya.
// (Daftar dipotong tiga teratas oleh loadJasa di
// lib/dashboard-api.ts.)
// ============================================================

function ContributorGroup({
  title,
  color,
  items,
}: {
  title: string
  color: string
  items: Contributor[]
}) {
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xs font-bold tracking-wide" style={{ color }}>{title}</div>
      {items.length === 0 ? (
        <p className="rounded-xl bg-[#14245a] px-4 py-3 text-xs text-[#b4c2e6]">Belum ada data kontributor.</p>
      ) : (
        items.map((item, i) => (
          <div key={`${item.name}-${i}`} className="flex items-center justify-between gap-3 rounded-xl bg-[#14245a] px-4 py-3">
            <span className="min-w-0 truncate text-sm font-semibold" title={item.name}>{item.name}</span>
            <span className="shrink-0 text-xs text-[#b4c2e6]">
              {formatRupiahShort(item.amount)}
              {item.percentage !== null ? ` · ${formatNumber(item.percentage, 1)}%` : ""}
            </span>
          </div>
        ))
      )}
    </div>
  )
}

export default function TopContributors({ load }: { load: Load<JasaSummary> }) {
  return (
    <div className={`${CARD} flex flex-col gap-3`}>
      <h2 className="text-lg font-bold">Kontributor jasa terbesar</h2>
      <p className="text-sm text-[#b4c2e6]">Pos biaya yang paling menentukan pada bulan forecast.</p>

      {load.state !== "ready" ? (
        <StateBox state={load.state} message={"message" in load ? load.message : undefined} />
      ) : (
        <>
          <ContributorGroup title="RUTIN" color="#8fb0ff" items={load.data.rutinTop} />
          <ContributorGroup title="NON RUTIN + OVH" color="#ffb067" items={load.data.nonRutinTop} />
        </>
      )}
    </div>
  )
}
