"use client"

import { useEffect, useState } from "react"
import {
  formatRupiah,
  type ForecastResponse,
} from "@/lib/forecast-data"
import { cn } from "@/lib/utils"

interface BreakdownDonutProps {
  data: ForecastResponse
}

export function BreakdownDonut({
  data,
}: BreakdownDonutProps) {
  const [mounted, setMounted] = useState(false)
  const [hovered, setHovered] = useState<number | null>(null)

  useEffect(() => {
    const id = requestAnimationFrame(() => {
      setMounted(true)
    })

    return () => {
      cancelAnimationFrame(id)
    }
  }, [])

  // Mencegah pembagian dengan 0
  const total = data.totalForecast || 1

  const segments = [
    {
      label: "RUTIN",
      value: data.rutinForecast || 0,
      color: "var(--chart-1)",
    },
    {
      label: "NON RUTIN + OVH",
      value: data.nonRutinForecast || 0,
      color: "var(--chart-2)",
    },
  ]

  const radius = 70
  const circumference = 2 * Math.PI * radius
  const stroke = 22

  let offsetAcc = 0

  return (
    <div className="flex h-full flex-col rounded-2xl border border-border bg-card p-5">
      
      {/* ================= HEADER ================= */}

      <div className="mb-4">
        <h2 className="text-lg font-semibold tracking-tight">
          Breakdown Forecast
        </h2>

        <p className="text-sm text-muted-foreground">
          {data.forecastMonthLabel}
        </p>
      </div>

      {/* ================= DONUT ================= */}

      <div className="flex flex-1 flex-col items-center justify-center gap-6">
        
        <div className="relative">

          <svg
            viewBox="0 0 200 200"
            className="size-48 -rotate-90"
          >

            {/* Background circle */}

            <circle
              cx="100"
              cy="100"
              r={radius}
              fill="none"
              stroke="var(--muted)"
              strokeWidth={stroke}
            />

            {/* Forecast segments */}

            {segments.map((segment, index) => {
              const percentage =
                segment.value / total

              const dash =
                percentage *
                circumference *
                (mounted ? 1 : 0)

              const dashOffset =
                -offsetAcc * circumference

              offsetAcc += percentage

              const isHovered =
                hovered === index

              if (segment.value <= 0) {
                return null
              }

              return (
                <circle
                  key={segment.label}
                  cx="100"
                  cy="100"
                  r={radius}
                  fill="none"
                  stroke={segment.color}
                  strokeWidth={
                    isHovered
                      ? stroke + 4
                      : stroke
                  }
                  strokeDasharray={`${dash} ${circumference}`}
                  strokeDashoffset={dashOffset}
                  strokeLinecap="round"
                  className="
                    cursor-pointer
                    transition-[stroke-width,opacity]
                    duration-300
                    ease-out
                  "
                  style={{
                    opacity:
                      hovered !== null && !isHovered
                        ? 0.4
                        : 1,

                    transition:
                      "stroke-dasharray 900ms ease-out, stroke-width 250ms ease, opacity 250ms ease",
                  }}
                  onMouseEnter={() =>
                    setHovered(index)
                  }
                  onMouseLeave={() =>
                    setHovered(null)
                  }
                />
              )
            })}
          </svg>

          {/* ================= CENTER LABEL ================= */}

          <div
            className="
              pointer-events-none
              absolute
              inset-0
              flex
              flex-col
              items-center
              justify-center
              text-center
            "
          >

            {hovered !== null ? (
              <>
                <span
                  className="
                    text-[10px]
                    font-medium
                    uppercase
                    tracking-wide
                    text-muted-foreground
                  "
                >
                  {segments[hovered].label}
                </span>

                <span
                  className="
                    mt-0.5
                    text-base
                    font-semibold
                    tabular-nums
                  "
                >
                  {(
                    (segments[hovered].value /
                      total) *
                    100
                  ).toFixed(0)}
                  %
                </span>

                <span
                  className="
                    text-[11px]
                    tabular-nums
                    text-muted-foreground
                  "
                >
                  {formatRupiah(
                    segments[hovered].value
                  )}
                </span>
              </>
            ) : (
              <>
                <span
                  className="
                    text-[10px]
                    font-medium
                    uppercase
                    tracking-wide
                    text-muted-foreground
                  "
                >
                  Total
                </span>

                <span
                  className="
                    mt-0.5
                    max-w-[7rem]
                    text-sm
                    font-semibold
                    leading-tight
                    tabular-nums
                  "
                >
                  {formatRupiah(
                    data.totalForecast || 0
                  )}
                </span>
              </>
            )}

          </div>
        </div>

        {/* ================= LEGEND ================= */}

        <div className="w-full space-y-2">

          {segments.map((segment, index) => {
            const percentage =
              (segment.value / total) * 100

            return (
              <button
                type="button"
                key={segment.label}
                onMouseEnter={() =>
                  setHovered(index)
                }
                onMouseLeave={() =>
                  setHovered(null)
                }
                className={cn(
                  `
                    flex
                    w-full
                    items-center
                    justify-between
                    gap-3
                    rounded-lg
                    border
                    px-3
                    py-2
                    text-left
                    transition-colors
                  `,
                  hovered === index
                    ? "border-border bg-muted"
                    : "border-transparent hover:bg-muted/50"
                )}
              >

                {/* Label */}

                <span
                  className="
                    flex
                    items-center
                    gap-2
                    text-sm
                  "
                >
                  <span
                    className="
                      size-2.5
                      rounded-full
                    "
                    style={{
                      background:
                        segment.color,
                    }}
                  />

                  {segment.label}
                </span>

                {/* Percentage + Rupiah */}

                <span
                  className="
                    flex
                    items-center
                    gap-2
                  "
                >
                  <span
                    className="
                      text-sm
                      font-semibold
                      tabular-nums
                    "
                  >
                    {percentage.toFixed(0)}%
                  </span>

                  <span
                    className="
                      text-xs
                      tabular-nums
                      text-muted-foreground
                    "
                  >
                    {formatRupiah(
                      segment.value
                    )}
                  </span>
                </span>

              </button>
            )
          })}

        </div>
      </div>
    </div>
  )
}