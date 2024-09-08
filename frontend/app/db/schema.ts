import { pgTable, uuid, jsonb, timestamp } from 'drizzle-orm/pg-core';

export const gs1Progress = pgTable('gs1_progress', {
  id: uuid('id').primaryKey().defaultRandom(),
  userId: uuid('user_id').notNull(),
  h1: jsonb('h1').default({
    status: 'not_started',
    last_activity: null,
    mock_scores: [],
    wrong_questions: []
  }),
  h2: jsonb('h2').default({
    status: 'not_started',
    last_activity: null,
    mock_scores: [],
    wrong_questions: []
  }),
  h3: jsonb('h3').default({
    status: 'not_started',
    last_activity: null,
    mock_scores: [],
    wrong_questions: []
  }),
  g1: jsonb('g1').default({
    status: 'not_started',
    last_activity: null,
    mock_scores: [],
    wrong_questions: []
  }),
  g2: jsonb('g2').default({
    status: 'not_started',
    last_activity: null,
    mock_scores: [],
    wrong_questions: []
  }),
  g3: jsonb('g3').default({
    status: 'not_started',
    last_activity: null,
    mock_scores: [],
    wrong_questions: []
  }),
  createdAt: timestamp('created_at').notNull().defaultNow(),
  updatedAt: timestamp('updated_at').notNull().defaultNow()
});