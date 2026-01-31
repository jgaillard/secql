-- API Keys table for SecQL
create table api_keys (
    id uuid primary key default gen_random_uuid(),
    key text unique not null,
    name text not null,
    email text not null,
    tier text not null default 'free',
    requests_per_minute int not null default 100,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    last_used_at timestamptz
);

-- Usage tracking table
create table api_usage (
    id bigserial primary key,
    api_key_id uuid not null references api_keys(id) on delete cascade,
    endpoint text not null,
    ticker text,
    status_code int not null,
    response_time_ms int,
    created_at timestamptz not null default now()
);

-- Index for fast key lookups
create index idx_api_keys_key on api_keys(key) where is_active = true;

-- Index for usage queries
create index idx_api_usage_key_date on api_usage(api_key_id, created_at);
create index idx_api_usage_created on api_usage(created_at);

-- Daily usage summary (materialized for billing)
create table daily_usage (
    id bigserial primary key,
    api_key_id uuid not null references api_keys(id) on delete cascade,
    date date not null,
    request_count int not null default 0,
    unique(api_key_id, date)
);

-- Function to generate API key
create or replace function generate_api_key()
returns text as $$
declare
    key text;
begin
    key := 'sk_live_' || encode(gen_random_bytes(24), 'base64');
    -- Remove non-alphanumeric characters
    key := regexp_replace(key, '[^a-zA-Z0-9_]', '', 'g');
    return key;
end;
$$ language plpgsql;

-- Function to create a new API key
create or replace function create_api_key(p_name text, p_email text)
returns table(id uuid, key text) as $$
declare
    new_key text;
    new_id uuid;
begin
    new_key := generate_api_key();
    insert into api_keys (key, name, email)
    values (new_key, p_name, p_email)
    returning api_keys.id into new_id;

    return query select new_id, new_key;
end;
$$ language plpgsql;

-- Function to validate API key and get rate limit
create or replace function validate_api_key(p_key text)
returns table(
    id uuid,
    tier text,
    requests_per_minute int
) as $$
begin
    return query
    select ak.id, ak.tier, ak.requests_per_minute
    from api_keys ak
    where ak.key = p_key and ak.is_active = true;

    -- Update last_used_at
    update api_keys set last_used_at = now() where key = p_key;
end;
$$ language plpgsql;

-- Function to record API usage
create or replace function record_usage(
    p_api_key_id uuid,
    p_endpoint text,
    p_ticker text,
    p_status_code int,
    p_response_time_ms int
) returns void as $$
begin
    -- Insert detailed usage record
    insert into api_usage (api_key_id, endpoint, ticker, status_code, response_time_ms)
    values (p_api_key_id, p_endpoint, p_ticker, p_status_code, p_response_time_ms);

    -- Upsert daily summary
    insert into daily_usage (api_key_id, date, request_count)
    values (p_api_key_id, current_date, 1)
    on conflict (api_key_id, date)
    do update set request_count = daily_usage.request_count + 1;
end;
$$ language plpgsql;

-- Enable RLS
alter table api_keys enable row level security;
alter table api_usage enable row level security;
alter table daily_usage enable row level security;

-- Comment for documentation
comment on table api_keys is 'API keys for SecQL users';
comment on table api_usage is 'Detailed API usage logs for analytics';
comment on table daily_usage is 'Daily aggregated usage for billing';
