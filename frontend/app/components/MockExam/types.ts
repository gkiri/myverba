export interface MockExamData {
    questions: Question[]; 
  }
  
  export interface Question {
    id: number;         // Unique identifier for the question
    text: string;       // The question text
    options: string[];   // An array of answer options
    correctAnswer: string; // The correct answer 
    explanation: string;  //  Explanation for the correct answer (optional)
  }