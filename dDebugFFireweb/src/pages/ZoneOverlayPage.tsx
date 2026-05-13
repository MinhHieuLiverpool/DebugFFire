import { useState, useMemo, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { parseOverlayData } from '../utils/overlayParser'

const ZoneOverlayPage = () => {
  const location = useLocation()
  const [rawText, setRawText] = useState(location.state?.rawText || '')

  // Playback state (synced from Analyzer)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState<number>(0)
  const [speed, setSpeed] = useState(10)

  const data = useMemo(() => parseOverlayData(rawText), [rawText])

  const startTime = useMemo(() => {
    if (data.zones.length === 0) return 0
    return new Date(data.zones[0].start.replace(' ', 'T')).getTime()
  }, [data])

  const endTime = useMemo(() => {
    if (data.zones.length === 0) return 0
    const lastZone = data.zones[data.zones.length - 1]
    const endStr = lastZone.end || lastZone.start
    return new Date(endStr.replace(' ', 'T')).getTime() + 60000
  }, [data])

  // Force transparent background for OBS browser source
  useEffect(() => {
    const prev = document.body.style.background
    document.body.style.background = 'transparent'
    document.documentElement.style.background = 'transparent'
    return () => {
      document.body.style.background = prev
      document.documentElement.style.background = ''
    }
  }, [])

  // Poll localStorage every 100ms for cross-tab sync (more reliable than storage events)
  useEffect(() => {
    const poll = () => {
      const savedTime = localStorage.getItem('overlay_current_time')
      if (savedTime) setCurrentTime(Number(savedTime))

      const command = localStorage.getItem('overlay_command')
      if (command?.startsWith('restart')) {
        localStorage.removeItem('overlay_command')
        setCurrentTime(Number(localStorage.getItem('overlay_start_time') || startTime))
      }
    }

    const interval = setInterval(poll, 100)
    poll() // immediate first read
    return () => clearInterval(interval)
  }, [startTime])

  const maxZones = 8
  const zoneIndices = Array.from({ length: maxZones }, (_, i) => i + 1)

  const getPercentInZone = (timeStr?: string, startStr?: string, endStr?: string) => {
    if (!timeStr || !startStr || !endStr) return 50
    try {
      const t = new Date(timeStr.replace(' ', 'T')).getTime()
      const s = new Date(startStr.replace(' ', 'T')).getTime()
      const e = new Date(endStr.replace(' ', 'T')).getTime()
      if (e <= s) return 50
      return Math.min(100, Math.max(0, ((t - s) / (e - s)) * 100))
    } catch (e) {
      return 50
    }
  }

  return (
    <div className="min-h-screen bg-transparent text-white font-['Space_Grotesk'] flex items-center justify-center">
      {rawText && (
        <div className="relative w-full max-w-[700px] mx-auto">
          {/* Header */}
          <div className="grid grid-cols-8">
            {zoneIndices.map((z) => (
              <div key={z} className="py-0.5 px-0.5">
                <div className="bg-[#f0c23a] text-black text-[9px] font-black italic py-0.5 px-1 text-center uppercase">
                  CIRCLE {z}
                </div>
              </div>
            ))}
          </div>

          {/* Grid Content */}
          <div className="relative pt-1 pb-2">
            {/* Vertical lines for zones - subtle */}
            <div className="absolute inset-0 grid grid-cols-8 pointer-events-none">
              {zoneIndices.map((z) => (
                <div key={z} className="border-r border-white/40 h-full last:border-r-0" />
              ))}
            </div>

            {/* Team Rows */}
            <div className="flex flex-col">
              {data.teams.map((team) => {
                const ZONE_DURATION = 5
                const MAX_ZONES = 8
                const TOTAL_VIRTUAL = ZONE_DURATION * MAX_ZONES
                
                // Helper to get virtual time (0-56) from real timestamp
                const getVirtualTime = (timestamp: string, zoneNum: number) => {
                  const zone = data.zones.find(z => z.number === zoneNum)
                  if (!zone) return (zoneNum - 1) * ZONE_DURATION + (ZONE_DURATION / 2)
                  const s = new Date(zone.start.replace(' ', 'T')).getTime()
                  const e = zone.end ? new Date(zone.end.replace(' ', 'T')).getTime() : s + 120000
                  const t = new Date(timestamp.replace(' ', 'T')).getTime()
                  const p = Math.min(1, Math.max(0, (t - s) / (e - s)))
                  return (zoneNum - 1) * ZONE_DURATION + p * ZONE_DURATION
                }

                const virtualElimTime = team.eliminatedTime ? getVirtualTime(team.eliminatedTime, team.eliminatedZone || 0) : Infinity
                const hasEliminated = currentTime >= virtualElimTime
                
                let currentPosPercent = 0
                if (hasEliminated) {
                  currentPosPercent = (virtualElimTime / TOTAL_VIRTUAL) * 100
                } else {
                  currentPosPercent = (currentTime / TOTAL_VIRTUAL) * 100
                }

                return (
                  <div key={team.team} className="relative h-10 group">
                    {/* Horizontal progress line - solid yellow */}
                    <div
                      className="absolute top-1/2 left-0 h-[1px] bg-[#f0c23a]"
                      style={{ width: `${currentPosPercent}%`, transition: 'width 120ms linear' }}
                    />

                    {/* Kills Indicators */}
                    {Object.entries(team.killsPerZone).map(([zoneStr, kills]) => {
                      const zone = parseInt(zoneStr)
                      if (zone > maxZones) return null
                      const triggerPos = (zone - 1) * 12.5 + (50 / 100) * 12.5
                      if (currentPosPercent < triggerPos) return null

                      return (
                        <div
                          key={zone}
                          className="absolute top-[52%] flex flex-col items-center"
                          style={{ left: `${triggerPos}%`, transform: 'translate(-50%, -50%)' }}
                        >
                          <div className="relative w-8 h-8 flex items-center justify-center">
                            <img
                              src="/img/kill.png"
                              alt="kill"
                              className="w-full h-full object-contain drop-shadow-[0_0_6px_rgba(240,194,58,0.8)]"
                            />
                            <span className="absolute -bottom-2 -right-1 text-[13px] font-black text-[#f0c23a]">X{kills}</span>
                          </div>
                        </div>
                      )
                    })}

                    {/* Logo Running - smooth via CSS transition */}
                    <div
                      className={`absolute top-1/2 flex flex-col items-center ${hasEliminated && team.isWinner ? 'z-50' : 'z-10'}`}
                      style={{
                        left: `${currentPosPercent}%`,
                        transform: 'translate(-50%, -50%)',
                        transition: 'left 120ms linear'
                      }}
                    >
                      <div className="relative group/logo flex flex-col items-center">
                        <div className="relative">
                          <img
                            src={`/LOGO RESIZE/${team.logo}.png`}
                            alt={team.team}
                            className="w-9 h-9 object-contain"
                            onError={(e) => { e.currentTarget.src = 'https://via.placeholder.com/60?text=' + team.team; }}
                          />
                          {hasEliminated && !team.isWinner && (
                            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                              <div className="w-full h-0.5 bg-red-500/90 rotate-45 absolute" />
                              <div className="w-full h-0.5 bg-red-500/90 -rotate-45 absolute" />
                            </div>
                          )}
                          {hasEliminated && team.isWinner && <div className="absolute inset-0 -z-10 animate-ping bg-yellow-500/30 rounded-full scale-125" />}
                        </div>

                        {hasEliminated && team.isWinner && (
                          <div className="absolute top-full left-0 right-0 flex justify-center -mt-1 pointer-events-none">
                            <div className="w-32 animate-bounce">
                              <img src="/img/booyah.png" alt="BOOYAH" className="w-full object-contain" />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ZoneOverlayPage
