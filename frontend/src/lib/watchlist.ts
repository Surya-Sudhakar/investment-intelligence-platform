export type WatchItem = { symbol: string; name: string; type: string };

export const WATCHLIST_STORAGE_KEY = "meridian-watchlist";
export const WATCHLIST_CHANGED_EVENT = "meridian-watchlist-changed";

export function readWatchlist(): WatchItem[] {
  try {
    const value: unknown = JSON.parse(
      window.localStorage.getItem(WATCHLIST_STORAGE_KEY) ?? "[]",
    );
    if (!Array.isArray(value)) return [];
    return value.filter(
      (item): item is WatchItem =>
        typeof item === "object" &&
        item !== null &&
        typeof item.symbol === "string" &&
        typeof item.name === "string" &&
        typeof item.type === "string",
    );
  } catch {
    return [];
  }
}

export function writeWatchlist(items: WatchItem[]): void {
  window.localStorage.setItem(WATCHLIST_STORAGE_KEY, JSON.stringify(items));
  window.dispatchEvent(new Event(WATCHLIST_CHANGED_EVENT));
}

export function addWatchItem(item: WatchItem): boolean {
  const current = readWatchlist();
  if (current.some((saved) => saved.symbol === item.symbol)) return false;
  writeWatchlist([...current, item]);
  return true;
}
