FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
COPY . .
# Ensure devDependencies (vite) are installed so the dev server is available in the container
# Run install after copying the source to avoid cache issues where node_modules might be missing
RUN npm ci --include=dev
# Vite listens on 5173 inside the container; docker-compose maps host 3000 -> container 5173
EXPOSE 5173
# Start the Vite dev server and bind it to 0.0.0.0 on port 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]