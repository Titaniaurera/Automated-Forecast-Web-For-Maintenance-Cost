"use client"

import { useMemo, type ReactNode } from "react"
import {
  ClipboardList,
  Package,
  Activity,
  ArrowUpFromLine,
  ArrowDownToLine,
  TrendingUp,
  Boxes,
  Clock,
  AlertTriangle,
  ListChecks,
  CheckCircle2
} from "lucide-react"
import {
  buildMaterialAnalysis,
  type AnalysisInput,
  type Severity
} from "@/lib/material-analysis"

// =====================================================
// TEMA WARNA PER KARTU
// (class ditulis utuh supaya terbaca Tailwind)
// =====================================================
type Theme = {
  box: string
  num: string
  title: string
  bullet: string
}

const THEME: Record<"blue" | "green" | "purple" | "cyan" | "orange" | "red" | "emerald", Theme> = {
  blue: {
    box: "border-blue-200 bg-blue-50/40",
    num: "bg-blue-600",
    title: "text-blue-700",
    bullet: "marker:text-blue-500"
  },
  green: {
    box: "border-green-200 bg-green-50/40",
    num: "bg-green-600",
    title: "text-green-700",
    bullet: "marker:text-green-500"
  },
  purple: {
    box: "border-purple-200 bg-purple-50/40",
    num: "bg-purple-600",
    title: "text-purple-700",
    bullet: "marker:text-purple-500"
  },
  cyan: {
    box: "border-cyan-200 bg-cyan-50/40",
    num: "bg-cyan-600",
    title: "text-cyan-700",
    bullet: "marker:text-cyan-500"
  },
  orange: {
    box: "border-orange-200 bg-orange-50/40",
    num: "bg-orange-500",
    title: "text-orange-700",
    bullet: "marker:text-orange-500"
  },
  red: {
    box: "border-red-200 bg-red-50/40",
    num: "bg-red-600",
    title: "text-red-700",
    bullet: "marker:text-red-500"
  },
  emerald: {
    box: "border-emerald-200 bg-emerald-50/40",
    num: "bg-emerald-600",
    title: "text-emerald-700",
    bullet: "marker:text-emerald-500"
  }
}

const SEV_PILL: Record<Severity, string> = {
  high: "bg-red-100 text-red-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-emerald-100 text-emerald-700",
  info: "bg-slate-100 text-slate-600"
}

const STATUS_PILL: Record<string, string> = {
  Reorder: "bg-red-100 text-red-600",
  Kritis: "bg-amber-100 text-amber-700",
  Aman: "bg-emerald-100 text-emerald-700"
}

const SEV_DOT: Record<Severity, string> = {
  high: "text-red-600",
  medium: "text-amber-600",
  low: "text-emerald-600",
  info: "text-slate-500"
}

