import { type ChangeEvent, useMemo, useState } from 'react'
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

  return (
    <section className="flex flex-col gap-6">
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
