import { pgTable, serial, text } from 'drizzle-orm/pg-core';

console.log('Test schema file is being executed');

export const testTable = pgTable('test_table', {
  id: serial('id').primaryKey(),
  name: text('name').notNull(),
});

console.log('Test table defined:', testTable);
