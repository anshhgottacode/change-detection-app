import {
  Layers, Contrast, Flame, ArrowLeftRight, Crosshair, Percent, Shapes,
  SlidersHorizontal, Timer, TriangleAlert, CheckCircle2, ScanSearch,
  Download, FileJson,
} from 'lucide-react'
import { AnimatedNumber, CompareSlider, StatCard, cardClass, mutedClass } from './ui'

const BASE_TABS = [
  { id: 'overlay', label: 'Overlay', icon: Layers },
  { id: 'mask', label: 'Mask', icon: Contrast },
  { id: 'heatmap', label: 'Heatmap', icon: Flame },
  { id: 'compare', label: 'Compare', icon: ArrowLeftRight },
]

// which image each tab downloads
const DOWNLOAD = {
  overlay: { key: 'overlay', ext: 'jpg' },
  mask: { key: 'mask', ext: 'png' },
  heatmap: { key: 'heatmap', ext: 'jpg' },
  compare: { key: 'after', ext: 'jpg' },
  align: { key: 'matches', ext: 'jpg' },
}

function saveHref(href, filename) {
  const a = document.createElement('a')
  a.href = href
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
}

function saveJson(data, filename) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }),
  )
  saveHref(url, filename)
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

function Empty() {
  const steps = [
    'Upload a before and an after image of the same scene, or try a sample.',
    'Choose a method and adjust the settings.',
    'Press Analyze to see what changed.',
  ]
  return (
    <div className="flex min-h-[28rem] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/60 p-8 text-center dark:border-slate-700 dark:bg-slate-900/40">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300">
        <ScanSearch className="h-7 w-7" />
      </div>
      <h2 className="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-50">
        See what changed
      </h2>
      <ol className="mt-4 space-y-2 text-left text-sm text-slate-600 dark:text-slate-300">
        {steps.map((s, i) => (
          <li key={s} className="flex gap-3">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              {i + 1}
            </span>
            {s}
          </li>
        ))}
      </ol>
    </div>
  )
}

function Loading({ slow }) {
  return (
    <div className="space-y-5" aria-live="polite">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-2xl bg-slate-200/70 dark:bg-slate-800/70" />
        ))}
      </div>
      <div className="flex h-96 animate-pulse flex-col items-center justify-center rounded-2xl bg-slate-200/70 text-sm text-slate-600 dark:bg-slate-800/70 dark:text-slate-300">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-400 border-t-transparent" />
        <p className="mt-3 font-medium">Analyzing…</p>
        {slow && (
          <p className="mt-1 max-w-xs text-center text-xs">
            This is taking longer than usual. A hosted server may be waking up,
            which can take about a minute.
          </p>
        )}
      </div>
    </div>
  )
}

function ErrorBox({ message, onRetry }) {
  return (
    <div
      role="alert"
      className="flex min-h-[16rem] flex-col items-center justify-center rounded-2xl border border-red-200 bg-red-50 p-8 text-center dark:border-red-900 dark:bg-red-950/40"
    >
      <TriangleAlert className="h-8 w-8 text-red-500" />
      <h2 className="mt-3 text-base font-semibold text-red-900 dark:text-red-200">
        Something went wrong
      </h2>
      <p className="mt-1 max-w-md text-sm text-red-700 dark:text-red-300">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 rounded-lg bg-white px-4 py-2 text-sm font-medium text-red-700 shadow-sm ring-1 ring-red-200 hover:bg-red-100 dark:bg-slate-900 dark:text-red-300 dark:ring-red-800 dark:hover:bg-slate-800"
      >
        Try again
      </button>
    </div>
  )
}

function AlignBanner({ stats, requested }) {
  if (!requested) return null
  if (stats.aligned) {
    return (
      <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-2.5 text-sm text-emerald-800 ring-1 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-800">
        <CheckCircle2 className="h-4 w-4 shrink-0" />
        Aligned using {stats.inliers} matching points. Overlap with the first
        image: {stats.valid_percent}%.
      </div>
    )
  }
  return (
    <div className="flex items-center gap-2 rounded-xl bg-amber-50 px-4 py-2.5 text-sm text-amber-800 ring-1 ring-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:ring-amber-800">
      <TriangleAlert className="h-4 w-4 shrink-0" />
      Alignment failed ({stats.alignment_note || 'unknown reason'}). Showing the
      result without alignment.
    </div>
  )
}

