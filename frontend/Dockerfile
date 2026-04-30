FROM node:22-alpine AS builder
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source and build
# Copy source files
COPY src/ ./src/
COPY public/ ./public/
COPY *.mjs *.json ./

# We disable eslint and typescript errors on build just in case for smooth containerization
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Production Runner Stage
FROM node:22-alpine AS runner
WORKDIR /app

# Set up non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED 1

# Copy build artifacts from builder
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

# Ensure permissions for non-root user
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

# Start Next.js production server
CMD ["npm", "start"]
