"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

export type LayoutMode = "app" | "web";

const STORAGE_KEY = "lodestar.layout";

interface Ctx {
  mode: LayoutMode;
  setMode: (m: LayoutMode) => void;
  toggle: () => void;
}

const LayoutCtx = createContext<Ctx | null>(null);

/** Context controlling whether Lodestar renders in its phone-sized app shell
 *  (fixed bottom tab bar, max-w-md centered column) or as a wider webapp
 *  (top-mounted tab bar, multi-column grids). Persists to localStorage so
 *  the user's preference survives refresh. */
export function LayoutModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<LayoutMode>("app");

  useEffect(() => {
    // Restore persisted preference after hydration. Synchronous setState is
    // intentional — mirrors next-themes / LanguageProvider so there's no
    // visible flash when the stored value differs from the SSR default.
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved === "app" || saved === "web") {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setModeState(saved);
      }
    } catch {
      // localStorage unavailable — keep default
    }
  }, []);

  const setMode = useCallback((m: LayoutMode) => {
    setModeState(m);
    try {
      window.localStorage.setItem(STORAGE_KEY, m);
    } catch {
      // ignore
    }
  }, []);

  const toggle = useCallback(() => {
    setMode(mode === "app" ? "web" : "app");
  }, [mode, setMode]);

  const value = useMemo<Ctx>(() => ({ mode, setMode, toggle }), [mode, setMode, toggle]);

  return <LayoutCtx.Provider value={value}>{children}</LayoutCtx.Provider>;
}

export function useLayoutMode(): Ctx {
  const ctx = useContext(LayoutCtx);
  if (!ctx) throw new Error("useLayoutMode must be used within <LayoutModeProvider>");
  return ctx;
}
