CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE user_role AS ENUM ('USER', 'ADMIN');
CREATE TYPE order_type AS ENUM ('LIMIT', 'MARKET');
CREATE TYPE order_status AS ENUM ('NEW', 'EXECUTED', 'PARTIALLY_EXECUTED', 'CANCELLED');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    role user_role DEFAULT 'USER'
);

CREATE TABLE instruments (
    ticker VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    ticker VARCHAR(10) REFERENCES instruments(ticker) NOT NULL,
    type order_type NOT NULL,
    price DECIMAL(20, 2),
    qty INTEGER NOT NULL CHECK (qty > 0),
    status order_status DEFAULT 'NEW',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE balances (
    user_id UUID REFERENCES users(id),
    ticker VARCHAR(10) REFERENCES instruments(ticker),
    amount INTEGER DEFAULT 0 CHECK (amount >= 0),
    PRIMARY KEY (user_id, ticker)
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker VARCHAR(10) REFERENCES instruments(ticker) NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    price DECIMAL(20, 2) NOT NULL CHECK (price > 0),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    order_id UUID REFERENCES orders(id)
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_balances_user_id ON balances(user_id);

INSERT INTO users (id, name, api_key, role)
SELECT
    'e8c08127-f0a7-42dd-abd7-8f0eec436df1',
    'Admin User',
    '$2b$12$uen1ldBxnsYlN6XXAUaceeJ/SpcoZ8uwSvJnC5QgvmmqvBVh45K4.',
    'ADMIN'
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE role = 'ADMIN'
);