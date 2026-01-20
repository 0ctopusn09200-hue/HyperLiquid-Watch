# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* pnpm-lock.yaml* ./

# Install dependencies
# Prefer npm (package-lock.json) if it exists, otherwise use pnpm
RUN if [ -f package-lock.json ]; then \
      npm ci; \
    elif [ -f pnpm-lock.yaml ]; then \
      corepack enable && corepack prepare pnpm@latest --activate && \
      (pnpm install --frozen-lockfile || pnpm install --no-frozen-lockfile); \
    else \
      npm install; \
    fi

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set build-time environment variables (use defaults if not provided)
ARG NEXT_PUBLIC_API_URL=http://localhost:8080
ARG NEXT_PUBLIC_WS_URL=ws://localhost:8080/api/v1/ws

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

# Build Next.js app
RUN if [ -f package-lock.json ]; then \
      npm run build; \
    elif [ -f pnpm-lock.yaml ]; then \
      corepack enable && corepack prepare pnpm@latest --activate && \
      pnpm build; \
    else \
      npm run build; \
    fi

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# Copy standalone output
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
