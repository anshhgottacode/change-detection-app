import { useEffect, useRef, useState } from 'react'
import { ScanSearch } from 'lucide-react'
import { API_URL, analyze, getConfig, getHealth } from './api'
import { Dropzone, Segmented, Slider, Toggle } from './ui'
import Results from './Results'

const DEFAULTS = {
  method: 'diff',
  blur: 5,
  autoThreshold: true,
  threshold: 40,
  minArea: 200,
  maxWidth: 1280,
  align: false,
  normalize: 'none',
}

const Section = ({ title, children }) => (
  <section className="space-y-3">
    <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
      {title}
    </h2>
    {children}
  </section>
)

export default function App() {
  const [before, setBefore] = useState(null)
  const [after, setAfter] = useState(null)
  const [settings, setSettings] = useState(DEFAULTS)
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [slow, setSlow] = useState(false)
  const [tab, setTab] = useState('overlay')
  const [api, setApi] = useState('checking')
  const [maxMb, setMaxMb] = useState(10)
  const abortRef = useRef(null)

  const set = (key) => (value) => setSettings((s) => ({ ...s, [key]: value }))

  useEffect(() => {
    getHealth().then(() => setApi('online')).catch(() => setApi('offline'))
    getConfig().then((c) => setMaxMb(c.max_upload_mb)).catch(() => {})
  }, [])

  async function run() {
    if (!before || !after || status === 'loading') return
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setStatus('loading')
    setError('')
    setSlow(false)
    const started = performance.now()
    const timer = setTimeout(() => setSlow(true), 6000)

    try {
      const data = await analyze(before, after, settings, controller.signal)
      setResult({ ...data, clientMs: performance.now() - started })
      setTab('overlay')
      setStatus('done')
      setApi('online')
    } catch (e) {
      if (e.name === 'AbortError') return
      setError(e.message)
      setStatus('error')
    } finally {
      clearTimeout(timer)
    }
  }

  function cancel() {
    abortRef.current?.abort()
    setStatus(result ? 'done' : 'idle')
  }

  const ready = Boolean(before && after)
  const loading = status === 'loading'
  const dot = { online: 'bg-emerald-500', offline: 'bg-red-500', checking: 'bg-slate-300' }[api]

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white">
              <ScanSearch className="h-5 w-5" />
            </div>
            <span className="text-base font-semibold tracking-tight">Change Detection</span>
          </div>
          <div
            className="flex items-center gap-2 text-xs text-slate-500"
            title={API_URL}
          >
            <span className={`h-2 w-2 rounded-full ${dot}`} />
            API {api}
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:sticky lg:top-20 lg:self-start">
          <Section title="Images">
            <Dropzone label="Before" file={before} onFile={setBefore} maxMb={maxMb} />
            <Dropzone label="After" file={after} onFile={setAfter} maxMb={maxMb} />
          </Section>

          <Section title="Method">
            <Segmented
              label="Detection method"
              value={settings.method}
              onChange={set('method')}
              options={[
                { value: 'diff', label: 'Difference' },
                { value: 'ssim', label: 'SSIM' },
              ]}
            />
            <p className="text-xs text-slate-400">
              {settings.method === 'diff'
                ? 'Fast pixel-by-pixel comparison.'
                : 'Compares local structure. Slower, and thresholded differently.'}
            </p>
          </Section>

          <Section title="Preparation">
            <Toggle
              label="Align images"
              hint="Corrects camera movement (ORB features + RANSAC)."
              checked={settings.align}
              onChange={set('align')}
            />
            <div>
              <p className="mb-1.5 text-sm font-medium text-slate-700">Lighting correction</p>
              <Segmented
                label="Lighting correction"
                value={settings.normalize}
                onChange={set('normalize')}
                options={[
                  { value: 'none', label: 'Off' },
                  { value: 'clahe', label: 'CLAHE' },
                  { value: 'match', label: 'Match' },
                ]}
              />
            </div>
          </Section>

          <Section title="Sensitivity">
            <Toggle
              label="Automatic threshold"
              hint="Uses Otsu's method to choose the cutoff."
              checked={settings.autoThreshold}
              onChange={set('autoThreshold')}
            />
            <Slider
              label="Threshold"
              min={0}
              max={255}
              value={settings.threshold}
              disabled={settings.autoThreshold}
              onChange={set('threshold')}
              hint="Lower values flag smaller differences."
            />
          </Section>

          <details className="group">
            <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wide text-slate-400 hover:text-slate-600">
              Advanced
            </summary>
            <div className="mt-3 space-y-4">
              <Slider
                label="Blur"
                min={1}
                max={21}
                step={2}
                value={settings.blur}
                onChange={set('blur')}
                format={(v) => (v === 1 ? 'off' : `${v}×${v}`)}
                hint="Smooths noise before comparing."
              />
              <Slider
                label="Minimum region area"
                min={0}
                max={2000}
                step={10}
                value={settings.minArea}
                onChange={set('minArea')}
                format={(v) => `${v} px`}
                hint="Smaller regions are ignored."
              />
              <div>
                <p className="mb-1.5 text-sm font-medium text-slate-700">Processing width</p>
                <Segmented
                  label="Processing width"
                  value={settings.maxWidth}
                  onChange={set('maxWidth')}
                  options={[
                    { value: 640, label: '640' },
                    { value: 960, label: '960' },
                    { value: 1280, label: '1280' },
                  ]}
                />
              </div>
            </div>
          </details>

          {loading ? (
            <button
              type="button"
              onClick={cancel}
              className="w-full rounded-xl bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-200"
            >
              Cancel
            </button>
          ) : (
            <button
              type="button"
              onClick={run}
              disabled={!ready}
              className="w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
            >
              {ready ? 'Analyze' : 'Add both images to start'}
            </button>
          )}
        </aside>

        <section>
          <Results
            status={status}
            result={result}
            error={error}
            slow={slow}
            tab={tab}
            setTab={setTab}
            onRetry={run}
          />
        </section>
      </main>

      <footer className="mx-auto max-w-7xl px-4 pb-8 text-xs text-slate-400">
        Classical computer vision (OpenCV, scikit-image). The result shows
        differences between the images, not confirmed real-world changes.
      </footer>
    </div>
  )
}