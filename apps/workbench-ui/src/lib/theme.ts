import { useEffect, useState } from "react";

export type Theme = "light" | "dark";

const KEY = "noesi-theme";

/** A saved choice wins; otherwise follow the OS. Storage can throw when the
 *  browser blocks it, and a theme is never worth failing the page over. */
function readSaved(): Theme | null {
  try {
    const saved = localStorage.getItem(KEY);
    return saved === "light" || saved === "dark" ? saved : null;
  } catch {
    return null;
  }
}

function systemTheme(): Theme {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ? "dark" : "light";
}

export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(() => readSaved() ?? systemTheme());

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(KEY, theme);
    } catch {
      // Non-fatal: the attribute is already applied for this session.
    }
  }, [theme]);

  return [theme, () => setTheme((current) =>
    current === "dark" ? "light" : "dark")];
}
