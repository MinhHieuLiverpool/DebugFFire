import type { ZoneStat } from '../utils/zoneParser'

type ZoneTableProps = {
  zone: ZoneStat
}

const FIXED_TEAMS = [
  'BRU',
  'EVOS',
  'SE',
  'AVD',
  'TWIS',
  'HEV',
  'FLCN',
  'FL',
  'ONIC',
  'WAG',
  'AUR',
  'ARG',
]

const parseTimestamp = (value?: string) => {
  if (!value) return null
  const parsed = new Date(value.replace(' ', 'T'))
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

const formatTimeRange = (start?: string, end?: string) => {
  if (!start) return ''
  const [startDate, startTime] = start.split(' ')
  if (!end) {
    return `${startTime || start} - (dang chay) ( ${startDate || ''} )`
  }
  const [, endTime] = end.split(' ')
  return `${startTime || start} - ${endTime || end} ( ${startDate || ''} )`
}

const ZoneTable = ({ zone }: ZoneTableProps) => {
  const teamMap = new Map(zone.teams.map((team) => [team.team, team]))
  const tableTeams = FIXED_TEAMS.map((team) => ({
    team,
    stat: teamMap.get(team) ?? null,
  }))
  const booyahTeam = zone.booyahTeam
  const booyahLogoTeam = booyahTeam === 'ARG' ? 'ACD' : booyahTeam
  const startTime = parseTimestamp(zone.start)
  const booyahTime = parseTimestamp(zone.booyahTime)
  const booyahMinutes =
    startTime && booyahTime ? Math.max(0, booyahTime.getTime() - startTime.getTime()) / 60000 : null

  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-white">Zone {zone.zone}</h3>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-white/70">
            {formatTimeRange(zone.start, zone.end)}
          </p>
        </div>
        <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.25em] text-white/70">
          {zone.totalKills} kills
        </span>
      </div>

      <div className="mt-5 overflow-hidden rounded-2xl border border-white/10">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-white/10 text-xs uppercase tracking-[0.25em] text-white/60">
              <tr>
                <th className="px-4 py-3">Zone</th>
                <th className="px-4 py-3">Hang</th>
                {tableTeams.map(({ team }) => {
                  const logoTeam = team === 'ARG' ? 'ACD' : team
                  return (
                  <th key={team} className="px-3 py-3 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <img
                        src={`/LOGO RESIZE/${logoTeam}.png`}
                        alt={`${team} logo`}
                        className="h-9 w-9 rounded-lg bg-white/5 object-contain p-1"
                        loading="lazy"
                      />
                      <span className="text-[11px] font-semibold text-white/80">{team}</span>
                    </div>
                  </th>
                  )
                })}
              </tr>
            </thead>
            <tbody className="text-white/80">
              <tr className="border-t border-white/10">
                <td
                  rowSpan={3}
                  className="px-4 py-3 align-top text-sm font-semibold text-white"
                >
                  Zone {zone.zone}
                </td>
                <td className="px-4 py-3 text-xs uppercase tracking-[0.2em] text-white/60">
                  Booyah
                </td>
                {tableTeams.map(({ team }) => (
                  <td key={`${team}-booyah`} className="px-3 py-3 text-center">
                    {booyahTeam && booyahTeam === team ? (
                      <div className="flex items-center justify-center">
                        <img
                          src="/img/booyah.png"
                          alt="Booyah"
                          className="h-12 w-12 object-contain"
                          loading="lazy"
                        />
                      </div>
                    ) : (
                      <span className="text-white/30">-</span>
                    )}
                  </td>
                ))}
              </tr>
              <tr className="border-t border-white/10">
                <td className="px-4 py-3 text-xs uppercase tracking-[0.2em] text-white/60">
                  Kill
                </td>
                {tableTeams.map(({ team, stat }) => (
                  <td key={`${team}-kills`} className="px-3 py-3 text-center">
                    {stat ? (
                      <div className="flex items-center justify-center gap-2">
                        <img
                          src="/img/kill.png"
                          alt="Kill"
                          className="h-5 w-5 object-contain"
                          loading="lazy"
                        />
                        <span className="text-sm font-semibold text-white">x{stat.kills}</span>
                      </div>
                    ) : (
                      <span className="text-white/30">-</span>
                    )}
                  </td>
                ))}
              </tr>
              <tr className="border-t border-white/10">
                <td className="px-4 py-3 text-xs uppercase tracking-[0.2em] text-white/60">
                  Clear
                </td>
                {tableTeams.map(({ team, stat }) => (
                  <td key={`${team}-clear`} className="px-3 py-3 text-center">
                    {stat?.cleared ? (
                      <div className="relative inline-flex h-12 w-12 items-center justify-center">
                        <img
                          src={`/LOGO RESIZE/${team === 'ARG' ? 'ACD' : team}.png`}
                          alt={`${team} logo`}
                          className="h-11 w-11 rounded-lg bg-white/5 object-contain p-1"
                          loading="lazy"
                        />
                        <span className="absolute left-1/2 top-1/2 h-1 w-14 -translate-x-1/2 -translate-y-1/2 rotate-45 rounded-full bg-rose-400/90" />
                        <span className="absolute left-1/2 top-1/2 h-1 w-14 -translate-x-1/2 -translate-y-1/2 -rotate-45 rounded-full bg-rose-400/90" />
                      </div>
                    ) : (
                      <span className="text-white/30">-</span>
                    )}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <p className="mt-4 text-xs uppercase tracking-[0.2em] text-white/40">
        Hien thi toi da 12 team theo so kill.
      </p>
    </div>
  )
}

export default ZoneTable
