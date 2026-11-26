CREATE TABLE IF NOT EXISTS users (
    id text PRIMARY KEY,
    name text NOT NULL,
    email text NOT NULL UNIQUE,
    password_hash text NOT NULL,
    role text NOT NULL CHECK (role IN ('participant', 'organizer')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS events (
    id text PRIMARY KEY,
    organizer_id text NOT NULL REFERENCES users (id),
    name text NOT NULL,
    starts_at timestamptz NOT NULL,
    venue text NOT NULL,
    capacity int NOT NULL CHECK (capacity >= 1),
    price_cents int NOT NULL CHECK (price_cents > 0),
    status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'cancelled')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tickets (
    id text PRIMARY KEY,
    event_id text NOT NULL REFERENCES events (id),
    user_id text REFERENCES users (id),
    buyer_email text,
    code text NOT NULL UNIQUE,
    status text NOT NULL CHECK (status IN ('pending', 'confirmed', 'declined', 'cancelled', 'refunded')),
    price_cents int NOT NULL,
    checked_in boolean NOT NULL DEFAULT false,
    gateway_approved boolean,
    gateway_due_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);
