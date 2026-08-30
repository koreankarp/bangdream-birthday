/**
 * 데이터에 저장된 에셋 경로('/characters/x.webp')를 배포 base 기준으로 바꾼다.
 *
 * GitHub Pages 프로젝트 페이지는 /<repo>/ 하위에서 서빙되므로, 절대 경로를 그대로 쓰면
 * 도메인 루트를 가리켜 404 가 된다. import.meta.env.BASE_URL 은 항상 '/' 로 끝난다.
 */
export function assetUrl(path: string): string {
  return `${import.meta.env.BASE_URL}${path.replace(/^\/+/, '')}`;
}
