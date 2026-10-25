"use client"

// =====================================================
// TYPE
// =====================================================

interface TrendDetailChartProps {

  trendGI?: number[]

  trendGR?: number[]

  forecastGI?: number | null

  forecastGR?: number | null

  // Bulan asli dari data
  //
  // Contoh:
  //
  // [
  //   "2023-03",
  //   "2023-04",
  //   "2023-05"
  // ]
  //
  // atau:
  //
  // [
  //   "2023-03-01",
  //   "2023-04-01",
  //   "2023-05-01"
  // ]

  trendDate?: string[]

  // Bulan target forecast
  //
  // Contoh:
  // "2023-06"
  //
  // Kalau kosong, otomatis dihitung:
  // bulan terakhir + 1 bulan

  forecastDate?: string

}


interface ChartPoint {

  x: number

  y: number

  value: number

}


// =====================================================
// HELPER : NAMA BULAN
// =====================================================

const NAMA_BULAN = [

  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "Mei",
  "Jun",
  "Jul",
  "Agu",
  "Sep",
  "Okt",
  "Nov",
  "Des"

]


// =====================================================
// HELPER : REGEX TAHUN-BULAN
// =====================================================

// Cocok untuk:
//
// "2023-03"
//
// maupun:
//
// "2023-03-01"

const YM_REGEX = /^(\d{4})-(\d{1,2})/


// =====================================================
// HELPER : FORMAT BULAN
// =====================================================

// "2023-03"
//       ↓
// "Mar 2023"
//
// "2023-03-01"
//       ↓
// "Mar 2023"
//
// Sengaja TIDAK memakai new Date()
// supaya tidak bergeser karena timezone.

function formatBulan(

  value: string

): string {

  const match = YM_REGEX.exec(value)

  if (match) {

    const monthIndex = Number(match[2]) - 1

    if (

      monthIndex >= 0

      &&

      monthIndex < 12

    ) {

      return `${NAMA_BULAN[monthIndex]} ${match[1]}`

    }

  }

  return value

}


// =====================================================
// HELPER : BULAN BERIKUTNYA
// =====================================================

// "2023-12"
//       ↓
// "2024-01"
//
// "2023-05"
//       ↓
// "2023-06"

function nextMonth(

  value: string

): string | null {

  const match = YM_REGEX.exec(value)

  if (!match) {

    return null

  }

  const year = Number(match[1])

  const month = Number(match[2])

  if (month >= 12) {

    return `${year + 1}-01`

  }

  return `${year}-${String(month + 1).padStart(2, "0")}`

}


// =====================================================
// HELPER : FORMAT ANGKA
// =====================================================

// Contoh:
//
// 1000
// ↓
// 1.000
//
// 1500000
// ↓
// 1.500.000

function formatNumber(

  value: number

): string {

  return value.toLocaleString(

    "id-ID",

    {

      maximumFractionDigits: 0

    }

  )

}


// =====================================================
// HELPER : INTERVAL SUMBU Y
// =====================================================
//
// Menentukan interval angka sumbu Y
// berdasarkan nilai maksimum material.
//
// Contoh:
//
// max = 8
//      -> 2
//
// max = 1.850
//      -> 500
//
// max = 30.380
//      -> 10.000
//
// max = 194.087
//      -> 50.000

function getNiceStep(

  maxValue: number

): number {

  if (maxValue <= 0) {

    return 1

  }

  // Target sekitar 5 interval

  const roughStep = maxValue / 5

  const magnitude =

    Math.pow(

      10,

      Math.floor(

        Math.log10(roughStep)

      )

    )

  const normalized =

    roughStep / magnitude

  let niceNormalized: number

  if (normalized <= 1) {

    niceNormalized = 1

  }

  else if (normalized <= 2) {

    niceNormalized = 2

  }

  else if (normalized <= 5) {

    niceNormalized = 5

  }

  else {

    niceNormalized = 10

  }

  return niceNormalized * magnitude

}


// =====================================================
// COMPONENT
// =====================================================

