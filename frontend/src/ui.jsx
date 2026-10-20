import { useEffect, useRef, useState } from 'react'
import { ImagePlus, X, MoveHorizontal } from 'lucide-react'

export const cardClass =
  'rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900'
export const mutedClass = 'text-xs text-slate-500 dark:text-slate-400'
const labelClass = 'text-sm font-medium text-slate-700 dark:text-slate-200'

/* ---------- Upload box with drag and drop ---------- */
export function Dropzone({ label, file, onFile, maxMb = 10 }) {
  const [drag, setDrag] = useState(false)
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState('')
  const input = useRef(null)

  useEffect(() => {
    if (!file) {
      setPreview(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  function accept(f) {
    if (!f) return
    if (!/^image\/(jpeg|png|webp)$/.test(f.type)) {
      setError('Use a JPEG, PNG or WebP image.')
      return
    }
    if (f.size > maxMb * 1024 * 1024) {
      setError(`Image must be under ${maxMb} MB.`)
      return
    }
    setError('')
    onFile(f)
  }

  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between">
        <span className={labelClass}>{label}</span>
        {file && (
          <span className="max-w-[10rem] truncate text-xs text-slate-500 dark:text-slate-400">
            {file.name}
          </span>
        )}
      </div>
      <div
        role="button"
        tabIndex={0}
        aria-label={`${label} image: drop a file or press Enter to browse`}
        onClick={() => input.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            input.current?.click()
          }
        }}
        onDragOver={(e) => {
          e.preventDefault()
          setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDrag(false)
          accept(e.dataTransfer.files?.[0])
        }}
        className={`group relative flex h-32 cursor-pointer items-center justify-center overflow-hidden rounded-xl border-2 border-dashed transition ${
          drag
            ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-950/40'
            : 'border-slate-300 bg-slate-50 hover:border-indigo-400 hover:bg-indigo-50/40 dark:border-slate-700 dark:bg-slate-800/40 dark:hover:border-indigo-500 dark:hover:bg-slate-800'
        }`}
      >
        {preview ? (
          <>
            <img src={preview} alt={`${label} preview`} className="h-full w-full object-cover" />
            <button
              type="button"
              aria-label={`Remove ${label}`}
              onClick={(e) => {
                e.stopPropagation()
                onFile(null)
              }}
              className="absolute right-2 top-2 rounded-full bg-white/90 p-1 shadow hover:bg-white dark:bg-slate-800/90 dark:hover:bg-slate-700"
            >
              <X className="h-4 w-4 text-slate-700 dark:text-slate-200" />
            </button>
          </>
        ) : (
          <div className="text-center">
            <ImagePlus className="mx-auto h-6 w-6 text-slate-400 group-hover:text-indigo-500" />
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Drop an image or{' '}
              <span className="font-medium text-indigo-600 dark:text-indigo-400">browse</span>
            </p>
          </div>
        )}
        <input
          ref={input}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          tabIndex={-1}
          onChange={(e) => {
            accept(e.target.files?.[0])
            e.target.value = ''
          }}
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-600 dark:text-red-400">{error}</p>}
    </div>
  )
}

/* ---------- Slider ---------- */
export function Slider({
  label, value, min, max, step = 1, onChange, hint, disabled, format = (v) => v,
}) {
  return (
    <div className={disabled ? 'opacity-50' : ''}>
      <div className="flex items-center justify-between text-sm">
        <span className={labelClass}>{label}</span>
        <span className="tabular-nums text-slate-500 dark:text-slate-400">{format(value)}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        aria-label={label}
        onChange={(e) => onChange(Number(e.target.value))}
        className="mt-2 w-full cursor-pointer accent-indigo-600 disabled:cursor-not-allowed dark:accent-indigo-400"
      />
      {hint && <p className={`mt-1 ${mutedClass}`}>{hint}</p>}
    </div>
  )
}

/* ---------- Segmented control ---------- */
export function Segmented({ options, value, onChange, label }) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className="grid auto-cols-fr grid-flow-col rounded-xl bg-slate-100 p-1 dark:bg-slate-800"
    >
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={value === o.value}
          onClick={() => onChange(o.value)}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
            value === o.value
              ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-600 dark:text-white'
              : 'text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

/* ---------- Switch ---------- */
export function Toggle({ checked, onChange, label, hint }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div>
        <p className={labelClass}>{label}</p>
        {hint && <p className={mutedClass}>{hint}</p>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={`relative mt-0.5 h-6 w-11 shrink-0 rounded-full transition ${
          checked ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-600'
        }`}
      >
        <span
          className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
            checked ? 'translate-x-5' : ''
          }`}
        />
      </button>
    </div>
  )
}

/* ---------- Count-up number (rounds half up, e.g. 4.595 -> 4.60) ---------- */
export function useCountUp(target, decimals = 0, duration = 700) {
  const [value, setValue] = useState(0)
  useEffect(() => {
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (reduce) {
      setValue(target)
      return
    }
    let raf
    let start
    const tick = (t) => {
      if (start === undefined) start = t
      const p = Math.min((t - start) / duration, 1)
      setValue(target * (1 - Math.pow(1 - p, 3)))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, duration])
  const f = 10 ** decimals
  return (Math.round(value * f + 1e-6) / f).toFixed(decimals)
}

export function AnimatedNumber({ value, decimals = 0, suffix = '' }) {
  const v = useCountUp(value, decimals)
  return (
    <>
      {v}
      {suffix}
    </>
  )
}

/* ---------- Stat card ---------- */
export function StatCard({ icon: Icon, label, sub, children }) {
  return (
    <div className={`${cardClass} p-4`}>
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
        <Icon className="h-4 w-4" />
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold tabular-nums text-slate-900 dark:text-slate-50">
        {children}
      </div>
      {sub && <p className={`mt-1 ${mutedClass}`}>{sub}</p>}
    </div>
  )
}

/* ---------- Before/after comparison slider ---------- */
export function CompareSlider({ left, right, leftLabel, rightLabel, width, height }) {
  const [pos, setPos] = useState(50)
  return (
    <div
      className="relative select-none overflow-hidden rounded-xl bg-slate-900"
      style={{ aspectRatio: `${width} / ${height}` }}
    >
      <img
        src={right}
        alt={rightLabel}
        draggable={false}
        className="absolute inset-0 h-full w-full object-contain"
      />
      <img
        src={left}
        alt={leftLabel}
        draggable={false}
        className="absolute inset-0 h-full w-full object-contain"
        style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}
      />
      <div
        className="pointer-events-none absolute inset-y-0 w-0.5 bg-white shadow"
        style={{ left: `${pos}%` }}
      >
        <div className="absolute left-1/2 top-1/2 flex h-9 w-9 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-white shadow-lg ring-1 ring-slate-200">
          <MoveHorizontal className="h-4 w-4 text-slate-600" />
        </div>
      </div>
      <span className="pointer-events-none absolute left-3 top-3 rounded-full bg-black/55 px-2.5 py-1 text-xs font-medium text-white">
        {leftLabel}
      </span>
      <span className="pointer-events-none absolute right-3 top-3 rounded-full bg-black/55 px-2.5 py-1 text-xs font-medium text-white">
        {rightLabel}
      </span>
      <input
        type="range"
        min="0"
        max="100"
        step="0.1"
        value={pos}
        aria-label="Comparison position"
        onChange={(e) => setPos(Number(e.target.value))}
        className="absolute inset-0 h-full w-full cursor-ew-resize opacity-0"
      />
    </div>
  )
}