export type TeamStat = {
  team: string
  kills: number
  cleared: boolean
}

export type ZoneStat = {
  zone: number
  start: string
  end?: string
  teams: TeamStat[]
  totalKills: number
  booyahTeam?: string
  booyahTime?: string
}

const ZONE_PRE_SHRINK = /Zone\s+(\d+)\s+trang\s+thai:\s*ZONE_TYPE_PRE_SHRINK/i
const ZONE_STABLE = /Zone\s+(\d+)\s+trang\s+thai:\s*ZONE_TYPE_STABLE/i
const KILL_EVENT = /(\S+)\s+KILLED BY\s+(\S+)/i
const TEAM_CLEARED = /Team\s+(\S+)\s+CLEARED/i
const BOOYAH_EVENT = /BOOYAH\s*-\s*Team:\s*(\S+)/i

const extractTimestamp = (line: string) => {
  const match = line.match(/^\[([^\]]+)\]/)
  return match?.[1] ?? ''
}

const stripTimestamp = (line: string) => line.replace(/^\[[^\]]+\]\s*/, '')

const extractTeam = (name: string) => {
  if (!name) return ''
  const dot = name.indexOf('.')
  if (dot === -1) return ''
  return name.slice(0, dot)
}

const getOrCreateTeam = (map: Map<string, TeamStat>, team: string) => {
  if (!team) return null
  const existing = map.get(team)
  if (existing) return existing
  const created = { team, kills: 0, cleared: false }
  map.set(team, created)
  return created
}

export const parseZones = (rawText: string): ZoneStat[] => {
  if (!rawText.trim()) return []

  const lines = rawText.split(/\r?\n/)
  const zones: Array<{
    zone: number
    start: string
    end?: string
    teams: Map<string, TeamStat>
    totalKills: number
    booyahTeam?: string
    booyahTime?: string
  }> = []
  let current: (typeof zones)[number] | null = null

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue

    const timestamp = extractTimestamp(trimmed)
    const body = stripTimestamp(trimmed)

    const stableMatch = body.match(ZONE_STABLE)
    const preMatch = body.match(ZONE_PRE_SHRINK)
    const zoneMatch = stableMatch ?? preMatch
    if (zoneMatch) {
      const zoneNumber = Number(zoneMatch[1])
      if (
        current &&
        current.zone === zoneNumber &&
        current.start === (timestamp || current.start)
      ) {
        continue
      }
      if (current && !current.end && timestamp) {
        current.end = timestamp
      }
      current = {
        zone: zoneNumber,
        start: timestamp || 'Unknown',
        teams: new Map(),
        totalKills: 0,
      }
      zones.push(current)
      continue
    }

    if (!current) continue

    const killMatch = body.match(KILL_EVENT)
    if (killMatch) {
      const victimTeam = extractTeam(killMatch[1])
      const killerTeam = extractTeam(killMatch[2])
      if (killerTeam && victimTeam && killerTeam === victimTeam) {
        continue
      }
      const stat = getOrCreateTeam(current.teams, killerTeam)
      if (stat) {
        stat.kills += 1
        current.totalKills += 1
      }
    }

    const clearedMatch = body.match(TEAM_CLEARED)
    if (clearedMatch) {
      const teamName = clearedMatch[1]
      const stat = getOrCreateTeam(current.teams, teamName)
      if (stat) {
        stat.cleared = true
      }
    }

    const booyahMatch = body.match(BOOYAH_EVENT)
    if (booyahMatch && !current.booyahTeam) {
      current.booyahTeam = booyahMatch[1]
      if (timestamp) {
        current.booyahTime = timestamp
      }
    }
  }

  return zones.map((zone) => {
    const teams = Array.from(zone.teams.values())
      .sort((a, b) => {
        if (b.kills !== a.kills) return b.kills - a.kills
        return a.team.localeCompare(b.team)
      })
      .slice(0, 12)

    return {
      zone: zone.zone,
      start: zone.start,
      end: zone.end,
      teams,
      totalKills: zone.totalKills,
      booyahTeam: zone.booyahTeam,
      booyahTime: zone.booyahTime,
    }
  })
}
