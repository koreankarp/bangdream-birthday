import BandLogo from './BandLogo';
import { assetUrl } from '../lib/asset';
import { bandColor } from '../lib/bandTheme';
import type { Ticket } from '../types';

/**
 * 오늘 생일인 캐릭터를 강조하는 패스 카드.
 * 티켓 목록과 같은 라이브 소품 세계관을 쓰되, 목걸이 스트랩·펀치홀·바코드로
 * '다른 물건'임을 만들어 한눈에 구분되게 한다.
 */
export default function BirthdayPass({ ticket }: { ticket: Ticket }) {
  const { character, month, day, daysUntil } = ticket;
  const isToday = daysUntil === 0;

  return (
    <article className="pass" style={{ ['--band-color' as string]: bandColor(character.bandId) }}>
      <div className="pass__lanyard">
        <span className="pass__hole" />
      </div>

      {character.image ? (
        <img className="pass__face" src={assetUrl(character.image)} alt="" width={152} height={152} />
      ) : (
        <span className="pass__face pass__face--empty" aria-hidden="true">
          {character.nameKo.slice(0, 1)}
        </span>
      )}

      {/* 당일이면 축하, 아니면 남은 일수를 같은 자리에 둔다 */}
      {isToday ? (
        <p className="pass__greeting">
          HAPPY
          <br />
          BIRTHDAY
        </p>
      ) : (
        <p className="pass__greeting pass__greeting--countdown">
          D-{daysUntil}
        </p>
      )}

      <h2 className="pass__name">{character.nameKo}</h2>
      <BandLogo bandId={character.bandId} className="pass__logo" />
      <span className="pass__date">
        {month}월 {day}일
      </span>

      <div className="pass__barcode" aria-hidden="true" />
    </article>
  );
}
