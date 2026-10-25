"use client"


import {
  Eye,
  X,
  PackageCheck,
  ShoppingCart,
  AlertTriangle,
  Package,
  ArrowUpFromLine,
  ArrowDownToLine,
  ArrowLeftRight,
  TrendingUp,
  TrendingDown,
  Calculator,
  Database,
  BarChart3,
  Scale
} from "lucide-react"


import { useState } from "react"


import TrendDetailChart from "./trend-detail-chart"
import MaterialAnalysisCard from "./material-analysis-card"


// =====================================================
// TYPE DATA
// =====================================================


interface ForecastItem {

  Material?: string

  "Material Description"?: string

  // [BARU] satuan dari GR
  Unit?: string

  Bulan?: string

  Trend_Bulan?: string[]

  // TAMBAHAN BARU
  // tanggal asli untuk grafik
  // contoh:
  // [
  // "2023-03-01",
  // "2023-04-01",
  // "2023-05-01"
  // ]

  Trend_Date?: string[]

  Forecast_Bulan?: string


  Stock?: number | null

  GI_Actual?: number | null

  GR_Actual?: number | null

  Net_Movement?: number | null


  Forecast_GI?: number | null

  Forecast_GR?: number | null

  Forecast_Net_Movement?: number | null


  Projected_Stock?: number | null

  Gap_Kebutuhan?: number | null


  Coverage?: number | null

  Coverage_Projection?: number | null


  Status?: string | null


  Best_Model_GI?: string

  Best_Model_GR?: string


  Trend_GI?: number[]

  Trend_GR?: number[]


  Has_GI?: boolean

  Has_GR?: boolean

  Has_Stock?: boolean


  History_Count?: number | null

}


interface DataTableProps {

  data: ForecastItem[]

  currentPage: number

  onPageChange: (page: number) => void

}


// =====================================================
// TREND CHANGE
// =====================================================


function getTrendChange(

  trend: number[] | undefined

) {

  if (

    !trend ||

    trend.length < 2

  ) {

    return null

  }


  const previous =

    trend[trend.length - 2]


  const current =

    trend[trend.length - 1]


  if (previous === 0) {

    return null

  }


  return (

    ((current - previous) / previous) * 100

  ).toFixed(1)

}


// =====================================================
// TREND PERCENTAGE
// =====================================================


function getTrendPercentage(

  trend: number[] | undefined

) {

  if (

    !trend ||

    trend.length < 2

  ) {

    return null

  }


  const previous =

    trend[trend.length - 2]


  const current =

    trend[trend.length - 1]


  if (previous === 0) {

    return null

  }


  const percentage =

    ((current - previous) / previous) * 100


  return {

    value:

      Math.abs(percentage).toFixed(0),

    up:

      percentage >= 0

  }

}


function fmt(
  value: number | null | undefined
) {
  if (value === null || value === undefined) {
    return "-"
  }
  return new Intl.NumberFormat(
    "id-ID",
    { maximumFractionDigits: 0 }
  ).format(value)
}

// Persentase perubahan current vs previous
function pctChange(
  current: number | null | undefined,
  previous: number | null | undefined
) {
  if (
    current === null || current === undefined ||
    previous === null || previous === undefined ||
    previous === 0
  ) {
    return null
  }
  const pct = ((current - previous) / previous) * 100
  return {
    value: Math.abs(pct).toFixed(0),
    up: pct >= 0
  }
}

// =====================================================
// KARTU STAT KECIL (dipakai di modal)
// =====================================================

type Tone = "blue" | "red" | "green" | "purple" | "amber" | "slate"

const TONE: Record<Tone, string> = {
  blue: "bg-blue-100 text-blue-600",
  red: "bg-red-100 text-red-500",
  green: "bg-emerald-100 text-emerald-600",
  purple: "bg-violet-100 text-violet-600",
  amber: "bg-amber-100 text-amber-600",
  slate: "bg-slate-100 text-slate-600"
}

