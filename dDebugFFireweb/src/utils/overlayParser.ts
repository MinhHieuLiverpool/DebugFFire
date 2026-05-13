export interface TeamProgress {
  team: string
  logo: string
  killsPerZone: Record<number, number>
  eliminatedZone?: number
  eliminatedTime?: string
  isWinner: boolean
  booyahZone?: number
}

export interface OverlayData {
  teams: TeamProgress[]
  zones: {
    number: number
    start: string
    end?: string
  }[]
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
  const upper = name.toUpperCase()
  // Common environment deaths to ignore as killers
  if (['ZONE', 'BLED OUT', 'FALL DAMAGE', 'VEHICLE', 'EXPLOSION'].includes(upper)) return ''
  
  const dot = upper.indexOf('.')
  if (dot === -1) return upper
  return upper.slice(0, dot)
}

export const parseOverlayData = (rawText: string): OverlayData => {
  if (!rawText.trim()) return { teams: [], zones: [] }

  const lines = rawText.split(/\r?\n/)
  const zones: { number: number; start: string; end?: string }[] = []
  const teamStats: Map<string, TeamProgress> = new Map()

  let currentZone: number | null = null

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue

    const timestamp = extractTimestamp(trimmed)
    const body = stripTimestamp(trimmed)

    // Zone detection
    const stableMatch = body.match(ZONE_STABLE)
    const preMatch = body.match(ZONE_PRE_SHRINK)
    const zoneMatch = stableMatch ?? preMatch
    if (zoneMatch) {
      const zoneNumber = Number(zoneMatch[1])
      currentZone = zoneNumber

      const existingZoneIndex = zones.findIndex(z => z.number === zoneNumber)
      if (existingZoneIndex !== -1) {
        // If we found a repeat of a zone number, we don't add it again,
        // but it effectively extends the current zone's duration.
      } else {
        // Close previous zone
        if (zones.length > 0 && !zones[zones.length - 1].end) {
          zones[zones.length - 1].end = timestamp
        }
        
        zones.push({
          number: zoneNumber,
          start: timestamp,
        })
      }
      continue
    }

    if (currentZone === null) continue

    // Kill event
    const killMatch = body.match(KILL_EVENT)
    if (killMatch) {
      const victimFullName = killMatch[1]
      const killerFullName = killMatch[2]
      
      const victimTeam = extractTeam(victimFullName)
      const killerTeam = extractTeam(killerFullName)
      
      // Skip if suicide (same person) or team kill (same team)
      if (killerTeam && killerTeam !== victimTeam && killerFullName.toUpperCase() !== victimFullName.toUpperCase()) {
        if (!teamStats.has(killerTeam)) {
          teamStats.set(killerTeam, {
            team: killerTeam,
            logo: killerTeam === 'ARG' ? 'ACD' : killerTeam,
            killsPerZone: {},
            isWinner: false,
          })
        }
        const stat = teamStats.get(killerTeam)!
        stat.killsPerZone[currentZone] = (stat.killsPerZone[currentZone] || 0) + 1
      }
    }

    // Team cleared
    const clearedMatch = body.match(TEAM_CLEARED)
    if (clearedMatch) {
      const teamName = clearedMatch[1].toUpperCase()
      if (!teamStats.has(teamName)) {
        teamStats.set(teamName, {
          team: teamName,
          logo: teamName === 'ARG' ? 'ACD' : teamName,
          killsPerZone: {},
          isWinner: false,
        })
      }
      const stat = teamStats.get(teamName)!
      // Only set elimination if not already set
      if (!stat.eliminatedTime) {
        stat.eliminatedZone = currentZone
        stat.eliminatedTime = timestamp
      }
    }

    // Booyah
    const booyahMatch = body.match(BOOYAH_EVENT)
    if (booyahMatch) {
      const teamName = booyahMatch[1].toUpperCase()
      if (!teamStats.has(teamName)) {
        teamStats.set(teamName, {
          team: teamName,
          logo: teamName === 'ARG' ? 'ACD' : teamName,
          killsPerZone: {},
          isWinner: false,
        })
      }
      const stat = teamStats.get(teamName)!
      stat.isWinner = true
      stat.booyahZone = currentZone
      stat.eliminatedZone = currentZone
      stat.eliminatedTime = timestamp
    }
  }

  // Ensure last zone has an end if possible
  if (zones.length > 0 && !zones[zones.length - 1].end) {
    const lastTimestamp = lines.length > 0 ? extractTimestamp(lines[lines.length - 1]) : ''
    if (lastTimestamp) {
       zones[zones.length - 1].end = lastTimestamp
    }
  }

  return {
    zones,
    teams: Array.from(teamStats.values()).sort((a, b) => {
        // Sort winner first, then by eliminated zone (descending), then by kills
        if (a.isWinner) return -1
        if (b.isWinner) return 1
        const aZone = a.eliminatedZone || 0
        const bZone = b.eliminatedZone || 0
        if (aZone !== bZone) return bZone - aZone
        const aKills = Object.values(a.killsPerZone).reduce((s, v) => s + v, 0)
        const bKills = Object.values(b.killsPerZone).reduce((s, v) => s + v, 0)
        return bKills - aKills
    }),
  }
}
