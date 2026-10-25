"use client"

import {
  LayoutDashboard,
  TrendingUp,
  ShoppingCart,
  Settings,
} from "lucide-react"

import Link from "next/link"
import { usePathname } from "next/navigation"

const navigationItems = [
  {
    icon: LayoutDashboard,
    label: "Dashboard",
    href: "/",
  },
  {
    icon: TrendingUp,
    label: "Forecast Jasa",
    href: "/forecast-jasa",
  },
  {
    icon: ShoppingCart,
    label: "Forecast Barang",
    href: "/forecast-barang",
  },
  {
    icon: Settings,
    label: "Settings",
    href: "/settings",
  },
]

interface SidebarProps {
  sidebarOpen: boolean
}

export default function Sidebar({
  sidebarOpen,
}: SidebarProps) {
  const pathname = usePathname()

  return (
    <aside
      className={`
        fixed
        left-0
        top-0
        z-50

        h-screen
        bg-white
        border-r
        border-slate-200

        flex
        flex-col

        shadow-sm

        transition-all
        duration-300
        ease-in-out

        overflow-hidden

        ${
          sidebarOpen
            ? "w-64"
            : "w-20"
        }
      `}
    >

      {/* ================= LOGO ================= */}

      <div
        className={`
          flex
          items-center

          ${
            sidebarOpen
              ? "justify-start px-6"
              : "justify-center"
          }

          pt-6
          pb-8
        `}
      >
        <div
          className="
            w-10
            h-10
            rounded-full
            bg-gradient-to-br
            from-blue-500
            to-blue-700

            flex
            items-center
            justify-center

            shrink-0

            shadow-lg
            shadow-blue-500/30
          "
        >
          <span className="text-white text-sm font-bold">
            SI
          </span>
        </div>

        <div
          className={`
            overflow-hidden
            transition-all
            duration-300

            ${
              sidebarOpen
                ? "ml-3 w-32 opacity-100"
                : "ml-0 w-0 opacity-0"
            }
          `}
        >
          <div className="text-xs font-bold whitespace-nowrap">
            SEMEN
          </div>

          <div className="text-xs font-bold whitespace-nowrap">
            INDONESIA
          </div>

          <div className="text-xs text-slate-500 whitespace-nowrap">
            GROUP
          </div>
        </div>
      </div>

      {/* ================= NAVIGATION ================= */}

      <nav className="flex-1 px-3 space-y-2">

        {navigationItems.map((item) => {

          const isActive =
            pathname === item.href

          return (
            <Link
              key={item.label}
              href={item.href}
              title={item.label}
              className={`
                group

                w-full
                flex
                items-center

                ${
                  sidebarOpen
                    ? "justify-start px-4 gap-3"
                    : "justify-center"
                }

                h-12

                rounded-xl

                transition-all
                duration-300

                ${
                  isActive
                    ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-lg shadow-blue-500/25"
                    : "text-slate-600 hover:bg-slate-100 hover:text-blue-600"
                }
              `}
            >

              <item.icon
                className={`
                  w-5
                  h-5
                  shrink-0

                  transition-transform
                  duration-300

                  group-hover:scale-110

                  ${
                    isActive
                      ? "text-white"
                      : ""
                  }
                `}
              />

              <span
                className={`
                  whitespace-nowrap
                  overflow-hidden

                  transition-all
                  duration-300

                  ${
                    sidebarOpen
                      ? "opacity-100 w-auto"
                      : "opacity-0 w-0"
                  }
                `}
              >
                {item.label}
              </span>

            </Link>
          )
        })}

      </nav>

      {/* ================= PROFILE ================= */}

      <div className="border-t border-slate-200 p-3">

        <div
          className={`
            rounded-2xl

            bg-gradient-to-br
            from-blue-500
            to-blue-700

            text-white

            transition-all
            duration-300

            ${
              sidebarOpen
                ? "p-4"
                : "p-3"
            }
          `}
        >

          <div
            className={`
              flex

              ${
                sidebarOpen
                  ? "justify-start"
                  : "justify-center"
              }
            `}
          >

            <div
              className="
                w-11
                h-11
                rounded-full

                bg-white/20

                flex
                items-center
                justify-center

                font-bold
              "
            >
              PG
            </div>

          </div>

          <div
            className={`
              overflow-hidden

              transition-all
              duration-300

              ${
                sidebarOpen
                  ? "max-h-40 opacity-100 mt-3"
                  : "max-h-0 opacity-0 mt-0"
              }
            `}
          >

            <div className="font-semibold">
              Planner PG01
            </div>

            <div className="text-xs text-blue-100">
              Planning Administrator
            </div>

            <div className="mt-4 flex items-center gap-2 text-xs">
              <div className="w-2 h-2 rounded-full bg-green-400"></div>
              Online
            </div>

          </div>

        </div>

      </div>

    </aside>
  )
}