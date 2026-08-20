import { useState } from "react";

/**
 * Like useState, but the value survives navigating away from the page and
 * back — backed by sessionStorage instead of component state.
 *
 * Why sessionStorage and not a global store or "keep the page mounted":
 *   - It holds only what you explicitly pass it (a question string, a
 *     small results array, a chat transcript) — nothing gets duplicated
 *     into a second in-memory cache, so there's no meaningful RAM cost
 *     beyond the state you'd have had anyway.
 *   - It's disk-backed by the browser, not the JS heap, and is capped at
 *     a few MB by the browser itself — it physically cannot "load
 *     everything" the way keeping every route mounted could.
 *   - It clears itself when the tab closes, so it never accumulates
 *     indefinitely the way localStorage would across sessions.
 *
 * Use a distinct `key` per field per page (e.g. "ai_search:question") so
 * different pages/fields don't collide.
 */
export function usePersistedState<T>(key: string, initialValue: T) {
  const storageKey = `iqac_session:${key}`;

  const [state, setState] = useState<T>(() => {
    try {
      const stored = sessionStorage.getItem(storageKey);
      return stored !== null ? (JSON.parse(stored) as T) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setPersistedState = (value: T | ((prev: T) => T)) => {
    setState((prev) => {
      const next = value instanceof Function ? value(prev) : value;
      try {
        sessionStorage.setItem(storageKey, JSON.stringify(next));
      } catch {
        // sessionStorage full or unavailable (e.g. private browsing) —
        // state still works for this session, it just won't persist.
      }
      return next;
    });
  };

  return [state, setPersistedState] as const;
}

/** Clears every key this hook has written, e.g. for a "New chat" / "Clear" action. */
export function clearPersistedState(keyPrefix: string) {
  const prefix = `iqac_session:${keyPrefix}`;
  Object.keys(sessionStorage)
    .filter((k) => k.startsWith(prefix))
    .forEach((k) => sessionStorage.removeItem(k));
}
