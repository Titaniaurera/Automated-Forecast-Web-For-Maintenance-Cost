// ============================================================
// FORECAST DATA LAYER - JASA
// ============================================================

export type JasaBreakdown = {
  nama: string
  jenis: "RUTIN" | "NON RUTIN" | "OVH"
  realisasi: number
  forecast: number
}


// ============================================================
// MONTH POINT
// ============================================================

export type MonthPoint = {
  /** YYYY-MM */
  key: string

  /** Contoh: "Mei 2026" */
  label: string

  // ----------------------------------------------------------
  // TOTAL
  // ----------------------------------------------------------

  /** Total aktual Rutin + Non Rutin/OVH */
  actual: number | null

  /** Total forecast Rutin + Non Rutin/OVH */
  forecast: number | null

  // ----------------------------------------------------------
  // RUTIN
  // ----------------------------------------------------------

  rutinActual: number
  rutinForecast: number

  // ----------------------------------------------------------
  // NON RUTIN + OVH
  // ----------------------------------------------------------

  nonRutinActual: number
  nonRutinForecast: number

  // ----------------------------------------------------------
  // RINCIAN
  // ----------------------------------------------------------

  jasa: JasaBreakdown[]
}


// ============================================================
// FORECAST RESPONSE
// ============================================================

export type ForecastResponse = {
  sourceFile: string
  mode: string

  forecastMonthKey: string
  forecastMonthLabel: string

  previousMonthLabel: string

  totalForecast: number
  rutinForecast: number
  nonRutinForecast: number

  totalChangePct: number
  rutinChangePct: number

  series: MonthPoint[]
}


// ============================================================
// FORMAT RUPIAH
// ============================================================

export function formatRupiah(
  value: number | null | undefined
): string {

  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0,
  }).format(Number(value ?? 0))
}


// ============================================================
// FORMAT COMPACT RUPIAH
// ============================================================

export function formatCompactRupiah(
  value: number | null | undefined
): string {

  const number = Number(value ?? 0)

  if (number >= 1_000_000_000) {
    return `Rp ${(number / 1_000_000_000).toFixed(2)} M`
  }

  if (number >= 1_000_000) {
    return `Rp ${(number / 1_000_000).toFixed(0)} jt`
  }

  if (number >= 1_000) {
    return `Rp ${(number / 1_000).toFixed(0)} rb`
  }

  return `Rp ${number}`
}


// ============================================================
// FORMAT BULAN
// ============================================================

function formatMonthLabel(
  period: string
): string {

  const [year, month] =
    period.split("-").map(Number)

  const date =
    new Date(year, month - 1, 1)

  return new Intl.DateTimeFormat(
    "id-ID",
    {
      month: "short",
      year: "numeric",
    }
  ).format(date)
}


// ============================================================
// HITUNG PERUBAHAN
// ============================================================

function calculateChangePct(
  current: number,
  previous: number
): number {

  if (!previous) {
    return 0
  }

  return Number(
    (
      ((current - previous) /
        Math.abs(previous)) *
      100
    ).toFixed(1)
  )
}


// ============================================================
// TIPE RESPONSE BACKEND
// ============================================================

type BackendSeriesPoint = {
  period: string
  actual?: number | null
  forecast?: number | null
}


type BackendContributor = {
  short_text: string
  amount: number
  percentage: number
}


type BackendResponse = {
  status: string

  forecast_month: string
  forecast_month_label: string

  total_forecast: number

  rutin: {
    forecast: number
    model?: string | null
    metrics?: Record<string, number>
    historical?: BackendSeriesPoint[]
    series?: BackendSeriesPoint[]
    contributors?: BackendContributor[]
  }

  non_rutin_ovh?: {
    forecast: number
    model?: string | null
    metrics?: Record<string, number>
    historical?: BackendSeriesPoint[]
    series?: BackendSeriesPoint[]
    contributors?: BackendContributor[]
  }

  historical?: BackendSeriesPoint[]

  series?: BackendSeriesPoint[]

  contributors?: BackendContributor[]
}


// ============================================================
// NORMALIZE RESPONSE
// RUTIN + NON RUTIN + OVH
// ============================================================

