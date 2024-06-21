export interface MockExamData {
    questions: Question[]; 
  }
  
export interface Question {
    global_questionID: string;  // Unique identifier for the question
    year: string;              // Year of the exam question 
    question: string;          // The question text
    options: string[];         // An array of answer options
    answer_key: string;       // The correct answer key (e.g., 'a', 'b', 'c', 'd')
    topic: string;             // Topic of the question (optional)
    description: string;        // Explanation for the answer (optional)
    question_number: string;     //  Question number in the original exam (optional)
  }