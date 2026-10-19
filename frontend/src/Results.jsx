import {
  Layers, Contrast, Flame, ArrowLeftRight, Crosshair, Percent, Shapes,
  SlidersHorizontal, Timer, TriangleAlert, CheckCircle2, ScanSearch,
} from 'lucide-react'
import { AnimatedNumber, CompareSlider, StatCard } from './ui'

const BASE_TABS = [
  { id: 'overlay', label: 'Overlay', icon: Layers },
  { id: 'mask', label: 'Mask', icon: Contrast },
  { id: 'heatmap', label: 'Heatmap', icon: Flame },
  { id: 'compare', label: 'Compare', icon: ArrowLeftRight },
]

function Empty() {
  const steps = [
    'Upload a before and an after image of the same scene.',
    'Choose a method and adjust the settings.',
    'Press Analyze to see what changed.',
  ]
  return (
    <div className="flex min-h-[28rem] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white/60 p-8 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
        <ScanSearch className="h-7 w-7" />
      </div>
      <h2 className="mt-4 text-lg font-semibold text-slate-900">See what changed</h2>
      <ol className="mt-4 space-y-2 text-left text-sm text-slate-500">
        {steps.map((s, i) => (
          <li key={s} className="flex gap-3">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
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
          <div key={i} className="h-24 animate-pulse rounded-2xl bg-slate-200/70" />
        ))}
      </div>
      <div className="flex h-96 animate-pulse flex-col items-center justify-center rounded-2xl bg-slate-200/70 text-sm text-slate-500">
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
      className="flex min-h-[16rem] flex-col items-center justify-center rounded-2xl border border-red-200 bg-red-50 p-8 text-center"
    >
      <TriangleAlert className="h-8 w-8 text-red-500" />
      <h2 className="mt-3 text-base font-semibold text-red-900">Something went wrong</h2>
      <p className="mt-1 max-w-md text-sm text-red-700">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 rounded-lg bg-white px-4 py-2 text-sm font-medium text-red-700 shadow-sm ring-1 ring-red-200 hover:bg-red-100"
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
      <div className="flex items-center gap-2 rounded-xl bg-emerald-50 px-4 py-2.5 text-sm text-emerald-800 ring-1 ring-emerald-200">
        <CheckCircle2 className="h-4 w-4 shrink-0" />
        Aligned using {stats.inliers} matching points. Overlap with the first
        image: {stats.valid_percent}%.
      </div>
    )
  }
  return (
    <div className="flex items-center gap-2 rounded-xl bg-amber-50 px-4 py-2.5 text-sm text-amber-800 ring-1 ring-amber-200">
      <TriangleAlert className="h-4 w-4 shrink-0" />
      Alignment failed ({stats.alignment_note || 'unknown reason'}). Showing the
      result without alignment.
    </div>
  )
}

export default function Results({
  status, result, error, slow, tab, setTab, onRetry,
}) {
  if (status === 'loading') return <Loading slow={slow} />
  if (status === 'error') return <ErrorBox message={error} onRetry={onRetry} />
  if (!result) return <Empty />

  const { stats, timing, images, settings } = result
  const tabs = images.matches
    ? [...BASE_TABS, { id: 'align', label: 'Alignment', icon: Crosshair }]
    : BASE_TABS
  const active = tabs.some((t) => t.id === tab) ? tab : 'overlay'
  const frame = { aspectRatio: `${stats.width} / ${stats.height}` }

  return (
    <div className="space-y-5">
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
          sub={`pipeline ${timing.pipeline_ms} ms · round trip ${Math.round(result.clientMs)} ms`}
        >
          {Math.round(timing.request_ms)} ms
        </StatCard>
      </div>

      <AlignBanner stats={stats} requested={settings.align} />

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div
          role="tablist"
          aria-label="Result views"
          className="mb-4 flex gap-1 overflow-x-auto rounded-xl bg-slate-100 p-1"
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
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-800'
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
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
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

        <p className="mt-3 text-xs text-slate-400">
          {settings.method === 'ssim' ? 'SSIM' : 'Difference'} · blur {settings.blur} ·
          minimum area {settings.min_area}px · lighting {settings.normalize} ·
          processed at {stats.width}×{stats.height}px
        </p>
      </div>
    </div>
  )
}