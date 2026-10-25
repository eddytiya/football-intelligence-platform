// Apply the saved appearance before CSS paints, including on deep links.
try {
  const saved = localStorage.getItem('football-appearance');
  document.documentElement.dataset.theme = ['light', 'dark'].includes(saved)
    ? saved : matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
} catch {
  document.documentElement.dataset.theme = matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
