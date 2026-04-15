# CS 4332 — Project 2: Grocery Store Database

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for the PostgreSQL container)
- Python 3.9+

---

## Setup

### 1. Configure environment variables

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

The defaults in `.env` work out of the box with the Docker setup:

```
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=proj
```

### 2. Start the database

```bash
docker compose up -d
```

This starts a PostgreSQL 16 container on port `5432`.

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

Run these two scripts **in order**:

### Step 1 — Create the schema

```bash
docker exec -i proj-postgres psql -U your_username -d proj < proj2-makeSchema.sql
```

This drops and recreates all tables. Re-run it any time you want a clean slate.

### Step 2 — Seed the data

```bash
python3 proj2-fillSchema.py
```

This inserts sample data across all 12 tables. It skips seeding if the `Store` table already has rows — run `proj2-makeSchema.sql` first to reset.

---

## Querying the Database

Connect using `psql` inside the container:

```bash
docker exec -it proj-postgres psql -U your_username -d proj
```

Useful psql commands once connected:

```sql
\dt                  -- list all tables
\d "Customer"        -- describe a table's columns
\q                   -- quit
```

Example queries:

```sql
-- All products in a category
SELECT p."Name", p."Brand", p."Price"
FROM "Product" p
JOIN "Category" c ON p."CategoryID" = c."CategoryID"
WHERE c."Name" = 'Dairy';

-- Top 5 best-selling products by quantity
SELECT p."Name", SUM(si."Quantity") AS total_sold
FROM "SaleItem" si
JOIN "Product" p ON si."ProductID" = p."ProductID"
GROUP BY p."Name"
ORDER BY total_sold DESC
LIMIT 5;
```

---

## Teardown

Stop and remove the container:

```bash
docker compose down
```

To also delete the stored data volume:

```bash
docker compose down -v
```

> **Note:** If you get a "container name already in use" error when bringing the container back up, force-remove the old container first:
> ```bash
> docker rm -f proj-postgres
> docker compose up -d
> ```

---

## File Overview

| File | Purpose |
|---|---|
| `proj2-makeSchema.sql` | Creates all tables (drops existing ones first) |
| `proj2-fillSchema.py` | Generates and inserts sample data |
| `docker-compose.yml` | PostgreSQL container definition |
| `.env` | Local DB credentials (not committed) |
| `requirements.txt` | Python dependencies |