function StatCard({
  icon,
  tone,
  label,
  value,
  unit,
  valueClass,
  change,
  note,
  noteClass
}: {
  icon: React.ReactNode
  tone: Tone
  label: string
  value: string
  unit?: string
  valueClass?: string
  change?: { value: string; up: boolean } | null
  note?: string
  noteClass?: string
}) {
  return (
    <div className="rounded-xl border border-white/70 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-3">
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${TONE[tone]}`}
        >
          {icon}
        </div>
        <p className="text-xs font-semibold text-slate-700">
          {label}
        </p>
      </div>

      <div className="mt-3 flex items-baseline gap-1.5">
        <span
          className={`text-2xl font-bold ${valueClass ?? "text-slate-900"}`}
        >
          {value}
        </span>
        {unit && (
          <span className="text-sm font-medium text-slate-500">
            {unit}
          </span>
        )}
      </div>

      {change && (
        <p
          className={`mt-1 text-xs font-semibold ${
            change.up ? "text-emerald-600" : "text-red-500"
          }`}
        >
          {change.up ? "▲" : "▼"} {change.value}%{" "}
          <span className="font-normal text-slate-500">
            dari periode sebelumnya
          </span>
        </p>
      )}

      {note && (
        <p
          className={`mt-1 text-xs ${noteClass ?? "text-slate-500"}`}
        >
          {note}
        </p>
      )}
    </div>
  )
}

// =====================================================
// CONDITION ANALYSIS
// =====================================================


function getConditionAnalysis(

  row: ForecastItem

) {

  const result: string[] = []


  if (

    (row.Stock ?? 0)

    <

    (row.Forecast_GI ?? 0)

  ) {

    result.push(

      "Stock saat ini lebih kecil dibanding kebutuhan GI periode berikutnya."

    )

  }


  if (

    (row.Projected_Stock ?? 0)

    <

    0

  ) {

    result.push(

      "Proyeksi stock menunjukkan potensi kekurangan material."

    )

  }


  if (

    (row.Gap_Kebutuhan ?? 0)

    >

    0

  ) {

    result.push(

      `Terdapat kebutuhan tambahan sebesar ${row.Gap_Kebutuhan}.`

    )

  }


  const giChange =

    getTrendChange(row.Trend_GI)


  if (giChange) {

    result.push(

      `Trend GI ${
        Number(giChange) >= 0
        ?
        "naik"
        :
        "turun"
      }
      ${Math.abs(Number(giChange))}%
      dibanding periode sebelumnya.`

    )

  }


  const grChange =

    getTrendChange(row.Trend_GR)


  if (grChange) {

    result.push(

      `Trend GR ${
        Number(grChange) >= 0
        ?
        "naik"
        :
        "turun"
      }
      ${Math.abs(Number(grChange))}%
      dibanding periode sebelumnya.`

    )

  }


  if (result.length === 0) {

    result.push(

      "Kondisi inventory relatif stabil berdasarkan data aktual dan proyeksi."

    )

  }


  return result

}


// =====================================================
// COMPONENT
// =====================================================


export default function DataTable({

  data,

  currentPage,

  onPageChange

}: DataTableProps) {


  const [selectedRow, setSelectedRow]

    =

    useState<ForecastItem | null>(null)


  const [isModalOpen, setIsModalOpen]

    =

    useState(false)


  // =====================================================
  // FORMAT HELPER
  // =====================================================

  const itemsPerPage = 10


  function formatNumber(

    value: number | null | undefined

  ) {

    if (

      value === null ||

      value === undefined

    ) {

      return "-"

    }

    return new Intl.NumberFormat(

      "id-ID",

      {

        maximumFractionDigits: 0

      }

    )

      .format(value)

  }


  function formatCoverage(

    value: number | null | undefined

  ) {

    if (

      value === null ||

      value === undefined

    ) {

      return "-"

    }

    return value.toFixed(2)

  }


  function statusStyle(

    status: string | null | undefined

  ) {

    switch (status) {

      case "Aman":
      case "Normal":
        return "bg-green-100 text-green-700 border-green-300"

      case "Kritis":
      case "Warning":
        return "bg-yellow-100 text-yellow-700 border-yellow-300"

      case "Reorder":
      case "Stock Out Risk":
        return "bg-red-100 text-red-700 border-red-300"

      case "Overstock Risk":
        return "bg-blue-100 text-blue-700 border-blue-300"

      default:
        return "bg-slate-100 text-slate-500 border-slate-300"

    }

  }


  // =====================================================
  // PAGINATION DATA
  // =====================================================

  const processedData = data.map(

    (row) => (

      {

        ...row,

        Coverage:
          row.Coverage ?? null,

        Status:
          row.Status ?? null,

        Has_GI:
          row.Has_GI ?? false,

        Has_GR:
          row.Has_GR ?? false,

        // "Ada stok" = terdaftar di file stok DAN jumlahnya > 0
        // (disamakan dengan syarat filter GI + GR + Stock di page.tsx)
        Has_Stock:
          (row.Has_Stock ?? false) &&
          Number(row.Stock ?? 0) > 0,

        History_Count:
          row.History_Count ?? 0

      }

    )

  )


  const totalPages = Math.ceil(

    processedData.length /

    itemsPerPage

  )


  const startIndex =

    (currentPage - 1)

    *

    itemsPerPage


  const currentData =

    processedData.slice(

      startIndex,

      startIndex + itemsPerPage

    )


  function openDetail(

    row: ForecastItem

  ) {

    setSelectedRow(row)

    setIsModalOpen(true)

  }


  function closeDetail() {

    setSelectedRow(null)

    setIsModalOpen(false)

  }


  // =====================================================
  // RETURN
  // =====================================================


  return (

    <div className="w-full">


      {/* =====================================================
      TABLE CONTAINER
      ===================================================== */}


      <div

        className="
        overflow-x-auto
        rounded-2xl
        border
        border-gray-200
        bg-white
        shadow-xl
        "

      >

        <table

          className="
          min-w-[1400px]
          w-full
          "

        >

          <thead>

            <tr

              className="
              bg-[#102A57]
              text-sm
              text-white
              "

            >

              <th className="px-4 py-4 text-center">
                No
              </th>

              <th className="px-4 py-4 text-left">
                Material
              </th>

              <th className="px-4 py-4 text-left">
                Deskripsi Material
              </th>

              <th className="px-4 py-4 text-center">
                Availability
              </th>

              <th className="px-4 py-4 text-right">
                Stock Saat Ini
              </th>

              <th className="px-4 py-4 text-right">
                GI Aktual
              </th>

              <th className="px-4 py-4 text-right">
                GR Aktual
              </th>

              <th className="px-4 py-4 text-right">
                Forecast GI
              </th>

              <th className="px-4 py-4 text-right">
                Forecast GR
              </th>

              <th className="px-4 py-4 text-center">
                Coverage
              </th>

              <th className="px-4 py-4 text-center">
                Status
              </th>

              <th className="px-4 py-4 text-center">
                Aksi
              </th>

            </tr>

          </thead>


          <tbody>

            {

              currentData.map(

                (row, index) => (

                  <tr

                    key={`${row.Material}-${index}`}

                    className="
                    border-b
                    border-gray-100
                    text-sm
                    text-gray-700
                    hover:bg-blue-50
                    "

                  >

                    <td className="px-4 py-5 text-center">
                      {startIndex + index + 1}
                    </td>

                    <td className="px-4 py-5 font-semibold">
                      {row.Material ?? "-"}
                    </td>

                    <td className="px-4 py-5">
                      {row["Material Description"] ?? "-"}
                    </td>

                    <td className="px-4 py-5 text-center">

                      <div className="flex flex-col gap-1 text-xs">

                        <span

                          className={
                            row.Has_GI
                              ?
                              "text-green-600"
                              :
                              "text-gray-400"
                          }

                        >
                          GI {row.Has_GI ? "✓" : "-"}
                        </span>

                        <span

                          className={
                            row.Has_GR
                              ?
                              "text-green-600"
                              :
                              "text-gray-400"
                          }

                        >
                          GR {row.Has_GR ? "✓" : "-"}
                        </span>

                        <span

                          className={
                            row.Has_Stock
                              ?
                              "text-green-600"
                              :
                              "text-gray-400"
                          }

                        >
                          Stock {row.Has_Stock ? "✓" : "-"}
                        </span>

                      </div>

                    </td>

                    <td className="px-4 py-5 text-right">
                      {formatNumber(row.Stock)}
                    </td>

                    <td className="px-4 py-5 text-right">
                      {formatNumber(row.GI_Actual)}
                    </td>

                    <td className="px-4 py-5 text-right">
                      {formatNumber(row.GR_Actual)}
                    </td>

                    <td className="px-4 py-5 text-right">
                      {formatNumber(row.Forecast_GI)}
                    </td>

                    <td className="px-4 py-5 text-right">
                      {formatNumber(row.Forecast_GR)}
                    </td>

                    <td className="px-4 py-5 text-center">
                      {formatCoverage(row.Coverage)}
                    </td>

                    <td className="px-4 py-5 text-center">

                      <span

                        className={`
                        rounded-full
                        border
                        px-3
                        py-1
                        text-xs
                        font-semibold
                        ${statusStyle(row.Status)}
                        `}

                      >
                        {row.Status ?? "-"}
                      </span>

                    </td>

                    <td className="px-4 py-5 text-center">

                      <button

                        type="button"

                        onClick={() => openDetail(row)}

                        className="
                        rounded-xl
                        bg-blue-600
                        p-2
                        text-white
                        hover:bg-blue-700
                        "

                      >
                        <Eye className="h-4 w-4" />
                      </button>

                    </td>

                  </tr>

                )

              )

            }

          </tbody>

        </table>

      </div>


      {/* =====================================================
      PAGINATION BAR
      ===================================================== */}


      <div

        className="
        flex
        items-center
        justify-between
        px-4
        py-3
        "

      >

        <p className="text-sm text-slate-500">

          Menampilkan{" "}

          <span className="font-semibold text-slate-700">
            {
              processedData.length === 0
                ?
                0
                :
                startIndex + 1
            }
          </span>

          {" "}-{" "}

          <span className="font-semibold text-slate-700">
            {
              Math.min(
                startIndex + itemsPerPage,
                processedData.length
              )
            }
          </span>

          {" "}dari{" "}

          <span className="font-semibold text-slate-700">
            {processedData.length}
          </span>

          {" "}data

        </p>


        <div className="flex items-center gap-2">

          <button

            type="button"

            disabled={currentPage <= 1}

            onClick={() => onPageChange(currentPage - 1)}

            className="
            rounded-lg
            border
            border-gray-300
            bg-white
            px-3
            py-1.5
            text-sm
            font-medium
            text-slate-700
            hover:bg-gray-100
            disabled:opacity-50
            "

          >
            Sebelumnya
          </button>

          <span className="px-2 text-sm text-slate-600">

            Halaman{" "}

            <span className="font-semibold text-slate-800">
              {currentPage}
            </span>

            {" "}dari{" "}

            <span className="font-semibold text-slate-800">
              {totalPages}
            </span>

          </span>

          <button

            type="button"

            disabled={currentPage >= totalPages}

            onClick={() => onPageChange(currentPage + 1)}

            className="
            rounded-lg
            border
            border-gray-300
            bg-white
            px-3
            py-1.5
            text-sm
            font-medium
            text-slate-700
            hover:bg-gray-100
            disabled:opacity-50
            "

          >
            Selanjutnya
          </button>

        </div>

      </div>


      {/* =====================================================
      MODAL DETAIL
      ===================================================== */}


      {

        isModalOpen && selectedRow && (

          <div

            className="
            fixed
            inset-0
            z-[999]
            flex
            items-center
            justify-center
            bg-black/40
            backdrop-blur-sm
            "

          >

            <div

              className="
              max-h-[90vh]
              w-full
              max-w-7xl
              overflow-y-auto
              rounded-2xl
              bg-white
              p-6
              shadow-2xl
              "

            >

              {/* HEADER */}

              <div

                className="
                mb-6
                flex
                items-start
                justify-between
                "

              >

                <div>

                  <h2

                    className="
                    text-xl
                    font-bold
                    text-slate-900
                    "

                  >
                    Analisis Material
                  </h2>

                  <p className="text-sm text-slate-600">
                    {selectedRow.Material}
                  </p>

                  <p className="text-sm text-slate-600">
                    {selectedRow["Material Description"]}
                  </p>

                </div>

                <button

                  type="button"

                  onClick={closeDetail}

                  className="
                  rounded-lg
                  p-2
                  text-slate-500
                  hover:bg-gray-100
                  "

                >
                  <X className="h-5 w-5" />
                </button>

              </div>


              {/* =====================================================
              DATA AKTUAL (PERIODE TERAKHIR)
              ===================================================== */}
              {(() => {
                const r = selectedRow
                const lastGI = r.Trend_GI?.[r.Trend_GI.length - 1]
                const prevGI = r.Trend_GI?.[r.Trend_GI.length - 2]
                const lastGR = r.Trend_GR?.[r.Trend_GR.length - 1]
                const prevGR = r.Trend_GR?.[r.Trend_GR.length - 2]

                const net =
                  r.Net_Movement ??
                  ((r.GR_Actual ?? 0) - (r.GI_Actual ?? 0))

                const netLabel =
                  net < 0 ? "Stok berkurang"
                  : net > 0 ? "Stok bertambah"
                  : "Balance"

                const netClass =
                  net < 0 ? "text-red-500"
                  : net > 0 ? "text-emerald-600"
                  : "text-slate-500"

                return (
                  <div className="mt-2 rounded-2xl border border-blue-100 bg-blue-50/60 p-4">
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Database className="h-4 w-4 text-blue-600" />
                        <h3 className="text-sm font-bold text-blue-700">
                          Data Aktual (Periode Terakhir)
                        </h3>
                      </div>
                      <p className="text-xs text-slate-500">
                        Berdasarkan transaksi aktual pada periode terakhir
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                      <StatCard
                        icon={<Package className="h-5 w-5" />}
                        tone="blue"
                        label="Stok Saat Ini"
                        value={fmt(r.Stock)}
                        unit={r.Unit || undefined}
                        note="Stok aktual di gudang"
                      />
                      <StatCard
                        icon={<ArrowUpFromLine className="h-5 w-5" />}
                        tone="red"
                        label="GI Aktual"
                        value={fmt(r.GI_Actual)}
                        unit={r.Unit || undefined}
                        change={pctChange(lastGI, prevGI)}
                      />
                      <StatCard
                        icon={<ArrowDownToLine className="h-5 w-5" />}
                        tone="green"
                        label="GR Aktual"
                        value={fmt(r.GR_Actual)}
                        unit={r.Unit || undefined}
                        change={pctChange(lastGR, prevGR)}
                      />
                      <StatCard
                        icon={<ArrowLeftRight className="h-5 w-5" />}
                        tone="purple"
                        label="Net Movement"
                        value={fmt(net)}
                        unit={r.Unit || undefined}
                        valueClass={netClass}
                        note={`GR − GI · ${netLabel}`}
                        noteClass={netClass}
                      />
                    </div>
                  </div>
                )
              })()}

              {/* =====================================================
              FORECAST (PERIODE BERIKUTNYA)
              ===================================================== */}
              {(() => {
                const r = selectedRow
                const lastGI = r.Trend_GI?.[r.Trend_GI.length - 1]
                const lastGR = r.Trend_GR?.[r.Trend_GR.length - 1]

                // Projected_Stock dihitung di backend:
                // Stok Terkini + Forecast GR - Forecast GI
                const projected = r.Projected_Stock
                const gap = r.Gap_Kebutuhan ?? 0
                const negative = (projected ?? 0) < 0

                return (
                  <div className="mt-4 rounded-2xl border border-violet-100 bg-violet-50/60 p-4">
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <BarChart3 className="h-4 w-4 text-violet-600" />
                        <h3 className="text-sm font-bold text-violet-700">
                          Forecast (Periode Berikutnya)
                        </h3>
                      </div>
                      <p className="text-xs text-slate-500">
                        Hasil peramalan berdasarkan pola historis
                        pemakaian dan penerimaan material
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                      <StatCard
                        icon={<ArrowUpFromLine className="h-5 w-5" />}
                        tone="red"
                        label="Forecast GI"
                        value={fmt(r.Forecast_GI)}
                        unit={r.Unit || undefined}
                        change={pctChange(r.Forecast_GI, lastGI)}
                      />
                      <StatCard
                        icon={<ArrowDownToLine className="h-5 w-5" />}
                        tone="green"
                        label="Forecast GR"
                        value={fmt(r.Forecast_GR)}
                        unit={r.Unit || undefined}
                        change={pctChange(r.Forecast_GR, lastGR)}
                      />
                      <StatCard
                        icon={<TrendingUp className="h-5 w-5" />}
                        tone="purple"
                        label="Projected Stock"
                        value={fmt(projected)}
                        unit={r.Unit || undefined}
                        valueClass={negative ? "text-red-500" : "text-slate-900"}
                        note="Stok Terkini + Forecast GR − Forecast GI"
                      />
                      <StatCard
                        icon={<Scale className="h-5 w-5" />}
                        tone="amber"
                        label="Gap Kebutuhan"
                        value={fmt(gap)}
                        unit={r.Unit || undefined}
                        valueClass={gap > 0 ? "text-red-500" : "text-emerald-600"}
                        note={
                          gap > 0
                            ? "Estimasi kebutuhan tambahan"
                            : "Tidak ada kebutuhan tambahan"
                        }
                      />
                    </div>
                  </div>
                )
              })()}

              {/* =====================================================
              TREND CHART
              ===================================================== */}


              <div className="mt-6">

                <TrendDetailChart

                  trendGI={selectedRow.Trend_GI}

                  trendGR={selectedRow.Trend_GR}

                  forecastGI={selectedRow.Forecast_GI}

                  forecastGR={selectedRow.Forecast_GR}

                  trendDate={selectedRow.Trend_Date}
                  forecastDate={selectedRow.Forecast_Bulan}

                />

              </div>


              {/* ANALISIS MATERIAL (7 kartu) */}
              <MaterialAnalysisCard row={selectedRow} unit={selectedRow.Unit ?? ""} />

            </div>

          </div>

        )

      }

    </div>

  )

}
