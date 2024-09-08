import { db } from '../db';
import { gs1Progress } from '../db/schema';
import { eq } from 'drizzle-orm';

export async function getGS1Progress(userId: string) {
  const result = await db.select().from(gs1Progress).where(eq(gs1Progress.userId, userId));
  return result[0];
}

export async function updateGS1Progress(userId: string, chapterId: string, data: any) {
  await db.update(gs1Progress)
    .set({ [chapterId]: data })
    .where(eq(gs1Progress.userId, userId));
}

export async function createGS1Progress(userId: string) {
  await db.insert(gs1Progress).values({ userId });
}