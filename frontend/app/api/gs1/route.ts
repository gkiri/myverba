import { NextResponse } from 'next/server';
import { getGS1Progress, updateGS1Progress, createGS1Progress, deleteGS1Progress } from '@/app/db/gs1';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const userId = searchParams.get('userId');
  
  if (!userId) {
    return NextResponse.json({ error: 'User ID is required' }, { status: 400 });
  }

  const progress = await getGS1Progress(userId);
  return NextResponse.json(progress);
}

export async function POST(request: Request) {
  const { userId } = await request.json();
  
  if (!userId) {
    return NextResponse.json({ error: 'User ID is required' }, { status: 400 });
  }

  const result = await createGS1Progress(userId);
  return NextResponse.json(result);
}

export async function PUT(request: Request) {
  const { userId, chapterId, data } = await request.json();
  
  if (!userId || !chapterId || !data) {
    return NextResponse.json({ error: 'User ID, Chapter ID, and data are required' }, { status: 400 });
  }

  const result = await updateGS1Progress(userId, chapterId, data);
  return NextResponse.json(result);
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const userId = searchParams.get('userId');
  
  if (!userId) {
    return NextResponse.json({ error: 'User ID is required' }, { status: 400 });
  }

  const result = await deleteGS1Progress(userId);
  return NextResponse.json(result);
}
