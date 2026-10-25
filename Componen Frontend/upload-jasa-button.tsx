"use client"

import { useEffect, useRef, useState } from "react"
import type { ChangeEvent } from "react"
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  Upload,
  X,
} from "lucide-react"

// ============================================================
// TIPE (sesuai response POST /upload di backend jasa)
// ============================================================

export interface UploadSummary {
  rows_in_file: number
  rows_inserted: number
  rows_duplicate: number
}

export interface UploadResult {
  status: string
  message?: string
  filename?: string
  upload_summary: UploadSummary
  database?: {
    table: string
    total_rows: number
  }
  warnings?: string[]
}

interface UploadJasaButtonProps {
  /**
   * Dipanggil SETELAH upload sukses (termasuk jika 0 baris baru).
   * Dipakai page.tsx untuk memuat ulang forecast.
   */
  onUploadSuccess?: (result: UploadResult) => void

  /** Default: backend jasa, port 8000. */
  apiUrl?: string

  className?: string
}

type UploadState =
  | { status: "idle" }
  | { status: "uploading"; fileName: string }
  | { status: "success"; fileName: string; result: UploadResult }
  | { status: "error"; message: string; fileName?: string }

// ============================================================
// KONFIGURASI
// ============================================================

const DEFAULT_API_URL = "http://127.0.0.1:8000/upload"

const ALLOWED_EXTENSIONS = [".xlsx", ".xls"]

// ============================================================
// HELPER
// ============================================================

function hasAllowedExtension(fileName: string): boolean {
  const lower = fileName.toLowerCase()

  return ALLOWED_EXTENSIONS.some((extension) =>
    lower.endsWith(extension)
  )
}

function formatNumber(value: number): string {
  return Number(value ?? 0).toLocaleString("id-ID")
}

/**
 * Mengambil pesan error dari response backend.
 * FastAPI mengirim { detail: "..." } (string) atau
 * { detail: [{ msg: "..." }] } untuk error validasi request.
 */
function extractErrorMessage(body: unknown, status: number): string {
  const record = (body ?? {}) as {
    detail?: unknown
    message?: unknown
  }

  if (typeof record.detail === "string" && record.detail.trim()) {
    return record.detail
  }

  if (Array.isArray(record.detail)) {
    const messages = record.detail
      .map((item) =>
        item && typeof item === "object" && "msg" in item
          ? String((item as { msg: unknown }).msg)
          : String(item)
      )
      .filter(Boolean)

    if (messages.length > 0) {
      return messages.join("\n")
    }
  }

  if (typeof record.message === "string" && record.message.trim()) {
    return record.message
  }

  return `Upload gagal (${status}).`
}

// ============================================================
// KOMPONEN
// ============================================================

