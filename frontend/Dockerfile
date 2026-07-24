FROM node:22-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

FROM node:22-alpine
RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
RUN chown -R app:app /app
USER app
EXPOSE 3000
CMD ["npm", "run", "dev"]

