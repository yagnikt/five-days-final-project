# Build Stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency files
COPY package.json ./

# Install dependencies
RUN npm install

# Copy application source code
COPY . .

# Set VITE_API_BASE_URL to empty string so Vite compiles the frontend to use relative URLs, 
# which will be intercepted and proxied by Nginx.
ENV VITE_API_BASE_URL=""

# Build the application
RUN npm run build

# Serve Stage
FROM nginx:alpine

# Install envsubst (comes pre-installed in nginx:alpine, but we make sure)
RUN apk add --no-cache gettext

# Copy static build files from Build Stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy Nginx template and startup script
COPY nginx.conf.template /etc/nginx/templates/nginx.conf.template
COPY start.sh /app/start.sh

# Make start script executable
RUN chmod +x /app/start.sh

# Set working directory
WORKDIR /app

# Expose port (Cloud Run will override this using the PORT env var)
EXPOSE 8080

# Run the startup script
CMD ["/app/start.sh"]
