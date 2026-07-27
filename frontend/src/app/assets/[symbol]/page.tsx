import { AppShell } from "@/components/shell/app-shell";
import { AssetWorkspace } from "@/components/workspaces/asset-workspace";

export default async function AssetPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = await params;
  return (
    <AppShell active="workspace">
      <AssetWorkspace symbol={decodeURIComponent(symbol).toUpperCase()} />
    </AppShell>
  );
}
