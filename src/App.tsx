import { useEffect, useMemo, useState } from 'react';
import BandLogo from './components/BandLogo';
import BirthdayPass from './components/BirthdayPass';
import rawData from './data/characters.json';
import { assetUrl } from './lib/asset';
import { bandColor, bandSpectrum, monthAbbr } from './lib/bandTheme';
import { buildTickets, formatToday, msUntilNextMidnight, startOfDay } from './lib/schedule';
import type { CharacterData, Ticket } from './types';

const data = rawData as CharacterData;

/** 밴드 목록이 바뀌면 배너 스펙트럼도 같이 따라오도록 데이터에서 만든다. */
const spectrum = bandSpectrum(data.bands.map((band) => band.id));

const ALL = 'all';

/**
 * 기본은 실제 오늘. `?today=YYYY-MM-DD` 쿼리가 있으면 그 날짜로 본다 —
 * 생일 당일 화면을 확인할 때 쓴다.
 */
function resolveToday(): Date {
  const raw = new URLSearchParams(window.location.search).get('today');
  const parsed = raw ? /^(\d{4})-(\d{2})-(\d{2})$/.exec(raw) : null;
  if (parsed) {
    const overridden = new Date(Number(parsed[1]), Number(parsed[2]) - 1, Number(parsed[3]));
    if (!Number.isNaN(overridden.getTime())) return overridden;
  }
  return startOfDay(new Date());
}

/** 날이 바뀌면 D-day가 저절로 갱신되도록 자정에 한 번 리렌더한다. */
function useToday(): Date {
  const [today, setToday] = useState(resolveToday);
  const isOverridden = useMemo(
    () => new URLSearchParams(window.location.search).has('today'),
    [],
  );

  useEffect(() => {
    if (isOverridden) return;
    const timer = window.setTimeout(
      () => setToday(startOfDay(new Date())),
      msUntilNextMidnight(new Date()) + 1000,
    );
    return () => window.clearTimeout(timer);
  }, [today, isOverridden]);

  return today;
}

/** 다가오는 생일 한 줄. 오늘 생일인 캐릭터는 패스 카드로 따로 나가므로 여기 오지 않는다. */
function TicketRow({ ticket }: { ticket: Ticket }) {
  const { character, daysUntil, month, day } = ticket;
  const color = bandColor(character.bandId);

  return (
    <article className="ticket" style={{ ['--band-color' as string]: color }}>
      <div className="ticket__stub">
        <span className="ticket__month">{monthAbbr(month)}</span>
        <span className="ticket__day">{day}</span>
      </div>

      <div className="ticket__body">
        {character.image ? (
          <img className="ticket__face" src={assetUrl(character.image)} alt="" width={52} height={52} />
        ) : (
          <span className="ticket__face ticket__face--empty" aria-hidden="true">
            {character.nameKo.slice(0, 1)}
          </span>
        )}

        <h2 className="ticket__name">{character.nameKo}</h2>

        <BandLogo bandId={character.bandId} className="ticket__logo" />

        <div className="ticket__dday">
          <span className="ticket__dday-num">{daysUntil}</span>
          <span className="ticket__dday-unit">DAYS</span>
        </div>
      </div>
    </article>
  );
}

export default function App() {
  const today = useToday();
  const [bandFilter, setBandFilter] = useState<string>(ALL);

  const allTickets = useMemo(() => buildTickets(data.characters, today), [today]);

  const tickets = useMemo(
    () =>
      bandFilter === ALL
        ? allTickets
        : allTickets.filter((t) => t.character.bandId === bandFilter),
    [allTickets, bandFilter],
  );

  const unknown = useMemo(
    () =>
      data.characters.filter(
        (c) => !c.birthday && (bandFilter === ALL || c.bandId === bandFilter),
      ),
    [bandFilter],
  );

  const todayTickets = tickets.filter((t) => t.daysUntil === 0);
  const upcoming = tickets.filter((t) => t.daysUntil > 0);
  const nextTicket = upcoming[0];

  return (
    <div className="page">
      <header className="banner">
        <div className="banner__row">
          <h1 className="banner__mark">
            BanG DREAM<em>!</em> BIRTHDAY
          </h1>
          <p className="banner__date">{formatToday(today)}</p>
        </div>
        <div
          className="banner__spectrum"
          style={{ backgroundImage: spectrum }}
          aria-hidden="true"
        />
      </header>

      {todayTickets.length > 0 ? (
        <section
          className="pass-stage"
          style={{ ['--band-color' as string]: bandColor(todayTickets[0].character.bandId) }}
          aria-label="오늘 생일"
        >
          {todayTickets.map((ticket) => (
            <BirthdayPass key={ticket.character.id} ticket={ticket} />
          ))}
        </section>
      ) : (
        <p className="lede">
          {nextTicket ? (
            <>
              오늘은 생일인 캐릭터가 없어. 가장 가까운 생일은{' '}
              <strong>{nextTicket.character.nameKo}</strong> — D-{nextTicket.daysUntil}
            </>
          ) : (
            <>이 필터에는 아직 생일이 확인된 캐릭터가 없어.</>
          )}
        </p>
      )}

      <nav className="filters" aria-label="밴드 필터">
        <button
          type="button"
          className={bandFilter === ALL ? 'chip chip--on' : 'chip'}
          aria-pressed={bandFilter === ALL}
          onClick={() => setBandFilter(ALL)}
        >
          전체
        </button>
        {data.bands.map((band) => (
          <button
            key={band.id}
            type="button"
            className={bandFilter === band.id ? 'chip chip--on' : 'chip'}
            aria-pressed={bandFilter === band.id}
            style={{ ['--band-color' as string]: bandColor(band.id) }}
            onClick={() => setBandFilter(band.id)}
          >
            {band.name}
          </button>
        ))}
      </nav>

      <main className="strip">
        {upcoming.map((ticket) => (
          <TicketRow key={ticket.character.id} ticket={ticket} />
        ))}
      </main>

      {unknown.length > 0 && (
        <section className="pending">
          <h2 className="pending__title">생일 미공개 · {unknown.length}명</h2>
          <p className="pending__note">
            공식 프로필에서 생일을 확인하지 못한 캐릭터야. 확인되는 대로 티켓에 합류해.
          </p>
          <ul className="pending__list">
            {unknown.map((c) => (
              <li key={c.id} className="pending__item">
                <span
                  className="pending__dot"
                  style={{ ['--band-color' as string]: bandColor(c.bandId) }}
                />
                {c.nameKo}
                <em>{c.bandName}</em>
              </li>
            ))}
          </ul>
        </section>
      )}

    </div>
  );
}
