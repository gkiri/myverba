CREATE TABLE IF NOT EXISTS "gs1_progress" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"user_id" uuid NOT NULL,
	"h1" jsonb DEFAULT '{"status":"not_started","last_activity":null,"mock_scores":[],"wrong_questions":[]}'::jsonb,
	"h2" jsonb DEFAULT '{"status":"not_started","last_activity":null,"mock_scores":[],"wrong_questions":[]}'::jsonb,
	"h3" jsonb DEFAULT '{"status":"not_started","last_activity":null,"mock_scores":[],"wrong_questions":[]}'::jsonb,
	"g1" jsonb DEFAULT '{"status":"not_started","last_activity":null,"mock_scores":[],"wrong_questions":[]}'::jsonb,
	"g2" jsonb DEFAULT '{"status":"not_started","last_activity":null,"mock_scores":[],"wrong_questions":[]}'::jsonb,
	"g3" jsonb DEFAULT '{"status":"not_started","last_activity":null,"mock_scores":[],"wrong_questions":[]}'::jsonb,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
