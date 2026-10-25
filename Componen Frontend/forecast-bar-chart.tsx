"use client"

import { useEffect, useMemo, useState } from "react"

import {
  formatRupiah,
  formatCompactRupiah,
  type MonthPoint,
} from "@/lib/forecast-data"

import { cn } from "@/lib/utils"


// ============================================================
// TYPES
// ============================================================

type Props = {
  series: MonthPoint[]
  forecastMonthKey: string
}

type FilterMode =
  | "all"
  | "rutin"
  | "non-rutin"



// ============================================================
// MAIN COMPONENT
// ============================================================

export function ForecastBarChart({
  series,
  forecastMonthKey,
}: Props) {


  const [mounted, setMounted] =
    useState(false)


  const [hovered, setHovered] =
    useState<number | null>(null)


  const [filter, setFilter] =
    useState<FilterMode>("all")



  // ==========================================================
  // MOUNT ANIMATION
  // ==========================================================

  useEffect(() => {

    const id =
      requestAnimationFrame(
        () => setMounted(true)
      )


    return () =>
      cancelAnimationFrame(id)

  }, [])



  // ==========================================================
  // GET VALUE SESUAI FILTER
  // ==========================================================

  const getValue = (
    point: MonthPoint
  ): number => {


    const rutin =
      point.rutinActual > 0
        ? point.rutinActual
        : point.rutinForecast


    const nonRutin =
      point.nonRutinActual > 0
        ? point.nonRutinActual
        : point.nonRutinForecast



    if (filter === "rutin") {

      return rutin

    }



    if (filter === "non-rutin") {

      return nonRutin

    }



    return rutin + nonRutin

  }



  // ==========================================================
  // MAX VALUE
  // ==========================================================

  const max =
    Math.max(
      ...series.map(
        (point) =>
          getValue(point)
      ),
      1
    )



  // ==========================================================
  // AXIS TICKS
  // ==========================================================

  const ticks =
    useMemo(() => {


      const step =
        max / 4


      return [
        4,
        3,
        2,
        1,
        0,
      ].map(
        (i) =>
          step * i
      )


    }, [max])




  // ==========================================================
  // FILTER BUTTONS
  // ==========================================================

  const filters = [

    {
      id: "all" as const,
      label: "Semua",
    },

    {
      id: "rutin" as const,
      label: "Rutin",
    },

    {
      id: "non-rutin" as const,
      label: "Non Rutin + OVH",
    },

  ]




  // ==========================================================
  // INTERNAL CHART WIDTH
  // ==========================================================

  const chartWidth =
    Math.max(
      series.length * 54,
      700
    )



  // ==========================================================
  // RENDER
  // ==========================================================

  return (

    <div
      className="
        w-full
        min-w-0
        overflow-hidden
        rounded-2xl
        border
        border-border
        bg-card
        p-5
      "
    >


      {/* ==================================================== */}
      {/* HEADER */}
      {/* ==================================================== */}


      <div
        className="
          mb-5
          flex
          min-w-0
          flex-wrap
          items-center
          justify-between
          gap-3
        "
      >

        <div className="min-w-0">

          <h2 className="text-lg font-semibold tracking-tight">
            Trend Realisasi Pembayaran
          </h2>


          <p className="text-sm text-muted-foreground">
            Aktual + Forecast bulan depan
          </p>


        </div>



        {/* FILTER */}

        <div
          className="
            flex
            shrink-0
            items-center
            gap-1
            rounded-xl
            bg-muted
            p-1
          "
        >

          {filters.map(
            (item) => (

              <button

                key={item.id}

                type="button"

                onClick={() => {

                  setFilter(item.id)

                  setHovered(null)

                }}

                className={cn(

                  "rounded-lg px-3 py-1.5 text-xs font-medium transition-all",

                  filter === item.id

                    ? "bg-background text-foreground shadow-sm"

                    : "text-muted-foreground hover:text-foreground"

                )}

              >

                {item.label}

              </button>

            )

          )}

        </div>


      </div>

            {/* ==================================================== */}
      {/* LEGEND */}
      {/* ==================================================== */}

      <div className="mb-4 flex flex-wrap items-center gap-4 text-xs">

        {(filter === "all" ||
          filter === "rutin") && (

          <Legend
            className="bg-chart-1"
            label="Rutin"
          />

        )}


        {(filter === "all" ||
          filter === "non-rutin") && (

          <Legend
            className="bg-chart-2"
            label="Non Rutin + OVH"
          />

        )}

      </div>



      {/* ==================================================== */}
      {/* CHART */}
      {/* ==================================================== */}

      <div className="flex min-w-0 gap-3">



        {/* ================================================= */}
        {/* Y AXIS */}
        {/* ================================================= */}

        <div
          className="
            flex
            w-14
            shrink-0
            flex-col
            justify-between
            py-1
            text-right
            text-[10px]
            tabular-nums
            text-muted-foreground
          "
        >

          {ticks.map(
            (tick, index) => (

              <span key={index}>

                {formatCompactRupiah(
                  tick
                )}

              </span>

            )
          )}

        </div>




        {/* ================================================= */}
        {/* HORIZONTAL SCROLL AREA */}
        {/* ================================================= */}

        <div
          className="
            min-w-0
            flex-1
            overflow-x-auto
            overflow-y-visible
            pb-3
            scrollbar-thin
          "
        >



          {/* ================================================= */}
          {/* INTERNAL CHART */}
          {/* ================================================= */}


          <div
            className="relative"
            style={{
              width: `${chartWidth}px`,
              minWidth: "100%",
            }}
          >



            {/* GRIDLINES */}

            <div
              className="
                pointer-events-none
                absolute
                inset-x-0
                top-0
                flex
                h-72
                flex-col
                justify-between
              "
            >

              {ticks.map(
                (_, index) => (

                  <div
                    key={index}
                    className="
                      h-px
                      w-full
                      bg-border/60
                    "
                  />

                )
              )}

            </div>





            {/* BARS */}


            <div
              className="
                relative
                flex
                h-72
                items-end
                gap-2
                px-1
              "
              onMouseLeave={() =>
                setHovered(null)
              }
            >



              {series.map(
                (point, index) => {


                  const rutin =
                    point.rutinActual > 0
                      ? point.rutinActual
                      : point.rutinForecast



                  const nonRutin =
                    point.nonRutinActual > 0
                      ? point.nonRutinActual
                      : point.nonRutinForecast



                  const total =
                    rutin + nonRutin



                  const value =
                    getValue(point)




                  const isForecast =
                    point.key ===
                      forecastMonthKey ||
                    point.actual == null




                  const isHovered =
                    hovered === index



                  const dimmed =
                    hovered !== null &&
                    !isHovered




                  const totalHeightPct =
                    (value / max) * 100




                  const rutinHeightPct =
                    filter === "all" ||
                    filter === "rutin"

                      ? (rutin / max) * 100

                      : 0




                  const nonRutinHeightPct =
                    filter === "all" ||
                    filter === "non-rutin"

                      ? (nonRutin / max) * 100

                      : 0



                  return (

                    <div
                      key={point.key}
                      className="
                        group
                        relative
                        flex
                        h-full
                        w-[46px]
                        shrink-0
                        cursor-pointer
                        flex-col
                        items-center
                        justify-end
                      "
                      onMouseEnter={() =>
                        setHovered(index)
                      }
                    >



                      {/* TOOLTIP */}

                      {isHovered && (

                        <ChartTooltip
                          point={point}
                          isForecast={isForecast}
                          filter={filter}
                          index={index}
                          total={series.length}
                        />

                      )}



                      {/* VALUE LABEL */}

                      <span
                        className={cn(
                          `
                            mb-1.5
                            whitespace-nowrap
                            text-[11px]
                            font-semibold
                            tabular-nums
                            transition-all
                            duration-200
                          `,

                          isHovered
                            ? "opacity-100"
                            : "opacity-0"
                        )}
                      >

                        {formatCompactRupiah(
                          value
                        )}

                      </span>

                                           {/* BAR CONTAINER */}

                      <div
                        className={cn(
                          `
                            relative
                            flex
                            w-full
                            flex-col
                            justify-end
                            overflow-hidden
                            rounded-t-md
                            transition-[height,opacity,filter,transform,box-shadow]
                            duration-300
                            ease-out
                          `,

                          dimmed &&
                            "opacity-40 saturate-50"
                        )}

                        style={{

                          height:
                            mounted
                              ? `${Math.max(
                                  totalHeightPct,
                                  2
                                )}%`
                              : "0%",


                          transitionDelay:
                            mounted &&
                            hovered === null

                              ? `${index * 40}ms`

                              : "0ms",



                          transform:
                            isHovered

                              ? "scaleY(1.03) scaleX(1.06)"

                              : "scaleY(1)",



                          transformOrigin:
                            "bottom",



                          boxShadow:
                            isHovered

                              ? "0 8px 28px -8px rgba(0,0,0,0.35)"

                              : "none",

                        }}
                      >



                        {/* NON RUTIN + OVH */}

                        {nonRutinHeightPct > 0 && (

                          <div

                            className={cn(

                              "w-full",


                              isForecast

                                ? `
                                  border
                                  border-dashed
                                  border-chart-2/70
                                  bg-chart-2/40
                                `

                                : "bg-chart-2"

                            )}


                            style={{

                              height:
                                `${(
                                  nonRutin /
                                  Math.max(
                                    total,
                                    1
                                  )
                                ) * 100}%`,

                            }}

                          />

                        )}






                        {/* RUTIN */}

                        {rutinHeightPct > 0 && (

                          <div

                            className={cn(

                              "w-full",


                              isForecast

                                ? `
                                  border
                                  border-dashed
                                  border-chart-1/70
                                  bg-chart-1/40
                                `

                                : "bg-chart-1"

                            )}


                            style={{

                              height:
                                `${(
                                  rutin /
                                  Math.max(
                                    total,
                                    1
                                  )
                                ) * 100}%`,

                            }}

                          />

                        )}



                      </div>






                      {/* X LABEL */}

                      <span

                        className={cn(

                          `
                            mt-2
                            whitespace-nowrap
                            text-[10px]
                            transition-colors
                            sm:text-[11px]
                          `,


                          isHovered

                            ? "font-semibold text-foreground"

                            : "text-muted-foreground"

                        )}

                      >

                        {point.label}

                      </span>



                    </div>

                  )


                }

              )}



            </div>



          </div>



        </div>



      </div>





      {/* ==================================================== */}
      {/* SCROLL HINT */}
      {/* ==================================================== */}


      {series.length > 12 && (

        <p className="mt-2 text-center text-[10px] text-muted-foreground">

          ← Geser ke kiri/kanan untuk melihat periode lainnya →

        </p>

      )}



    </div>

  )

}






