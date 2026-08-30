import { assetUrl } from '../lib/asset';
import { logoFilter } from '../lib/bandTheme';
import { bandOf } from '../lib/bands';

/**
 * 밴드 로고 이미지. 로고 파일이 없거나 로딩에 실패하면 밴드명 텍스트로 되돌아간다.
 *
 * 로고는 어두운 배경 위에 올라가므로, 어두운 로고는 bandTheme 의 LOGO_FILTERS 에서
 * 밴드별로 보정한다.
 */
export default function BandLogo({
  bandId,
  className,
}: {
  bandId: string;
  className: string;
}) {
  const band = bandOf(bandId);
  if (!band) return null;

  if (!band.logo) {
    return <span className={`${className} ${className}--text`}>{band.name}</span>;
  }

  const filter = logoFilter(bandId);

  return (
    <img
      className={className}
      src={assetUrl(band.logo)}
      alt={band.name}
      style={filter ? { filter } : undefined}
      loading="lazy"
    />
  );
}
