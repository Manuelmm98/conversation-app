# syntax=docker/dockerfile:1

FROM node:16.17.0-bullseye-slim
WORKDIR /webapp
COPY package* ./
RUN npm install --production
COPY . .
CMD [ "npm", "start" ]