// ============================================================
// LEGEND
// ============================================================


function Legend({

  className,

  label,

}: {

  className: string

  label: string

}) {



  return (

    <span className="inline-flex items-center gap-1.5 text-muted-foreground">


      <span

        className={cn(

          "size-3 rounded-sm",

          className

        )}

      />


      {label}


    </span>

  )

}

// ============================================================
// TOOLTIP
// ============================================================

function ChartTooltip({
  point,
  isForecast,
  filter,
  index,
  total,
}: {
  point: MonthPoint
  isForecast: boolean
  filter: FilterMode
  index: number
  total: number
}) {



  const alignRight =
    index <= 1


  const alignLeft =
    index >= total - 2


  const align =
    alignLeft
      ? "right-0"
      : alignRight
        ? "left-0"
        : "left-1/2 -translate-x-1/2"




  const rutin =
    isForecast
      ? point.rutinForecast
      : point.rutinActual



  const nonRutin =
    isForecast
      ? point.nonRutinForecast
      : point.nonRutinActual



  const totalValue =
    rutin + nonRutin




  const selectedValue =
    filter === "rutin"

      ? rutin

      : filter === "non-rutin"

        ? nonRutin

        : totalValue





  const relevantJasa =
    point.jasa.filter(
      (jasa) => {


        if (
          filter === "rutin"
        ) {

          return (
            jasa.jenis ===
            "RUTIN"
          )

        }



        if (
          filter === "non-rutin"
        ) {

          return (
            jasa.jenis !==
            "RUTIN"
          )

        }



        return true

      }
    )




  return (

    <div
      className={cn(
        `
          pointer-events-none
          absolute
          bottom-[calc(100%+0.5rem)]
          z-20
          w-64
          origin-bottom
          rounded-xl
          border
          border-border
          bg-popover/95
          p-3.5
          text-left
          shadow-2xl
          backdrop-blur
        `,

        `
          animate-in
          fade-in-0
          zoom-in-95
          slide-in-from-bottom-1
          duration-200
        `,

        align
      )}
    >



      <div className="flex items-center justify-between gap-2">

        <span className="text-sm font-semibold">
          {point.label}
        </span>


        <span
          className={cn(
            `
              rounded-full
              px-2
              py-0.5
              text-[10px]
              font-medium
            `,


            isForecast
              ? "bg-chart-2/20 text-chart-2"
              : "bg-chart-1/20 text-chart-1"
          )}
        >

          {isForecast
            ? "FORECAST"
            : "AKTUAL"}

        </span>


      </div>





      <p className="mt-2.5 text-lg font-semibold tabular-nums">

        {formatRupiah(
          selectedValue
        )}

      </p>





      <div className="mt-3 space-y-2 border-t border-border pt-3">



        {(filter === "all" ||
          filter === "rutin") && (

          <div className="flex items-center justify-between gap-3 text-xs">

            <span className="flex items-center gap-1.5">

              <span className="size-2 rounded-full bg-chart-1" />

              <span>
                Rutin
              </span>

            </span>


            <span className="font-medium tabular-nums">

              {formatCompactRupiah(
                rutin
              )}

            </span>


          </div>

        )}






        {(filter === "all" ||
          filter === "non-rutin") && (

          <div className="flex items-center justify-between gap-3 text-xs">


            <span className="flex items-center gap-1.5">

              <span className="size-2 rounded-full bg-chart-2" />

              <span>
                Non Rutin + OVH
              </span>

            </span>



            <span className="font-medium tabular-nums">

              {formatCompactRupiah(
                nonRutin
              )}

            </span>


          </div>

        )}



      </div>





      {relevantJasa.length > 0 && (

        <div className="mt-3 border-t border-border pt-3">


          <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">

            Rincian Jasa

          </p>



          <div className="space-y-1.5">


            {relevantJasa.map(
              (jasa) => (

                <div
                  key={`${jasa.jenis}-${jasa.nama}`}
                  className="
                    flex
                    items-center
                    justify-between
                    gap-3
                    text-xs
                  "
                >


                  <span className="flex min-w-0 items-center gap-1.5">


                    <span
                      className={cn(
                        "size-1.5 shrink-0 rounded-full",

                        jasa.jenis === "RUTIN"

                          ? "bg-chart-1"

                          : "bg-chart-2"

                      )}
                    />


                    <span className="truncate">

                      {jasa.nama}

                    </span>


                  </span>





                  <span className="shrink-0 tabular-nums text-muted-foreground">


                    {formatCompactRupiah(

                      isForecast

                        ? jasa.forecast

                        : jasa.realisasi

                    )}


                  </span>




                </div>

              )
            )}



          </div>



        </div>

      )}



    </div>

  )

}