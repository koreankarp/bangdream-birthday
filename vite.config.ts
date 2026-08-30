import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// GitHub Pages 프로젝트 페이지는 /<repo>/ 하위에서 서빙되므로 base 를 맞춰야 한다.
// 로컬 개발과 루트 도메인 배포에서는 '/' 그대로 쓴다.
const base = process.env.BASE_PATH || '/';

export default defineConfig({
  base,
  plugins: [react()],
});
