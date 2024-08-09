import { createClient } from '@/utils/supabase/client';

const supabase = createClient();

export async function createTodo(task: string, userId: string) {
  const { data, error } = await supabase
    .from('todos')
    .insert({ task, user_id: userId })
    .select();
  
  if (error) throw error;
  return data[0];
}

export async function getTodos(userId: string) {
  const { data, error } = await supabase
    .from('todos')
    .select('*')
    .eq('user_id', userId)
    .order('inserted_at', { ascending: false });
  
  if (error) throw error;
  return data;
}

export async function updateTodo(id: number, updates: Partial<Todo>) {
  const { data, error } = await supabase
    .from('todos')
    .update(updates)
    .eq('id', id)
    .select();
  
  if (error) throw error;
  return data[0];
}

export async function deleteTodo(id: number) {
  const { error } = await supabase
    .from('todos')
    .delete()
    .eq('id', id);
  
  if (error) throw error;
}