// =====================================================
// KOMPONEN KECIL
// =====================================================
function Card({
  n,
  title,
  icon,
  theme,
  right,
  className = "",
  children
}: {
  n: number
  title: string
  icon: ReactNode
  theme: keyof typeof THEME
  right?: ReactNode
  className?: string
  children: ReactNode
}) {
  const t = THEME[theme]
  return (
    <section className={`rounded-xl border p-4 ${t.box} ${className}`}>
      <header className="mb-3 flex items-center gap-2">
        <span
          className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white ${t.num}`}
        >
          {n}
        </span>
        <span className={`shrink-0 ${t.title}`}>{icon}</span>
        <h4 className={`text-sm font-semibold ${t.title}`}>{title}</h4>
        {right && <div className="ml-auto">{right}</div>}
      </header>
      {children}
    </section>
  )
}

function Bullets({
  items,
  theme
}: {
  items: string[]
  theme: keyof typeof THEME
}) {
  return (
    <ul
      className={`list-disc space-y-1.5 pl-4 text-xs leading-relaxed text-slate-700 ${THEME[theme].bullet}`}
    >
      {items.map((t, i) => (
        <li key={i}>{t}</li>
      ))}
    </ul>
  )
}

// =====================================================
// MAIN
// =====================================================
interface Props {
  row: AnalysisInput
  unit?: string
}

export default function MaterialAnalysisCard({ row, unit = "" }: Props) {
  const a = useMemo(() => buildMaterialAnalysis(row, unit), [row, unit])

  return (
    <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5">
      <div className="mb-4 flex items-center gap-2">
        <ClipboardList className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-semibold text-slate-900">
          Analisis Material
        </h3>
      </div>

      {/* ================= BARIS 1 ================= */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        {/* 1. KONDISI */}
        <Card
          n={1}
          title="Kondisi Material Saat Ini"
          icon={<Package className="h-4 w-4" />}
          theme="blue"
          className="lg:col-span-3"
          right={
            a.kondisi.status && (
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_PILL[a.kondisi.status] ?? SEV_PILL.info}`}
              >
                {a.kondisi.status}
              </span>
            )
          }
        >
          <Bullets items={a.kondisi.bullets} theme="blue" />
          {a.kondisi.metrics.length > 0 && (
            <div className="mt-3 grid grid-cols-2 gap-2">
              {a.kondisi.metrics.map((m) => (
                <div
                  key={m.label}
                  className="rounded-lg border border-blue-100 bg-white p-2"
                >
                  <p className="text-[10px] text-slate-500">{m.label}</p>
                  <p className="text-xs font-bold text-slate-900">{m.value}</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* 2. PERGERAKAN GI & GR */}
        <Card
          n={2}
          title="Pergerakan GI & GR Historis"
          icon={<Activity className="h-4 w-4" />}
          theme="green"
          className="lg:col-span-6"
        >
          <div
            className={`grid gap-3 ${a.historis.gr ? "md:grid-cols-2" : "grid-cols-1"}`}
          >
            <div className="rounded-lg border border-green-100 bg-white p-3">
              <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-green-700">
                <ArrowUpFromLine className="h-3.5 w-3.5" />
                {a.historis.gi.title}
              </p>
              <Bullets items={a.historis.gi.bullets} theme="green" />
            </div>
            {a.historis.gr && (
              <div className="rounded-lg border border-green-100 bg-white p-3">
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-green-700">
                  <ArrowDownToLine className="h-3.5 w-3.5" />
                  {a.historis.gr.title}
                </p>
                <Bullets items={a.historis.gr.bullets} theme="green" />
              </div>
            )}
          </div>
        </Card>

        {/* 3. FORECAST GI & GR */}
        <Card
          n={3}
          title="Forecast GI & GR"
          icon={<TrendingUp className="h-4 w-4" />}
          theme="purple"
          className="lg:col-span-3"
        >
          <Bullets items={a.forecast.bullets} theme="purple" />
        </Card>
      </div>

      {/* ================= BARIS 2 ================= */}
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {/* 4. DAMPAK STOK */}
        <Card
          n={4}
          title="Dampak terhadap Stok"
          icon={<Boxes className="h-4 w-4" />}
          theme="cyan"
        >
          <Bullets items={a.stok.bullets} theme="cyan" />
          {a.stok.formula && (
            <div className="mt-3 rounded-lg border border-cyan-100 bg-white p-2.5">
              <p className="text-[10px] text-slate-500">Projected Stock</p>
              <p className="text-xs font-semibold text-slate-700">
                {a.stok.formula.expr}
              </p>
              <p
                className={`text-sm font-bold ${a.stok.severity === "high" ? "text-red-600" : "text-slate-900"}`}
              >
                {a.stok.formula.result}
              </p>
            </div>
          )}
        </Card>

        {/* 5. SKENARIO GR TERLAMBAT */}
        <Card
          n={5}
          title="Skenario GR Terlambat"
          icon={<Clock className="h-4 w-4" />}
          theme="orange"
        >
          {a.skenario ? (
            <>
              <p className={`mb-2 text-xs font-semibold ${SEV_DOT[a.skenario.severity]}`}>
                {a.skenario.headline}
              </p>
              <Bullets items={a.skenario.bullets} theme="orange" />
              <p className="mt-3 text-[11px] italic leading-snug text-slate-500">
                {a.skenario.note}
              </p>
            </>
          ) : (
            <p className="text-xs text-slate-600">
              Skenario belum dapat dihitung karena data GI, GR, atau Stock belum lengkap.
            </p>
          )}
        </Card>

        {/* 6. RISIKO */}
        <Card
          n={6}
          title="Risiko"
          icon={<AlertTriangle className="h-4 w-4" />}
          theme="red"
        >
          {a.risiko.length > 0 ? (
            <Bullets items={a.risiko.map((r) => r.text)} theme="red" />
          ) : (
            <p className="text-xs text-slate-600">
              Risiko belum dapat dinilai karena data belum lengkap.
            </p>
          )}
        </Card>

        {/* 7. REKOMENDASI */}
        <Card
          n={7}
          title="Rekomendasi"
          icon={<ListChecks className="h-4 w-4" />}
          theme="emerald"
        >
          {a.complete ? (
            <>
              <span className="mb-2 inline-block rounded-full border border-emerald-200 bg-white px-2.5 py-0.5 text-[11px] font-semibold text-emerald-700">
                Prioritas: {a.rekomendasi.priority}
              </span>
              <ul className="space-y-2 text-xs leading-relaxed text-slate-700">
                {a.rekomendasi.bullets.map((t, i) => (
                  <li key={i} className="flex gap-2">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                    <span>{t}</span>
                  </li>
                ))}
              </ul>
              {a.rekomendasi.warning && (
                <div className="mt-3 flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-2.5 text-[11px] leading-snug text-amber-800">
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                  <span>{a.rekomendasi.warning}</span>
                </div>
              )}
            </>
          ) : (
            <p className="text-xs text-slate-600">
              Rekomendasi tersedia setelah data GI, GR, dan Stock lengkap.
            </p>
          )}
        </Card>
      </div>
    </div>
  )
}
