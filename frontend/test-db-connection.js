const { config } = require('dotenv');
const postgres = require('postgres');

console.log('Starting database connection test...');

try {
  config({ path: '.env' });
  console.log('Loaded .env file');
} catch (error) {
  console.error('Error loading .env file:', error);
  process.exit(1);
}

const connectionString = process.env.DATABASE_URL;
console.log('DATABASE_URL:', connectionString);

if (!connectionString) {
  console.error('DATABASE_URL is not set in the .env file');
  process.exit(1);
}

console.log('Attempting to connect with:', connectionString);

const sql = postgres(connectionString);

async function testConnection() {
  try {
    console.log('Executing SQL query...');
    const result = await sql`SELECT current_database()`;
    console.log('Successfully connected to database:', result[0].current_database);
  } catch (error) {
    console.error('Failed to connect to database:', error);
  } finally {
    console.log('Closing database connection...');
    await sql.end();
    console.log('Database connection closed');
  }
}

testConnection().catch(error => {
  console.error('Unhandled error in testConnection:', error);
  process.exit(1);
});

console.log('Test script execution completed');
