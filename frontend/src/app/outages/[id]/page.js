// GitHub Pages uses `output: "export"` which requires `generateStaticParams` for
// dynamic routes. Outage IDs come from a live API/DB, so we don't know them at
// build time. Export none so the static build succeeds.
export const dynamicParams = false;
export async function generateStaticParams() {
    return [];
}

import OutageDetailClient from "./OutageDetailClient";

export default function OutageDetailPage() {
    return <OutageDetailClient />;
}