export default function TrendDetailChart({

  trendGI = [],

  trendGR = [],

  forecastGI,

  forecastGR,

  trendDate = [],

  forecastDate

}: TrendDetailChartProps) {


  // =====================================================
  // CHECK FORECAST
  // =====================================================

  const hasForecast =

    (

      forecastGI !== null

      &&

      forecastGI !== undefined

    )

    ||

    (

      forecastGR !== null

      &&

      forecastGR !== undefined

    )


  // =====================================================
  // CHECK DATA
  // =====================================================

  if (

    trendGI.length === 0

    &&

    trendGR.length === 0

    &&

    !hasForecast

  ) {

    return (

      <div

        className="
          rounded-xl
          border
          border-slate-200
          bg-white
          p-5
          text-center
          text-sm
          text-slate-500
        "

      >

        Data trend belum tersedia

      </div>

    )

  }


  // =====================================================
  // SVG CONFIG
  // =====================================================

  const width = 850

  const height = 350

  // Ruang kiri diperbesar
  // agar angka sumbu Y tidak terpotong.

  const paddingLeft = 90

  const paddingRight = 50

  const paddingTop = 40

  const paddingBottom = 65


  // =====================================================
  // LABEL BULAN
  // =====================================================

  const actualCount = Math.max(

    trendGI.length,

    trendGR.length,

    trendDate.length

  )


  const labels: string[] = Array.from(

    {

      length: actualCount

    },

    (_, index) =>

      trendDate[index]

        ? formatBulan(

            trendDate[index]

          )

        : `Periode ${index + 1}`

  )


  // =====================================================
  // LABEL FORECAST
  // =====================================================

  const lastDate =

    trendDate.length

      ? trendDate[

          trendDate.length - 1

        ]

      : null


  const forecastRaw =

    forecastDate

    ||

    (

      lastDate

        ? nextMonth(lastDate)

        : null

    )


  const forecastLabel =

    forecastRaw

      ? formatBulan(forecastRaw)

      : "Forecast"


  // =====================================================
  // SLOT SUMBU X
  // =====================================================

  const slotCount =

    actualCount +

    (

      hasForecast

        ? 1

        : 0

    )


  const stepX =

    (

      width

      - paddingLeft

      - paddingRight

    )

    /

    Math.max(

      slotCount - 1,

      1

    )


  // =====================================================
  // GET X POSITION
  // =====================================================

  function getX(

    slot: number

  ) {

    return (

      paddingLeft

      +

      slot * stepX

    )

  }


  // =====================================================
  // SEMUA NILAI
  // =====================================================
  //
  // Semua nilai aktual dan forecast
  // digunakan untuk menentukan skala Y.
  //
  // TIDAK ada lagi angka minimum 100.
  //
  // Jadi setiap material mempunyai
  // skala berdasarkan nilainya sendiri.

  const allValues = [

    ...trendGI,

    ...trendGR,

    ...(

      forecastGI !== null

      &&

      forecastGI !== undefined

        ? [forecastGI]

        : []

    ),

    ...(

      forecastGR !== null

      &&

      forecastGR !== undefined

        ? [forecastGR]

        : []

    )

  ]


  // =====================================================
  // NILAI MAKSIMUM DATA
  // =====================================================

  const rawMaxValue =

    allValues.length > 0

      ? Math.max(

          ...allValues

        )

      : 0


  // =====================================================
  // INTERVAL SUMBU Y
  // =====================================================

  const yStep =

    getNiceStep(

      rawMaxValue

    )


  // =====================================================
  // MAKSIMUM SUMBU Y
  // =====================================================
  //
  // Contoh:
  //
  // rawMax = 30.380
  // yStep   = 10.000
  //
  // maxValue = 40.000
  //
  // Maka sumbu:
  //
  // 0
  // 10.000
  // 20.000
  // 30.000
  // 40.000

  const maxValue =

    rawMaxValue > 0

      ? Math.ceil(

          rawMaxValue /

          yStep

        ) * yStep

      : yStep


  // =====================================================
  // Y AXIS TICKS
  // =====================================================

  const yTicks: number[] = []


  for (

    let value = 0;

    value <= maxValue;

    value += yStep

  ) {

    yTicks.push(value)

  }


  // =====================================================
  // Y POSITION
  // =====================================================

  function getY(

    value: number

  ) {

    return (

      height

      - paddingBottom

      -

      (

        value /

        maxValue

      )

      *

      (

        height

        - paddingTop

        - paddingBottom

      )

    )

  }


  // =====================================================
  // CREATE POINT
  // =====================================================
  //
  // Data diratakan ke kanan / bulan terakhir.
  //
  // Contoh:
  //
  // actualCount = 6
  //
  // GI = 6 data
  // offset = 0
  //
  // GR = 4 data
  // offset = 2
  //
  // GR ditempatkan pada 4 bulan terakhir.

  function createPoints(

    data: number[]

  ): ChartPoint[] {

    const offset =

      actualCount -

      data.length


    return data.map(

      (value, index) => {

        const x = getX(

          index +

          offset

        )

        const y = getY(

          value

        )

        return {

          x,

          y,

          value

        }

      }

    )

  }


  // =====================================================
  // CREATE LINE PATH
  // =====================================================

  function createLine(

    points: ChartPoint[]

  ) {

    return points

      .map(

        (point, index) =>

          `${

            index === 0

              ? "M"

              : "L"

          } ${point.x} ${point.y}`

      )

      .join(" ")

  }


  // =====================================================
  // CREATE POINT DATA
  // =====================================================

  const giPoints =

    createPoints(

      trendGI

    )


  const grPoints =

    createPoints(

      trendGR

    )


  // =====================================================
  // FORECAST POSITION
  // =====================================================

  const forecastX =

    getX(

      actualCount

    )


  // =====================================================
  // LAST ACTUAL POINT
  // =====================================================

  const lastGI =

    giPoints.length

      ? giPoints[

          giPoints.length - 1

        ]

      : null


  const lastGR =

    grPoints.length

      ? grPoints[

          grPoints.length - 1

        ]

      : null


  // =====================================================
  // RENDER
  // =====================================================

  return (

    <div

      className="
        rounded-xl
        border
        border-slate-200
        bg-white
        p-4
      "

    >

      {/* =================================================
          HEADER
          ================================================= */}

      <div

        className="
          mb-4
          flex
          flex-wrap
          items-center
          justify-between
          gap-3
        "

      >

        {/* =================================================
            TITLE
            ================================================= */}

        <h3

          className="
            text-sm
            font-bold
            text-slate-800
          "

        >

          📈 Trend GI, GR dan Forecast

        </h3>


        {/* =================================================
            LEGEND
            ================================================= */}

        <div

          className="
            flex
            flex-wrap
            gap-4
            text-xs
            text-slate-700
          "

        >

          {/* =================================================
              GI AKTUAL
              ================================================= */}

          <span

            className="
              flex
              items-center
              gap-2
            "

          >

            <span

              className="
                relative
                flex
                h-3
                w-5
                items-center
              "

            >

              {/* Garis biru */}

              <span

                className="
                  absolute
                  h-0.5
                  w-5
                  bg-blue-600
                "

              />

              {/* Titik biru */}

              <span

                className="
                  relative
                  mx-auto
                  h-2.5
                  w-2.5
                  rounded-full
                  bg-blue-600
                "

              />

            </span>


            <span>

              GI Aktual

            </span>

          </span>


          {/* =================================================
              GR AKTUAL
              ================================================= */}

          <span

            className="
              flex
              items-center
              gap-2
            "

          >

            <span

              className="
                relative
                flex
                h-3
                w-5
                items-center
              "

            >

              {/* Garis hijau */}

              <span

                className="
                  absolute
                  h-0.5
                  w-5
                  bg-green-600
                "

              />

              {/* Titik hijau */}

              <span

                className="
                  relative
                  mx-auto
                  h-2.5
                  w-2.5
                  rounded-full
                  bg-green-600
                "

              />

            </span>


            <span>

              GR Aktual

            </span>

          </span>


          {/* =================================================
              FORECAST GI
              ================================================= */}

          <span

            className="
              flex
              items-center
              gap-2
            "

          >

            <span

              className="
                relative
                flex
                h-3
                w-5
                items-center
              "

            >

              {/* Garis merah putus-putus */}

              <span

                className="
                  absolute
                  h-0.5
                  w-5
                  bg-red-600
                "

                style={{

                  backgroundImage:

                    "repeating-linear-gradient(to right, #dc2626 0px, #dc2626 5px, transparent 5px, transparent 8px)"

                }}

              />

              {/* Titik merah */}

              <span

                className="
                  relative
                  mx-auto
                  h-2.5
                  w-2.5
                  rounded-full
                  bg-red-600
                "

              />

            </span>


            <span>

              Forecast GI

            </span>

          </span>


          {/* =================================================
              FORECAST GR
              ================================================= */}

          <span

            className="
              flex
              items-center
              gap-2
            "

          >

            <span

              className="
                relative
                flex
                h-3
                w-5
                items-center
              "

            >

              {/* =========================================
                  GARIS ORANGE
                  ========================================= */}

              <span

                className="
                  absolute
                  h-0.5
                  w-5
                "

                style={{

                  backgroundImage:

                    "repeating-linear-gradient(to right, #f97316 0px, #f97316 5px, transparent 5px, transparent 8px)"

                }}

              />


              {/* =========================================
                  TITIK ORANGE
                  ========================================= */}

              <span

                className="
                  relative
                  mx-auto
                  h-2.5
                  w-2.5
                  rounded-full
                "

                style={{

                  backgroundColor: "#f97316"

                }}

              />

            </span>


            <span>

              Forecast GR

            </span>

          </span>

        </div>

      </div>


      {/* =================================================
          Y AXIS TITLE
          ================================================= */}

      <p

        className="
          mb-2
          text-xs
          font-semibold
          text-slate-700
        "

      >

        Jumlah (kg)

      </p>


      {/* =================================================
          SVG CHART
          ================================================= */}

      <svg

        viewBox={`0 0 ${width} ${height}`}

        className="w-full"

      >


        {/* =================================================
            Y AXIS GRID + LABEL
            ================================================= */}

        {

          yTicks.map(

            (tick, index) => {

              const y =

                getY(tick)


              return (

                <g

                  key={`y-axis-${index}`}

                >

                  {/* =======================================
                      GARIS GRID HORIZONTAL
                      ======================================= */}

                  <line

                    x1={paddingLeft}

                    y1={y}

                    x2={

                      width -

                      paddingRight

                    }

                    y2={y}

                    stroke="#e2e8f0"

                    strokeWidth="1"

                    strokeDasharray="4 4"

                  />


                  {/* =======================================
                      ANGKA SUMBU Y
                      ======================================= */}

                  <text

                    x={

                      paddingLeft - 12

                    }

                    y={y + 4}

                    fontSize="11"

                    textAnchor="end"

                    fill="#64748b"

                  >

                    {

                      formatNumber(

                        tick

                      )

                    }

                  </text>

                </g>

              )

            }

          )

        }


        {/* =================================================
            Y AXIS VERTICAL LINE
            ================================================= */}

        <line

          x1={paddingLeft}

          y1={paddingTop}

          x2={paddingLeft}

          y2={

            height -

            paddingBottom

          }

          stroke="#cbd5e1"

          strokeWidth="1"

        />


        {/* =================================================
            X AXIS HORIZONTAL LINE
            ================================================= */}

        <line

          x1={paddingLeft}

          y1={

            height -

            paddingBottom

          }

          x2={

            width -

            paddingRight

          }

          y2={

            height -

            paddingBottom

          }

          stroke="#cbd5e1"

          strokeWidth="1"

        />


        {/* =================================================
            GI LINE
            ================================================= */}

        {

          giPoints.length > 1

          &&

          (

            <path

              d={

                createLine(

                  giPoints

                )

              }

              fill="none"

              stroke="#2563eb"

              strokeWidth="2.5"

            />

          )

        }


        {/* =================================================
            GR LINE
            ================================================= */}

        {

          grPoints.length > 1

          &&

          (

            <path

              d={

                createLine(

                  grPoints

                )

              }

              fill="none"

              stroke="#16a34a"

              strokeWidth="2.5"

            />

          )

        }


        {/* =================================================
            GI POINT
            ================================================= */}

        {

          giPoints.map(

            (point, index) => (

              <g

                key={`gi-${index}`}

              >

                <circle

                  cx={point.x}

                  cy={point.y}

                  r="5"

                  fill="#2563eb"

                />


                <text

                  x={point.x}

                  y={point.y - 10}

                  fontSize="11"

                  textAnchor="middle"

                  fill="#334155"

                >

                  {

                    formatNumber(

                      point.value

                    )

                  }

                </text>

              </g>

            )

          )

        }


        {/* =================================================
            GR POINT
            ================================================= */}

        {

          grPoints.map(

            (point, index) => (

              <g

                key={`gr-${index}`}

              >

                <circle

                  cx={point.x}

                  cy={point.y}

                  r="5"

                  fill="#16a34a"

                />


                <text

                  x={point.x}

                  y={point.y - 10}

                  fontSize="11"

                  textAnchor="middle"

                  fill="#334155"

                >

                  {

                    formatNumber(

                      point.value

                    )

                  }

                </text>

              </g>

            )

          )

        }


        {/* =================================================
            FORECAST GI
            ================================================= */}

        {

          forecastGI !== null

          &&

          forecastGI !== undefined

          &&

          lastGI

          &&

          (

            <>

              {/* Garis forecast GI */}

              <line

                x1={lastGI.x}

                y1={lastGI.y}

                x2={forecastX}

                y2={

                  getY(

                    forecastGI

                  )

                }

                stroke="#dc2626"

                strokeWidth="2"

                strokeDasharray="8 6"

              />


              {/* Titik forecast GI */}

              <circle

                cx={forecastX}

                cy={

                  getY(

                    forecastGI

                  )

                }

                r="5"

                fill="#dc2626"

              />


              {/* Nilai forecast GI */}

              <text

                x={forecastX}

                y={

                  getY(

                    forecastGI

                  ) - 10

                }

                fontSize="11"

                textAnchor="middle"

                fill="#dc2626"

              >

                {

                  formatNumber(

                    forecastGI

                  )

                }

              </text>

            </>

          )

        }


        {/* =================================================
            FORECAST GR
            ================================================= */}

        {

          forecastGR !== null

          &&

          forecastGR !== undefined

          &&

          lastGR

          &&

          (

            <>

              {/* =========================================
                  GARIS FORECAST GR
                  ========================================= */}

              <line

                x1={lastGR.x}

                y1={lastGR.y}

                x2={forecastX}

                y2={

                  getY(

                    forecastGR

                  )

                }

                stroke="#f97316"

                strokeWidth="2"

                strokeDasharray="8 6"

              />


              {/* =========================================
                  TITIK FORECAST GR
                  ========================================= */}

              <circle

                cx={forecastX}

                cy={

                  getY(

                    forecastGR

                  )

                }

                r="5"

                fill="#f97316"

              />


              {/* =========================================
                  NILAI FORECAST GR
                  ========================================= */}

              <text

                x={forecastX}

                y={

                  getY(

                    forecastGR

                  ) - 10

                }

                fontSize="11"

                textAnchor="middle"

                fill="#f97316"

              >

                {

                  formatNumber(

                    forecastGR

                  )

                }

              </text>

            </>

          )

        }


        {/* =================================================
            X LABEL : BULAN AKTUAL
            ================================================= */}

        {

          labels.map(

            (label, index) => (

              <text

                key={`${label}-${index}`}

                x={

                  getX(index)

                }

                y={

                  height - 20

                }

                fontSize="12"

                textAnchor="middle"

                fill="#334155"

              >

                {label}

              </text>

            )

          )

        }


        {/* =================================================
            X LABEL : BULAN FORECAST
            ================================================= */}

        {

          hasForecast

          &&

          (

            <>

              {/* Nama bulan forecast */}

              <text

                x={forecastX}

                y={height - 20}

                fontSize="12"

                fontWeight="600"

                textAnchor="middle"

                fill="#dc2626"

              >

                {forecastLabel}

              </text>


              {/* Keterangan forecast */}

              <text

                x={forecastX}

                y={height - 6}

                fontSize="10"

                textAnchor="middle"

                fill="#94a3b8"

              >

                (forecast)

              </text>

            </>

          )

        }


      </svg>

    </div>

  )

}