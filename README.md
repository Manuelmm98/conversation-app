# Running this project
Run `npm install` in the `webapp/` directory to install required dependencies.

## Development
Run `docker compose up --build` in the project's root directory.

## Production
Run `docker-compose -f docker-compose.prod.yml up --build` in the project's root directory.

I don't know if this will necessarily be used, hence the v1 compose syntax.

# Notes for running on MacOS without a Docker Desktop license
[colima](https://github.com/abiosoft/colima) will need to be installed to run Docker Engine without Docker Desktop. After installing, edit `~/.docker/config.json` and remove the line referring to `credStore`.
