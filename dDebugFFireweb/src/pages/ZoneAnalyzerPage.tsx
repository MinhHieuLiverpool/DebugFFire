import { type ChangeEvent, useMemo, useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import SummaryCard from '../components/SummaryCard'
import ZoneTable from '../components/ZoneTable'
import { parseZones } from '../utils/zoneParser'

const ZoneAnalyzerPage = () => {
  const [rawText, setRawText] = useState('')
  const [fileName, setFileName] = useState('')

  const teams = [
    'ACD',
    'AG',
    'AUR',
    'AVD',
    'BRU',
    'BTR',
    'EVOS',
    'FL',
    'FLCN',
    'GOW',
    'HEV',
    'MEC',
    'ONIC',
    'PE',
    'RRQ',
    'SE',
    'TWIS',
    'WAG',
  ]

  const zones = useMemo(() => parseZones(rawText), [rawText])
  const totalKills = zones.reduce((sum, zone) => sum + zone.totalKills, 0)

  const parseTimestamp = (value?: string) => {
    if (!value) return null
    const parsed = new Date(value.replace(' ', 'T'))
    return Number.isNaN(parsed.getTime()) ? null : parsed
  }

  const overallStart = zones[0]?.start
  const lastBooyah = [...zones].reverse().find((zone) => zone.booyahTime)?.booyahTime
  const overallStartDate = parseTimestamp(overallStart)
  const lastBooyahDate = parseTimestamp(lastBooyah)
  const totalMinutes =
    overallStartDate && lastBooyahDate
      ? Math.max(0, lastBooyahDate.getTime() - overallStartDate.getTime()) / 60000
      : null

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setFileName(file.name)

    const reader = new FileReader()
    reader.onload = () => {
      setRawText(String(reader.result || ''))
    }
    reader.readAsText(file)
  }

  const [isOverlayPlaying, setIsOverlayPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0) // Visual time 0-56
  const [speed, setSpeed] = useState(1)
  const timerRef = useRef<number | null>(null)

  const ZONE_DURATION = 5 
  const MAX_ZONES = 8
  const VIRTUAL_END_TIME = MAX_ZONES * ZONE_DURATION

  const startTime = useMemo(() => {
    if (zones.length === 0) return 0
    return new Date(zones[0].start.replace(' ', 'T')).getTime()
  }, [zones])

  const endTime = useMemo(() => {
    if (zones.length === 0) return 0
    const lastZone = zones[zones.length - 1]
    const endStr = lastZone.end || lastZone.start
    return new Date(endStr.replace(' ', 'T')).getTime() + 60000 
  }, [zones])

  useEffect(() => {
    localStorage.setItem('overlay_playing', String(isOverlayPlaying))
    localStorage.setItem('overlay_current_time', String(currentTime))
    localStorage.setItem('overlay_speed', String(speed))
    localStorage.setItem('overlay_start_time', '0')
    localStorage.setItem('overlay_end_time', String(VIRTUAL_END_TIME))
  }, [isOverlayPlaying, currentTime, speed, VIRTUAL_END_TIME])

  useEffect(() => {
    if (isOverlayPlaying) {
      const interval = 100 
      timerRef.current = window.setInterval(() => {
        setCurrentTime(prev => {
          const next = prev + (interval / 1000) * speed
          if (next >= VIRTUAL_END_TIME) {
            setIsOverlayPlaying(false)
            return VIRTUAL_END_TIME
          }
          return next
        })
      }, interval)
    } else {
      if (timerRef.current) clearInterval(timerRef.current)
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [isOverlayPlaying, speed, VIRTUAL_END_TIME])

  const restart = () => {
    setIsOverlayPlaying(false)
    setCurrentTime(0)
    localStorage.setItem('overlay_command', 'restart_' + Date.now())
  }

  return (
    <section className="flex flex-col gap-6">
      {zones.length > 0 && (
        <div className="bg-white/5 border border-white/10 rounded-2xl p-4 shadow-xl backdrop-blur-md flex flex-col gap-4">
          <div className="flex items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsOverlayPlaying(!isOverlayPlaying)}
                className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold transition active:scale-95 ${
                  isOverlayPlaying ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'
                }`}
              >
                {isOverlayPlaying ? 'Stop Overlay' : 'Start Overlay'}
              </button>
              
              <button 
                onClick={restart}
                className="px-6 py-2.5 rounded-xl font-bold bg-white/5 border border-white/10 hover:bg-white/10 transition"
              >
                Restart
              </button>

              <div className="h-8 w-[1px] bg-white/10 mx-2" />

              <div className="flex items-center gap-3">
                 <span className="text-xs text-white/40 uppercase font-bold">Speed</span>
                 <select 
                   value={speed} 
                   onChange={(e) => setSpeed(Number(e.target.value))}
                   className="bg-black/40 border border-white/10 rounded-lg px-2 py-1 text-sm outline-none"
                 >
                   {[1, 5, 10, 50, 100].map(s => <option key={s} value={s}>{s}x</option>)}
                 </select>
              </div>
            </div>

            <div className="flex gap-8">
              <div className="text-right">
                <div className="text-[10px] text-white/40 uppercase tracking-widest font-bold">Total Duration</div>
                <div className="text-lg font-mono font-bold">
                   {Math.floor((endTime - startTime) / 60000)}m {Math.floor(((endTime - startTime) % 60000) / 1000)}s
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-white/40 uppercase tracking-widest font-bold">Current Time</div>
                <div className="text-lg font-mono font-bold text-green-400">
                   {new Date(currentTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </div>
              </div>
            </div>
          </div>

          <div className="px-2">
            <input 
              type="range"
              min={startTime}
              max={endTime}
              value={currentTime}
              onChange={(e) => {
                setIsOverlayPlaying(false)
                setCurrentTime(Number(e.target.value))
              }}
              className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-green-400 hover:bg-white/20 transition"
            />
          </div>
        </div>
      )}

      <div className="flex items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-xl font-bold italic tracking-tight">MATCH DASHBOARD</h2>
          <p className="text-sm text-white/50">Manage match playback and real-time overlay data</p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/overlay"
            state={{ rawText }}
            target="_blank"
            className="group flex items-center gap-2 rounded-xl bg-electric/20 border border-electric/40 px-6 py-3 text-sm font-black text-electric transition hover:bg-electric/30 hover:scale-105 active:scale-95 shadow-[0_0_30px_rgba(103,65,202,0.2)]"
          >
            <span className="uppercase tracking-widest">Open Overlay</span>
            <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </Link>
        </div>
      </div>

      <div className="space-y-6 rounded-3xl border border-white/10 bg-white/5 p-6 shadow-[0_20px_60px_rgba(8,10,26,0.45)]">
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Nhap file</h2>
          <p className="text-sm text-white/60">
            Ho tro .txt hoac .log. Du lieu se xu ly truc tiep tren trinh duyet.
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-[0.7fr_1.3fr] lg:items-start">
          <label className="flex cursor-pointer flex-col gap-3 rounded-2xl border border-dashed border-white/20 bg-white/5 px-5 py-6 text-sm text-white/70 transition hover:border-white/40">
            <span className="text-xs uppercase tracking-[0.3em] text-white/50">Chon file</span>
            <span className="text-base font-medium text-white">
              {fileName || 'Keo tha hoac bam de chon file'}
            </span>
            <input
              type="file"
              accept=".txt,.log"
              className="hidden"
              onChange={handleFileChange}
            />
          </label>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs uppercase tracking-[0.25em] text-white/50">
              <span>Noi dung</span>
              <button
                type="button"
                className="rounded-full border border-white/10 px-3 py-1 text-[10px] uppercase tracking-[0.2em] text-white/60 transition hover:border-white/30 hover:text-white"
                onClick={() => {
                  setRawText('')
                  setFileName('')
                }}
              >
                Clear
              </button>
            </div>
            <textarea
              value={rawText}
              onChange={(event) => setRawText(event.target.value)}
              placeholder="Hoac paste log vao day..."
              className="min-h-[220px] w-full resize-y rounded-2xl border border-white/10 bg-black/30 p-4 text-sm leading-relaxed text-white/80 outline-none ring-1 ring-transparent transition focus:border-white/30 focus:ring-electric/40"
            />
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div className="flex flex-col gap-4">
          <p className="max-w-xl text-sm leading-relaxed text-white/70">
            Upload log text.txt, he thong se cat theo tung Zone (tu preshrink nay den
            preshrink tiep theo) va thong ke 12 team noi bat theo so kill.
          </p>
          <div className="grid gap-4 md:grid-cols-3">
            <SummaryCard label="Tong Zone" value={String(zones.length)} />
            <SummaryCard label="Tong Kill" value={String(totalKills)} />
            <SummaryCard
              label="Tong phut"
              value={totalMinutes !== null ? totalMinutes.toFixed(1) : '-'}
            />
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-base font-semibold">Danh sach team</h3>
            <span className="text-xs uppercase tracking-[0.25em] text-white/50">
              {teams.length} team
            </span>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {teams.map((team) => {
              const logoTeam = team === 'ARG' ? 'ACD' : team
              return (
              <div
                key={team}
                className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/20 px-3 py-2 text-sm text-white/90"
              >
                <img
                  src={`/LOGO RESIZE/${logoTeam}.png`}
                  alt={`${team} logo`}
                  className="h-9 w-9 rounded-lg bg-white/5 object-contain p-1"
                  loading="lazy"
                />
                <span className="text-sm font-medium">{team}</span>
              </div>
              )
            })}
          </div>
        </div>

        {zones.length === 0 ? (
          <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-center text-sm text-white/60">
            Chua tim thay zone preshrink nao. Kiem tra lai format log.
          </div>
        ) : (
          <div className="space-y-6">
            {zones.map((zone) => (
              <ZoneTable key={`${zone.zone}-${zone.start}`} zone={zone} />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

export default ZoneAnalyzerPage
