import { createContext, useContext, useEffect, useLayoutEffect, useState } from 'react';
import { FiMoon, FiSun } from 'react-icons/fi';

const ThemeContext = createContext(null);
const key = 'football-appearance';
const savedTheme = () => {
  try { return localStorage.getItem(key); } catch { return null; }
};
const systemTheme = () => window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
export const useStadiumTheme = () => useContext(ThemeContext);

export function ThemeProvider({ children }) {
  const [theme, updateTheme] = useState(() => document.documentElement.dataset.theme || systemTheme());
  useLayoutEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);
  useEffect(() => {
    const preference = window.matchMedia('(prefers-color-scheme: dark)');
    const systemChanged = () => { if (!['light', 'dark'].includes(savedTheme())) updateTheme(systemTheme()); };
    const storageChanged = (event) => {
      if (event.key === key || event.key === null) updateTheme(['light', 'dark'].includes(savedTheme()) ? savedTheme() : systemTheme());
    };
    preference.addEventListener('change', systemChanged);
    window.addEventListener('storage', storageChanged);
    return () => { preference.removeEventListener('change', systemChanged); window.removeEventListener('storage', storageChanged); };
  }, []);
  const setTheme = (value) => {
    updateTheme(value);
    try { localStorage.setItem(key, value); } catch { /* Appearance still works when storage is unavailable. */ }
  };
  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
}

export default function ThemeToggle() {
  const { theme, setTheme } = useContext(ThemeContext);
  return <div className="stadium-theme-switch" role="group" aria-label="Stadium appearance">
    <button type="button" aria-label="Day mode" aria-pressed={theme === 'light'} onClick={() => setTheme('light')}><FiSun aria-hidden="true" /><span>Day</span></button>
    <button type="button" aria-label="Night mode" aria-pressed={theme === 'dark'} onClick={() => setTheme('dark')}><FiMoon aria-hidden="true" /><span>Night</span></button>
  </div>;
}
