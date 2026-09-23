# Production Dockerfile for Billing 2FA Gate
FROM node:20-alpine AS production

# Install su-exec, tzdata, nginx (for syntax testing), and sudo
RUN apk add --no-cache su-exec tzdata nginx sudo && \
    echo "node ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/node && \
    chmod 440 /etc/sudoers.d/node

# Set working directory
WORKDIR /app

# Set default production environment variables
ENV NODE_ENV=production \
    PORT=3100 \
    HOST=0.0.0.0 \
    DATA_DIR=/var/lib/billing-gate

# Copy package specifications and install production dependencies
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force

# Copy application source code
COPY server.js cli.js ./
COPY lib/ ./lib/
COPY public/ ./public/
COPY views/ ./views/

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose internal listening port
EXPOSE 3100

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:' + (process.env.PORT || 3100) + '/gate/health').then(r => process.exit(r.ok ? 0 : 1)).catch(() => process.exit(1))"

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["node", "server.js"]
