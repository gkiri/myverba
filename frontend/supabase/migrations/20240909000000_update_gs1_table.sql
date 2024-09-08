-- Update GS1 table to include Geography chapters and restructure chapter-specific fields
-- This migration alters the existing GS1 table to better manage syllabus progress for both History and Geography

-- Add comment to describe the purpose of the GS1 table
comment on table public.gs1 is 'Tracks user progress for GS1 syllabus, including History (H1-H3) and Geography (G1-G3) chapters';

-- Alter existing History chapter columns
alter table public.gs1
  -- H1 updates
  alter column h1_status set data type text,
  alter column h1_status set default 'not_started',
  alter column h1_last_studied rename to h1_last_activity,
  add column h1_mock_exam_scores jsonb default '[]'::jsonb,
  drop column h1_progress,
  -- H2 updates
  alter column h2_status set data type text,
  alter column h2_status set default 'not_started',
  alter column h2_last_studied rename to h2_last_activity,
  add column h2_mock_exam_scores jsonb default '[]'::jsonb,
  drop column h2_progress,
  -- H3 updates
  alter column h3_status set data type text,
  alter column h3_status set default 'not_started',
  alter column h3_last_studied rename to h3_last_activity,
  add column h3_mock_exam_scores jsonb default '[]'::jsonb,
  drop column h3_progress;

-- Add new Geography chapter columns
alter table public.gs1
  -- G1 columns
  add column g1_status text default 'not_started',
  add column g1_last_activity timestamp with time zone,
  add column g1_mock_exam_scores jsonb default '[]'::jsonb,
  add column g1_mock_exam_mistakes jsonb,
  -- G2 columns
  add column g2_status text default 'not_started',
  add column g2_last_activity timestamp with time zone,
  add column g2_mock_exam_scores jsonb default '[]'::jsonb,
  add column g2_mock_exam_mistakes jsonb,
  -- G3 columns
  add column g3_status text default 'not_started',
  add column g3_last_activity timestamp with time zone,
  add column g3_mock_exam_scores jsonb default '[]'::jsonb,
  add column g3_mock_exam_mistakes jsonb;

-- Drop the test_field column as it's no longer needed
alter table public.gs1 drop column if exists test_field;

-- Update RLS policies to include new columns
drop policy if exists "Users can insert their own GS1 progress" on public.gs1;
drop policy if exists "Users can update their own GS1 progress" on public.gs1;
drop policy if exists "Users can read their own GS1 progress" on public.gs1;
drop policy if exists "Users can delete their own GS1 progress" on public.gs1;

-- Create new RLS policies
create policy "Users can insert their own GS1 progress"
  on public.gs1 for insert
  with check (auth.uid() = user_id);

create policy "Users can update their own GS1 progress"
  on public.gs1 for update
  using (auth.uid() = user_id);

create policy "Users can read their own GS1 progress"
  on public.gs1 for select
  using (auth.uid() = user_id);

create policy "Users can delete their own GS1 progress"
  on public.gs1 for delete
  using (auth.uid() = user_id);

-- Add comments to explain the purpose of each column
comment on column public.gs1.h1_status is 'Status of study for History chapter 1 (not started, in progress, complete)';
comment on column public.gs1.h1_last_activity is 'Timestamp of last activity for History chapter 1';
comment on column public.gs1.h1_mock_exam_scores is 'List of mock exam scores for History chapter 1';
comment on column public.gs1.h1_mock_exam_mistakes is 'List of questions answered incorrectly in mock exams for History chapter 1';

-- Repeat comments for H2, H3, G1, G2, G3 columns (omitted for brevity)
