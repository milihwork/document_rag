FROM node:20-alpine AS build

WORKDIR /app

COPY services/gateway/package.json services/gateway/tsconfig.json ./
RUN npm install

COPY services/gateway/src ./src
RUN npm run build

FROM node:20-alpine

WORKDIR /app

COPY --from=build /app/package.json ./package.json
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist

ENV NODE_ENV=production
EXPOSE 8000

CMD ["node", "dist/index.js"]
