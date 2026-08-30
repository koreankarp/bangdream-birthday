/**
 * 밴드별 표시 색상.
 *
 * 주의: 이 값들은 UI 토큰이고 공식 발표 컬러코드가 아니다 — 각 밴드의 통상적인
 * 이미지 컬러를 눈대중으로 맞춘 근사값이다. 공식 컬러가 확인되면 여기만 고치면 된다.
 */
const BAND_COLORS: Record<string, string> = {
  'poppin-party': '#ff6392',
  afterglow: '#df5a5a',
  'pastel-palettes': '#6fd8c4',
  roselia: '#6f5fc4',
  'hello-happy-world': '#f5c53f',
  morfonica: '#4fa3de',
  'raise-a-suilen': '#3fbfa8',
  mygo: '#7fbf8f',
  'ave-mujica': '#9a5fc9',
  'mugendai-mewtype': '#ef7fb8',
  millsage: '#8fa6d8',
  'ikka-dumb-rock': '#f0885a',
};

const FALLBACK_COLOR = '#8a8ca4';

export function bandColor(bandId: string): string {
  return BAND_COLORS[bandId] ?? FALLBACK_COLOR;
}

/**
 * 배너의 밴드 컬러 스펙트럼용 linear-gradient 문자열.
 * 색을 섞지 않고 각 밴드가 같은 폭의 단색 구간을 갖도록 stop 을 두 번씩 찍는다.
 */
export function bandSpectrum(bandIds: string[]): string {
  if (bandIds.length === 0) return FALLBACK_COLOR;

  const step = 100 / bandIds.length;
  const stops = bandIds.flatMap((id, index) => {
    const color = bandColor(id);
    return [`${color} ${(index * step).toFixed(3)}%`, `${color} ${((index + 1) * step).toFixed(3)}%`];
  });

  return `linear-gradient(90deg, ${stops.join(', ')})`;
}

/**
 * 로고가 어두워서 다크 배경(#1b1d28)에 묻히는 밴드만 CSS filter 로 보정한다.
 * 실제 이미지를 눈으로 확인하고 정한 값이다.
 * - afterglow: 원본이 순수 검정 스크립트라 brightness 로는 살아나지 않는다 → 반전해 흰색으로.
 * - roselia / millsage: 짙은 남색·자색 단색이라 밝기만 올려 색조를 유지한다.
 * - ave-mujica / raise-a-suilen: 밝은 부분과 검은 부분이 섞여 있어 반전·증폭 대신
 *   흰 후광을 깔아 검은 획의 윤곽만 살린다.
 */
const LOGO_FILTERS: Record<string, string> = {
  afterglow: 'invert(1)',
  roselia: 'brightness(1.85) saturate(1.15)',
  millsage: 'brightness(1.9) saturate(1.1)',
  'ave-mujica': 'drop-shadow(0 0 2px rgba(255, 255, 255, 0.5))',
  'raise-a-suilen': 'drop-shadow(0 0 2px rgba(255, 255, 255, 0.55))',
};

export function logoFilter(bandId: string): string | null {
  return LOGO_FILTERS[bandId] ?? null;
}

const MONTH_ABBR = [
  'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
  'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
];

export function monthAbbr(month: number): string {
  return MONTH_ABBR[month - 1] ?? '???';
}
