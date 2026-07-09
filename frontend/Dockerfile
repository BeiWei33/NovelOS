FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm config set registry https://registry.npmmirror.com && npm ci && npm config delete registry

COPY . .

CMD ["npm", "run", "dev"]