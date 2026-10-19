import { useEffect, useRef, useState } from 'react'
import { ImagePlus, X, MoveHorizontal } from 'lucide-react'

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
        <span className="text-sm font-medium text-slate-700">{label}</span>
        {file && (
          <span className="max-w-[10rem] truncate text-xs text-slate-400">
            {file.name}
          </span>
        )}
      </div>
      <div
        role="button"
        tabIndex={0}
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
            ? 'border-indigo-500 bg-indigo-50'
            : 'border-slate-200 bg-slate-50 hover:border-indigo-300 hover:bg-indigo-50/40'
        }`}
      >
        {preview ? (
          <>
            <img
              src={preview}
              alt={`${label} preview`}
              className="h-full w-full object-cover"
            />
            <button
              type="button"
              aria-label={`Remove ${label}`}
              onClick={(e) => {
                e.stopPropagation()
                onFile(null)
              }}
              className="absolute right-2 top-2 rounded-full bg-white/90 p-1 shadow hover:bg-white"
            >
              <X className="h-4 w-4 text-slate-700" />
            </button>
          </>
        ) : (
          <div className="text-center">
            <ImagePlus className="mx-auto h-6 w-6 text-slate-400 group-hover:text-indigo-500" />
            <p className="mt-1 text-xs text-slate-500">
              Drop an image or{' '}
              <span className="font-medium text-indigo-600">browse</span>
            </p>
          </div>
        )}
        <input
          ref={input}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => {
            accept(e.target.files?.[0])
            e.target.value = ''
          }}
        />
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
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
        <span className="font-medium text-slate-700">{label}</span>
        <span className="tabular-nums text-slate-500">{format(value)}</span>
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
        className="mt-2 w-full cursor-pointer accent-indigo-600 disabled:cursor-not-allowed"
      />
      {hint && <p className="mt-1 text-xs text-slate-400">{hint}</p>}
    </div>
  )
}

/* ---------- Segmented control ---------- */
export function Segmented({ options, value, onChange, label }) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className="grid auto-cols-fr grid-flow-col rounded-xl bg-slate-100 p-1"
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
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-500 hover:text-slate-800'
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
        <p className="text-sm font-medium text-slate-700">{label}</p>
        {hint && <p className="text-xs text-slate-400">{hint}</p>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={`relative mt-0.5 h-6 w-11 shrink-0 rounded-full transition ${
          checked ? 'bg-indigo-600' : 'bg-slate-300'
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

/* ---------- Count-up number ---------- */
export function useCountUp(target, decimals = 0, duration = 700) {
  const [value, setValue] = useState(0)
  useEffect(() => {
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
  return value.toFixed(decimals)
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
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-slate-400">
        <Icon className="h-4 w-4" />
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold tabular-nums text-slate-900">
        {children}
      </div>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </div>
  )
}

/* ---------- Before/after comparison slider ---------- */
export function CompareSlider({
  left, right, leftLabel, rightLabel, width, height,
}) {
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