export function normalizeForecastResponse(
  response: BackendResponse
): ForecastResponse {

  // ==========================================================
  // 1. AMBIL SERIES RUTIN
  // ==========================================================

  const rutinSeries =
    response.rutin?.series ??
    response.rutin?.historical ??
    []


  // ==========================================================
  // 2. AMBIL SERIES NON RUTIN + OVH
  // ==========================================================

  const nonRutinSeries =
    response.non_rutin_ovh?.series ??
    response.non_rutin_ovh?.historical ??
    []


  // ==========================================================
  // 3. CONTRIBUTORS
  // ==========================================================

  const rutinContributors =
    response.rutin?.contributors ??
    []


  const nonRutinContributors =
    response.non_rutin_ovh?.contributors ??
    []


  // ==========================================================
  // 4. BUAT MAP PER BULAN
  // ==========================================================

  const periodMap =
    new Map<
      string,
      {
        rutinActual: number
        rutinForecast: number

        nonRutinActual: number
        nonRutinForecast: number
      }
    >()


  // ==========================================================
  // 5. MASUKKAN DATA RUTIN
  // ==========================================================

  for (const point of rutinSeries) {

    if (!periodMap.has(point.period)) {

      periodMap.set(
        point.period,
        {
          rutinActual: 0,
          rutinForecast: 0,
          nonRutinActual: 0,
          nonRutinForecast: 0,
        }
      )
    }

    const item =
      periodMap.get(point.period)!

    if (point.actual != null) {

      item.rutinActual +=
        Number(point.actual) || 0

    }

    if (point.forecast != null) {

      item.rutinForecast +=
        Number(point.forecast) || 0

    }
  }


  // ==========================================================
  // 6. MASUKKAN DATA NON RUTIN + OVH
  // ==========================================================

  for (const point of nonRutinSeries) {

    if (!periodMap.has(point.period)) {

      periodMap.set(
        point.period,
        {
          rutinActual: 0,
          rutinForecast: 0,
          nonRutinActual: 0,
          nonRutinForecast: 0,
        }
      )
    }

    const item =
      periodMap.get(point.period)!

    if (point.actual != null) {

      item.nonRutinActual +=
        Number(point.actual) || 0

    }

    if (point.forecast != null) {

      item.nonRutinForecast +=
        Number(point.forecast) || 0

    }
  }


  // ==========================================================
  // 7. PASTIKAN FORECAST MONTH ADA
  // ==========================================================

  if (
    response.forecast_month &&
    !periodMap.has(
      response.forecast_month
    )
  ) {

    periodMap.set(
      response.forecast_month,
      {
        rutinActual: 0,
        rutinForecast:
          Number(
            response.rutin?.forecast
          ) || 0,

        nonRutinActual: 0,
        nonRutinForecast:
          Number(
            response.non_rutin_ovh?.forecast
          ) || 0,
      }
    )
  }


  // ==========================================================
  // 8. SORT BULAN
  // ==========================================================

  const sortedPeriods =
    Array.from(
      periodMap.keys()
    ).sort()


  // ==========================================================
  // 9. BUAT SERIES UNTUK UI
  // ==========================================================

  const series: MonthPoint[] =
    sortedPeriods.map(
      (period) => {

        const item =
          periodMap.get(period)!

        const isForecast =
          period ===
          response.forecast_month


        const totalActual =
          item.rutinActual +
          item.nonRutinActual


        const totalForecast =
          item.rutinForecast +
          item.nonRutinForecast


        // ----------------------------------------------------
        // RINCIAN JASA
        // ----------------------------------------------------

        const jasa: JasaBreakdown[] = []


        // RUTIN CONTRIBUTORS

        if (
          isForecast &&
          item.rutinForecast > 0
        ) {

          for (
            const contributor
            of rutinContributors
          ) {

            jasa.push({

              nama:
                contributor.short_text,

              jenis:
                "RUTIN",

              realisasi:
                0,

              forecast:
                Number(
                  contributor.amount
                ) || 0,

            })
          }
        }


        // NON RUTIN + OVH CONTRIBUTORS

        if (
          isForecast &&
          item.nonRutinForecast > 0
        ) {

          for (
            const contributor
            of nonRutinContributors
          ) {

            jasa.push({

              nama:
                contributor.short_text,

              jenis:
                "NON RUTIN",

              realisasi:
                0,

              forecast:
                Number(
                  contributor.amount
                ) || 0,

            })
          }
        }


        // ----------------------------------------------------
        // RETURN MONTH POINT
        // ----------------------------------------------------

        return {

          key:
            period,

          label:
            formatMonthLabel(
              period
            ),

          actual:
            isForecast
              ? null
              : totalActual > 0
                ? totalActual
                : null,

          forecast:
            isForecast
              ? totalForecast
              : null,

          rutinActual:
            item.rutinActual,

          rutinForecast:
            item.rutinForecast,

          nonRutinActual:
            item.nonRutinActual,

          nonRutinForecast:
            item.nonRutinForecast,

          jasa,

        }
      }
    )


  // ==========================================================
  // 10. AKTUAL TERAKHIR
  // ==========================================================

  const actualPoints =
    series.filter(
      (point) =>
        point.actual != null
    )


  const currentActual =
    actualPoints.length >= 1
      ? Number(
          actualPoints[
            actualPoints.length - 1
          ].actual
        )
      : 0


  const previousActual =
    actualPoints.length >= 2
      ? Number(
          actualPoints[
            actualPoints.length - 2
          ].actual
        )
      : 0


  const previousMonthLabel =
    actualPoints.length >= 2
      ? actualPoints[
          actualPoints.length - 2
        ].label
      : "bulan sebelumnya"


  // ==========================================================
  // 11. TOTAL CHANGE
  // ==========================================================

  const totalChangePct =
    calculateChangePct(
      currentActual,
      previousActual
    )


  // ==========================================================
  // 12. RUTIN CHANGE
  // ==========================================================

  const rutinActualPoints =
    series.filter(
      (point) =>
        point.rutinActual > 0
    )


  const currentRutin =
    rutinActualPoints.length >= 1
      ? rutinActualPoints[
          rutinActualPoints.length - 1
        ].rutinActual
      : 0


  const previousRutin =
    rutinActualPoints.length >= 2
      ? rutinActualPoints[
          rutinActualPoints.length - 2
        ].rutinActual
      : 0


  const rutinChangePct =
    calculateChangePct(
      currentRutin,
      previousRutin
    )


  // ==========================================================
  // 13. RETURN
  // ==========================================================

  return {

    sourceFile:
      "MySQL • data_jasa",

    mode:
      "Forecast bulan depan otomatis",

    forecastMonthKey:
      response.forecast_month,

    forecastMonthLabel:
      response.forecast_month_label,

    previousMonthLabel,

    totalForecast:
      Number(
        response.total_forecast
      ) || 0,

    rutinForecast:
      Number(
        response.rutin?.forecast
      ) || 0,

    nonRutinForecast:
      Number(
        response.non_rutin_ovh?.forecast
      ) || 0,

    totalChangePct,

    rutinChangePct,

    series,

  }
}