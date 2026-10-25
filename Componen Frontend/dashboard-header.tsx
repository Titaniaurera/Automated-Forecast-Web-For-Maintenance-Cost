import { CircleUser, FileSpreadsheet, Sparkles, CheckCircle2 } from "lucide-react"
import type { ForecastResponse } from "@/lib/forecast-data"

export function DashboardHeader({ data }: { data: ForecastResponse }) {
  return (
    <header className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1.5">
          <h1 className="text-pretty text-2xl font-semibold tracking-tight md:text-3xl">
            Dashboard Forecasting Realisasi Pembayaran
          </h1>
          <p className="text-sm text-muted-foreground">
            Prediksi realisasi pembayaran berdasarkan hasil backend model RUTIN
          </p>
        </div>
        <div className="flex items-center gap-3 rounded-full border border-border bg-card px-3 py-1.5">
          <CircleUser className="size-5 text-primary" />
          <div className="leading-tight">
            <p className="text-sm font-medium">Admin</p>
            <p className="text-[11px] text-muted-foreground">Planning Administrator</p>
          </div>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <InfoTile
          icon={<FileSpreadsheet className="size-4 text-chart-2" />}
          label="File hasil backend"
          value={data.sourceFile}
          mono
        />
        <InfoTile
          icon={<Sparkles className="size-4 text-primary" />}
          label="Mode forecast"
          value={data.mode}
        />
      </div>

      <div className="flex items-center gap-2.5 rounded-lg border border-chart-3/30 bg-chart-3/10 px-4 py-2.5 text-sm text-chart-3">
        <CheckCircle2 className="size-4 shrink-0" />
        Hasil backend berhasil dimuat.
      </div>
    </header>
  )
}

function InfoTile({
  icon,
  label,
  value,
  mono,
}: {
  icon: React.ReactNode
  label: string
  value: string
  mono?: boolean
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="mb-1 flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className={`truncate text-sm text-foreground ${mono ? "font-mono" : ""}`}>{value}</p>
    </div>
  )
}
