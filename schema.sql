CREATE TABLE "user" (
    username TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_password (
    username TEXT PRIMARY KEY REFERENCES "user"(username) ON DELETE CASCADE,
    password_hash BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE loved_one (
    username TEXT NOT NULL REFERENCES "user"(username) ON DELETE CASCADE,
    name TEXT NOT NULL,
    last_called_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (username, name)
);
