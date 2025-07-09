# Install Nepal Compliance using Docker
**This guide will help you to install and run Nepal Compliance using Docker and Docker Compose.**

### Dependencies
You need to have the Docker installed and ready in your system:
* Docker Engine & Docker CLI. Check using `docker --version`
* Docker Compose. Check using `docker compose version`

## Step 1: Clone the Repository
First, clone the Nepal Compliance repository from GitHub:
```
git clone https://github.com/yarsa/nepal-compliance.git
```
Change directory into the folder:
```
cd nepal-compliance
```

## Step 2: Set Up Environment Variables

Copy the `.env.example` to `.env`

```
cp .env.example .env
```

Edit the `.env` file with your own values. For eg:

```
ADMIN_PASSWORD=your-admin-password
DB_ROOT_PASSWORD=your-db-root-password
```
***Note: The `.env` file should be placed at the root of the project directory next to your `compose.yaml` file.***


## Step 3: Pull the Docker Image
### Pull the default `latest` tag from DockerHub
```
docker pull yarsalabs/nepal-compliance
```
**Or**, specify a VERSION_TAG. For eg:
```
docker pull yarsalabs/nepal-compliance:latest
```

## Step 4: Run Nepal Compliance with Docker Compose

```
docker compose up -d
```

### Access your ERP instance running at `http://localhost:8080`

Now you should have Nepal Compliance up and running using Docker.

After docker compose, the `create-site-1` container runs in background and takes around 3-5 minutes to install and build frappe apps along with `frontend` site, so check logs before accessing it in your browser.
```
docker logs {container-name} -f
```

Also after setting up the `.env` file, you can check variables and values used by your Compose to interpolate the Compose model by running:
```
docker compose config --environment
```
This command should display all environment variables in `.env` being used in your Docker Compose.

---
### Environment Variables
These variables are defined in an `.env` file and used to inject configuration into services via `docker compose`.

| Key                         | Value                     | Description                                               |
|-----------------------------|---------------------------|-----------------------------------------------------------|
| `VERSION_TAG`               | `latest`                  | Version of the current Docker image tag. Default `latest` |
| `DB_HOST`                   | `db`                      | Hostname of the MariaDB container.                        |
| `DB_PORT`                   | `"3306"`                  | Port for the database (MySQL/MariaDB).                    |
| `MYSQL_ROOT_PASSWORD`       | `your-mysql-root-password`| Root password for MySQL (if used).                        |
| `MARIADB_ROOT_PASSWORD`     | `your-db-root-password`   | MariaDB root password (primary for ERPNext setup).        |
| `DB_ROOT_PASSWORD`          | `your-db-root-password`   | General DB root password (may overlap with MariaDB one).  |
| `REDIS_CACHE`               | `redis-cache:6379`        | Redis instance for caching.                               |
| `REDIS_QUEUE`               | `redis-queue:6379`        | Redis instance for task queues.                           |
| `SOCKETIO_PORT`             | `"9000"`                  | Port used by the WebSocket server.                        |
| `SOCKETIO`                  | `websocket:9000`          | WebSocket address used by the frontend.                   |
| `ADMIN_PASSWORD`            | `your-admin-password`     | Administrator password for `bench new-site {site} --admin-password`|
| `BACKEND`                   | `backend:8000`            | Backend app server address used by frontend.              |
| `FRAPPE_SITE_NAME_HEADER`   | `frontend`                | Site name. Host header to route requests in multi-site setup.|
| `UPSTREAM_REAL_IP_ADDRESS`  | `127.0.0.1`               | Upstream proxy IP for real IP resolution.                   |
| `UPSTREAM_REAL_IP_HEADER`   | `X-Forwarded-For`         | Header to extract the real IP of the client.              |
| `UPSTREAM_REAL_IP_RECURSIVE`| `"off"`                   | Enables/disables recursive lookup for real IPs.            |

# Next
* Learn how to [contribute to this project](/CONTRIBUTING.md)
* [Manual Install - Nepal Compliance](/docs/manual-install.md)

**If you liked our work, then we would love to get your stars on our GitHub and Docker repositories.** 😀