export function UploadJasaButton({
  onUploadSuccess,
  apiUrl = DEFAULT_API_URL,
  className = "",
}: UploadJasaButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const mountedRef = useRef(true)

  const [state, setState] = useState<UploadState>({
    status: "idle",
  })

  useEffect(() => {
    mountedRef.current = true

    return () => {
      mountedRef.current = false
    }
  }, [])

  const isUploading = state.status === "uploading"

  function safeSetState(next: UploadState) {
    if (mountedRef.current) {
      setState(next)
    }
  }

  function handleButtonClick() {
    if (isUploading) return

    inputRef.current?.click()
  }

  async function handleFileChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const input = event.target
    const file = input.files?.[0]

    // Reset agar file yang sama bisa dipilih ulang
    input.value = ""

    if (!file || isUploading) return

    // --------------------------------------------------------
    // VALIDASI DI SISI KLIEN
    // --------------------------------------------------------

    if (!hasAllowedExtension(file.name)) {
      safeSetState({
        status: "error",
        fileName: file.name,
        message:
          "File harus berupa Excel (.xlsx atau .xls).",
      })
      return
    }

    if (file.size === 0) {
      safeSetState({
        status: "error",
        fileName: file.name,
        message: "File kosong.",
      })
      return
    }

    // --------------------------------------------------------
    // KIRIM KE BACKEND
    // --------------------------------------------------------

    safeSetState({
      status: "uploading",
      fileName: file.name,
    })

    let result: UploadResult

    try {
      const formData = new FormData()
      formData.append("file", file)

      // Jangan set header Content-Type: browser mengisinya
      // otomatis lengkap dengan boundary multipart.
      const response = await fetch(apiUrl, {
        method: "POST",
        body: formData,
      })

      let body: unknown = null

      try {
        body = await response.json()
      } catch {
        body = null
      }

      if (!response.ok) {
        throw new Error(
          extractErrorMessage(body, response.status)
        )
      }

      const parsed = body as UploadResult | null

      if (!parsed || !parsed.upload_summary) {
        throw new Error("Respons backend tidak dikenali.")
      }

      result = parsed
    } catch (error) {
      const message =
        error instanceof TypeError
          ? "Tidak dapat terhubung ke backend jasa (port 8000). " +
            "Pastikan backend sedang berjalan."
          : error instanceof Error
            ? error.message
            : "Upload gagal."

      safeSetState({
        status: "error",
        fileName: file.name,
        message,
      })
      return
    }

    safeSetState({
      status: "success",
      fileName: file.name,
      result,
    })

    // Dipanggil di luar try/catch: error di callback page
    // tidak boleh tampil sebagai "upload gagal".
    onUploadSuccess?.(result)
  }

  // ----------------------------------------------------------
  // RENDER
  // ----------------------------------------------------------

  return (
    <div className={`inline-flex flex-col items-start gap-3 ${className}`}>
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls"
        className="hidden"
        onChange={handleFileChange}
      />

      <button
        type="button"
        onClick={handleButtonClick}
        disabled={isUploading}
        className="
          flex h-11 items-center gap-2 rounded-xl border border-white/15
          bg-white/10 px-4 text-sm font-medium text-white
          backdrop-blur-xl transition
          hover:bg-white/20
          disabled:cursor-not-allowed disabled:opacity-60
        "
      >
        {isUploading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Upload className="h-4 w-4" />
        )}

        {isUploading ? "Mengunggah..." : "Upload Data Jasa"}
      </button>

      {/* ====================================================
          STATUS
      ==================================================== */}

      {state.status !== "idle" && (
        <div
          role="status"
          aria-live="polite"
          className={`
            relative w-full max-w-[460px] rounded-xl border px-4 py-3
            text-sm backdrop-blur-xl
            ${
              state.status === "success"
                ? "border-emerald-400/30 bg-emerald-500/15 text-emerald-50"
                : state.status === "error"
                  ? "border-red-400/30 bg-red-500/15 text-red-50"
                  : "border-white/15 bg-white/10 text-white"
            }
          `}
        >
          {!isUploading && (
            <button
              type="button"
              aria-label="Tutup"
              onClick={() => safeSetState({ status: "idle" })}
              className="absolute right-2 top-2 rounded-md p-1 text-white/60 transition hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          )}

          {/* ---------------- MENGUNGGAH ---------------- */}

          {state.status === "uploading" && (
            <p className="pr-6 break-all">
              Mengunggah <strong>{state.fileName}</strong>. Mohon
              tunggu, file sedang diproses...
            </p>
          )}

          {/* ---------------- BERHASIL ---------------- */}

          {state.status === "success" && (
            <div className="flex gap-2 pr-6">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />

              <div className="min-w-0">
                <p className="font-semibold">
                  Upload berhasil: {formatNumber(
                    state.result.upload_summary.rows_inserted
                  )}{" "}
                  baris baru,{" "}
                  {formatNumber(
                    state.result.upload_summary.rows_duplicate
                  )}{" "}
                  duplikat
                </p>

                <p className="mt-1 break-all text-emerald-100/80">
                  {state.fileName} (
                  {formatNumber(
                    state.result.upload_summary.rows_in_file
                  )}{" "}
                  baris di file)
                  {state.result.database
                    ? ` · total di database ${formatNumber(
                        state.result.database.total_rows
                      )} baris`
                    : ""}
                </p>

                {state.result.upload_summary.rows_inserted === 0 && (
                  <p className="mt-1 text-emerald-100/80">
                    Tidak ada data baru: semua baris sudah ada di
                    database.
                  </p>
                )}

                {state.result.warnings &&
                  state.result.warnings.length > 0 && (
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-amber-200">
                      {state.result.warnings.map((warning, index) => (
                        <li key={index}>{warning}</li>
                      ))}
                    </ul>
                  )}
              </div>
            </div>
          )}

          {/* ---------------- GAGAL ---------------- */}

          {state.status === "error" && (
            <div className="flex gap-2 pr-6">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />

              <div className="min-w-0">
                <p className="font-semibold">Upload gagal</p>

                <p className="mt-1 max-h-48 overflow-y-auto whitespace-pre-line break-words text-red-100/90">
                  {state.message}
                </p>

                {state.fileName && (
                  <p className="mt-1 break-all text-xs text-red-100/60">
                    File: {state.fileName}
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default UploadJasaButton
