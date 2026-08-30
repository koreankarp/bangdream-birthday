import type { Character, Ticket } from '../types';

const DAY_MS = 24 * 60 * 60 * 1000;

/** 시/분/초를 떨어낸 로컬 자정 기준 Date */
export function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function parseBirthday(birthday: string): { month: number; day: number } | null {
  const match = /^(\d{2})-(\d{2})$/.exec(birthday);
  if (!match) return null;
  const month = Number(match[1]);
  const day = Number(match[2]);
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  return { month, day };
}

/**
 * 오늘(포함) 이후 가장 빠른 생일 날짜를 구한다.
 * 2/29처럼 해당 연도에 존재하지 않는 날짜는 실제로 존재하는 다음 해로 넘긴다.
 */
export function nextOccurrence(month: number, day: number, today: Date): Date {
  const base = startOfDay(today);
  for (let offset = 0; offset <= 8; offset += 1) {
    const year = base.getFullYear() + offset;
    const candidate = new Date(year, month - 1, day);
    // 존재하지 않는 날짜는 JS가 다음 달로 굴려버리므로 되돌아왔는지 확인한다.
    const isRealDate = candidate.getMonth() === month - 1 && candidate.getDate() === day;
    if (isRealDate && candidate.getTime() >= base.getTime()) {
      return candidate;
    }
  }
  // 도달할 수 없는 경로지만 타입을 위해 남겨둔다.
  return new Date(base.getFullYear(), month - 1, day);
}

export function daysBetween(from: Date, to: Date): number {
  return Math.round((startOfDay(to).getTime() - startOfDay(from).getTime()) / DAY_MS);
}

/** 생일이 확정된 캐릭터만 티켓으로 만들고, D-day 오름차순으로 정렬한다. */
export function buildTickets(characters: Character[], today: Date): Ticket[] {
  const tickets: Ticket[] = [];

  for (const character of characters) {
    if (!character.birthday) continue;
    const parsed = parseBirthday(character.birthday);
    if (!parsed) continue;

    const nextDate = nextOccurrence(parsed.month, parsed.day, today);
    tickets.push({
      character,
      daysUntil: daysBetween(today, nextDate),
      month: parsed.month,
      day: parsed.day,
      nextDate,
    });
  }

  tickets.sort((a, b) => {
    if (a.daysUntil !== b.daysUntil) return a.daysUntil - b.daysUntil;
    // 같은 날이면 밴드 → 이름 순으로 안정적으로 정렬한다.
    if (a.character.bandId !== b.character.bandId) {
      return a.character.bandId.localeCompare(b.character.bandId);
    }
    return a.character.nameKo.localeCompare(b.character.nameKo, 'ko');
  });

  return tickets;
}

export function formatToday(date: Date): string {
  const weekday = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'][date.getDay()];
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yyyy}.${mm}.${dd} ${weekday}`;
}

/** 다음 자정까지 남은 밀리초 — 날이 바뀌면 D-day를 다시 계산하기 위해 쓴다. */
export function msUntilNextMidnight(now: Date): number {
  const nextMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  return nextMidnight.getTime() - now.getTime();
}
