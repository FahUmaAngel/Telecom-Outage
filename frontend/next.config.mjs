/** @type {import('next').NextConfig} */
const isGitHubPages = process.env.GITHUB_PAGES === "true";
const outputExport = process.env.NEXT_OUTPUT_EXPORT === "true" || isGitHubPages;
const basePath = isGitHubPages ? "/Telecom-Outage" : "";

const nextConfig = {
  generateBuildId: async () => Date.now().toString(),
  ...(outputExport
    ? {
        output: "export",
        images: { unoptimized: true },
        trailingSlash: true,
        basePath,
        assetPrefix: basePath,
      }
    : {}),
};

export default nextConfig;
