import type { ZoneStat } from '../utils/zoneParser'

type ZoneTableProps = {
  zone: ZoneStat
}

const ZoneTable = ({ zone }: ZoneTableProps) => (
  <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
    <div className="flex flex-wrap items-baseline justify-between gap-3">
      <div>
        <h3 className="text-xl font-semibold text-white">Zone {zone.zone}</h3>
        <p className="text-xs uppercase tracking-[0.25em] text-white/50">
          Tu {zone.start} {zone.end ? `den ${zone.end}` : '(dang chay)'}
        </p>
      </div>
      <span className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs uppercase tracking-[0.25em] text-white/70">
        {zone.totalKills} kills
      </span>
    </div>

    <div className="mt-5 overflow-hidden rounded-2xl border border-white/10">
      <table className="w-full text-left text-sm">
        <thead className="bg-white/10 text-xs uppercase tracking-[0.25em] text-white/60">
          <tr>
            <th className="px-4 py-3">Team</th>
            <th className="px-4 py-3">Kills</th>
            <th className="px-4 py-3">Clear</th>
          </tr>
        </thead>
        <tbody>
          {zone.teams.length === 0 ? (
            <tr>
              <td colSpan={3} className="px-4 py-4 text-sm text-white/50">
                Khong co su kien kill hoac clear trong zone nay.
              </td>
            </tr>
          ) : (
            zone.teams.map((team) => (
              <tr key={team.team} className="border-t border-white/10 text-white/80">
                <td className="px-4 py-3 font-semibold text-white">{team.team}</td>
                <td className="px-4 py-3">{team.kills}</td>
                <td className="px-4 py-3">
                  {team.cleared ? (
                    <span className="rounded-full bg-rose-500/20 px-3 py-1 text-xs uppercase tracking-[0.2em] text-rose-200">
                      Cleared
                    </span>
                  ) : (
                    <span className="text-white/40">-</span>
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>

    <p className="mt-4 text-xs uppercase tracking-[0.2em] text-white/40">
      Hien thi toi da 12 team theo so kill.
    </p>
  </div>
)

export default ZoneTable
