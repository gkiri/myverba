-- Create gs1_progress table
create table public.gs1_progress (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  h1 jsonb default '{"status": "not_started", "last_activity": null, "mock_scores": [], "wrong_questions": []}',
  h2 jsonb default '{"status": "not_started", "last_activity": null, "mock_scores": [], "wrong_questions": []}',
  h3 jsonb default '{"status": "not_started", "last_activity": null, "mock_scores": [], "wrong_questions": []}',
  g1 jsonb default '{"status": "not_started", "last_activity": null, "mock_scores": [], "wrong_questions": []}',
  g2 jsonb default '{"status": "not_started", "last_activity": null, "mock_scores": [], "wrong_questions": []}',
  g3 jsonb default '{"status": "not_started", "last_activity": null, "mock_scores": [], "wrong_questions": []}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Enable Row Level Security
alter table public.gs1_progress enable row level security;

-- Create RLS policies
create policy "Users can view their own gs1_progress"
  on public.gs1_progress for select
  using (auth.uid() = user_id);

create policy "Users can insert their own gs1_progress"
  on public.gs1_progress for insert
  with check (auth.uid() = user_id);

create policy "Users can update their own gs1_progress"
  on public.gs1_progress for update
  using (auth.uid() = user_id);

-- Create index for faster queries
create index idx_gs1_progress_user_id on public.gs1_progress(user_id);

-- Add comment to describe the table
comment on table public.gs1_progress is 'Stores user progress for GS1 chapters in UPSC preparation';

-- Create function to automatically update the updated_at column
create or replace function public.update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Create trigger to update the updated_at column
create trigger update_gs1_progress_updated_at
before update on public.gs1_progress
for each row
execute function public.update_updated_at_column();
