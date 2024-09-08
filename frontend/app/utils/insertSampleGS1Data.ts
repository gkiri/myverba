import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

const sampleGS1Data = {
  h1: {
    status: 'in_progress',
    last_activity: new Date().toISOString(),
    mock_scores: [75, 80, 90],
    wrong_questions: ['q1', 'q5', 'q8']
  },
  h2: {
    status: 'completed',
    last_activity: new Date().toISOString(),
    mock_scores: [85, 95],
    wrong_questions: ['q3']
  },
  h3: {
    status: 'not_started',
    last_activity: null,
    mock_scores: [],
    wrong_questions: []
  },
  g1: {
    status: 'in_progress',
    last_activity: new Date().toISOString(),
    mock_scores: [70, 75],
    wrong_questions: ['q2', 'q7']
  },
  g2: {
    status: 'not_started',
    last_activity: null,
    mock_scores: [],
    wrong_questions: []
  },
  g3: {
    status: 'completed',
    last_activity: new Date().toISOString(),
    mock_scores: [90, 95, 100],
    wrong_questions: []
  }
};

export async function insertSampleGS1Data(userId: string) {
  try {
    const { data, error } = await supabase
      .from('gs1_progress')
      .upsert({
        user_id: userId,
        ...sampleGS1Data
      })
      .select()
      .single();

    if (error) {
      console.error('Error inserting sample GS1 data:', error);
      return null;
    }

    console.log('Sample GS1 data inserted successfully:', data);
    return data;
  } catch (error) {
    console.error('Error in insertSampleGS1Data:', error);
    return null;
  }
}
