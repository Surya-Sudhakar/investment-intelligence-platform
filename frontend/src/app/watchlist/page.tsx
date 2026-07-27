import { AppShell } from "@/components/shell/app-shell";
import { LocalWatchlist } from "@/components/watchlist/local-watchlist";

export default function WatchlistPage() {
  return (
    <AppShell active="watchlist">
      <LocalWatchlist />
    </AppShell>
  );
}