const btn =
  'inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50 dark:text-slate-200 dark:ring-slate-700 dark:hover:bg-slate-800'

export default function Results({ status, result, error, slow, tab, setTab, onRetry }) {
  if (status === 'loading') return <Loading slow={slow} />
  if (status === 'error') return <ErrorBox message={error} onRetry={onRetry} />
  if (!result) return <Empty />

  const { stats, timing, images, settings } = result
  const tabs = images.matches
    ? [...BASE_TABS, { id: 'align', label: 'Alignment', icon: Crosshair }]
    : BASE_TABS
  const active = tabs.some((t) => t.id === tab) ? tab : 'overlay'
  const frame = { aspectRatio: `${stats.width} / ${stats.height}` }
  const dl = DOWNLOAD[active]

  return (
    <div className="fade-up space-y-5">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          icon={Percent}
          label="Changed"
          sub={stats.aligned ? 'of the overlapping area' : 'of all pixels'}
        >
          <AnimatedNumber value={stats.change_percent} decimals={2} suffix="%" />
        </StatCard>
        <StatCard icon={Shapes} label="Regions" sub="above the minimum area">
          <AnimatedNumber value={stats.regions} />
        </StatCard>
        <StatCard
          icon={SlidersHorizontal}
          label="Threshold"
          sub={settings.threshold === null ? 'chosen automatically (Otsu)' : 'set manually'}
        >
          {Math.round(stats.threshold)}
        </StatCard>
        <StatCard
          icon={Timer}
          label="Time"
          sub={
            <>
              pipeline {timing.pipeline_ms} ms
              <br />
              round trip {Math.round(result.clientMs)} ms
            </>
          }
        >
          {Math.round(timing.request_ms)} ms
        </StatCard>
      </div>

      <AlignBanner stats={stats} requested={settings.align} />

      <div className={`${cardClass} p-4`}>
        <div
          role="tablist"
          aria-label="Result views"
          className="mb-4 flex gap-1 overflow-x-auto rounded-xl bg-slate-100 p-1 dark:bg-slate-800"
        >
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={active === id}
              onClick={() => setTab(id)}
              className={`flex shrink-0 items-center gap-2 rounded-lg px-3.5 py-1.5 text-sm font-medium transition ${
                active === id
                  ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-600 dark:text-white'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white'
              }`}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </div>

        {['overlay', 'mask', 'heatmap'].includes(active) && (
          <img
            src={images[active]}
            alt={`${active} result`}
            style={frame}
            className="w-full rounded-xl bg-slate-900 object-contain"
          />
        )}

        {active === 'compare' && (
          <CompareSlider
            left={images.before}
            right={images.after}
            leftLabel="Before"
            rightLabel={settings.align && stats.aligned ? 'After (aligned)' : 'After'}
            width={stats.width}
            height={stats.height}
          />
        )}

        {active === 'align' && (
          <div className="space-y-4">
            <CompareSlider
              left={images.blend_raw}
              right={images.blend_aligned}
              leftLabel="Before alignment"
              rightLabel="After alignment"
              width={stats.width}
              height={stats.height}
            />
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Matched points
              </p>
              <img
                src={images.matches}
                alt="Keypoint matches between the two images"
                className="w-full rounded-xl bg-slate-900"
              />
            </div>
          </div>
        )}

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <p className={mutedClass}>
            {settings.method === 'ssim' ? 'SSIM' : 'Difference'} · blur {settings.blur} ·
            minimum area {settings.min_area}px · lighting {settings.normalize} ·
            processed at {stats.width}×{stats.height}px
          </p>
          <div className="flex gap-2">
            <button
              type="button"
              className={btn}
              onClick={() =>
                saveHref(images[dl.key], `change-detection_${active}.${dl.ext}`)
              }
            >
              <Download className="h-4 w-4" />
              Image
            </button>
            <button
              type="button"
              className={btn}
              onClick={() =>
                saveJson({ stats, timing, settings }, 'change-detection_summary.json')
              }
            >
              <FileJson className="h-4 w-4" />
              Summary
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}