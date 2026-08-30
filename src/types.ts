export type Confidence = 'official' | 'secondary' | 'unknown';

export interface Band {
  id: string;
  name: string;
  category: string;
  /** public/bands 에서 찾은 로고 경로. 없으면 null */
  logo: string | null;
}

export interface Character {
  id: string;
  nameKo: string;
  stageName: string | null;
  bandId: string;
  bandName: string;
  roles: string[];
  /** "MM-DD", 아직 확인되지 않은 캐릭터는 null */
  birthday: string | null;
  confidence: Confidence;
  sourceName: string | null;
  sourceUrl: string | null;
  /** 목록용 썸네일 (200px 대) */
  image: string | null;
  /** 패스 카드용 고해상도 초상화 (1000px 대). 없으면 image 로 대체한다. */
  imageHd: string | null;
}

export interface CharacterData {
  generatedAt: string;
  bands: Band[];
  characters: Character[];
}

/** 생일이 확정된 캐릭터 + 오늘 기준 D-day 계산 결과 */
export interface Ticket {
  character: Character;
  /** 다음 생일까지 남은 일수. 오늘이면 0 */
  daysUntil: number;
  month: number;
  day: number;
  /** 다음 생일의 실제 날짜 (연도 포함) */
  nextDate: Date;
}
