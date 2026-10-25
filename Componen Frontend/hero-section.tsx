'use client'

import {
  Bell,
  ChevronRight,
  Menu,
} from 'lucide-react'

interface HeroSectionProps {
  sidebarOpen: boolean
  setSidebarOpen: React.Dispatch<React.SetStateAction<boolean>>
}

export default function HeroSection({
  sidebarOpen,
  setSidebarOpen,
}: HeroSectionProps) {
  return (
    <div className="relative h-[270px]">

      {/* Content */}
      <div className="relative z-10 flex h-full items-start justify-between px-10 pt-8">

        {/* ================= LEFT ================= */}
        <div className="flex-1">

          {/* Breadcrumb */}
          <div className="mb-4 flex items-center gap-3">

            {/* Sidebar Toggle */}
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="
                flex
                h-10
                w-10
                items-center
                justify-center

                rounded-xl

                border
                border-white/15

                bg-white/10
                backdrop-blur-xl

                text-white

                transition-all
                duration-300

                hover:bg-white/20
                hover:scale-105
              "
            >
              <Menu className="h-5 w-5" />
            </button>

            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-sm text-white/70">

              <span>Forecast Barang</span>

              <ChevronRight className="h-4 w-4" />

              <span>Section</span>

              <ChevronRight className="h-4 w-4" />

              <span className="font-medium text-white">
                Stock Availability
              </span>

            </div>

          </div>

          {/* Title */}
          <h1 className="mb-3 text-5xl font-bold tracking-tight text-white drop-shadow-md">
            Stock Availability
          </h1>

          {/* Subtitle */}
          <p className="max-w-2xl text-base leading-7 text-white/80">
            Analisis ketersediaan stok material berdasarkan forecast
            pemakaian dan stok terkini.
          </p>

        </div>

        {/* ================= RIGHT ================= */}
        <div className="flex items-center gap-3">

          {/* Notification */}
          <button
            className="
              relative

              flex
              h-11
              w-11

              items-center
              justify-center

              rounded-xl

              bg-white

              shadow-lg

              transition-all
              duration-300

              hover:-translate-y-0.5
              hover:bg-slate-50
            "
          >
            <Bell className="h-5 w-5 text-slate-700" />

            <span
              className="
                absolute
                right-2
                top-2

                h-2.5
                w-2.5

                rounded-full

                bg-red-500
              "
            />
          </button>

        </div>

      </div>

    </div>
  )
}