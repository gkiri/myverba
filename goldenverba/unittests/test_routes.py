# Health check
curl http://localhost:8000/api/health

# Get status
curl http://localhost:8000/api/get_status

# Get configuration
curl http://localhost:8000/api/config

# Query (POST request)
curl -X POST http://localhost:8000/api/query -H "Content-Type: application/json" -d '{"query": "What is Verba?"}'

# Get all documents (POST request)
curl -X POST http://localhost:8000/api/get_all_documents \
  -H "Content-Type: application/json" \
  -d '{"query": "", "doc_type": "", "page": 1, "pageSize": 10}'

# Upload a mock exam (you'll need to create a JSON file with the correct structure)
curl -X POST http://localhost:8000/api/upload_mock_exam \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/your/mock_exam.json"

# Get mock exam data
curl http://localhost:8000/api/mock_exam

# Generate bullet points (POST request)
curl -X POST http://localhost:8000/api/bullet_points \
  -H "Content-Type: application/json" \
  -d '{"query": "The provided context discusses various aspects of the Indian economy, focusing on initiatives like Make in India,FDI inflows, infrastructure development, policy reforms, and sectors targeted for growth. It highlights the governments efforts to promote investment, innovation, and economic growth in India. If you need more specific information or details on a particular aspect of the Indian economy"}'

# Generate summary (POST request)
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"query": "The provided context discusses various aspects of the Indian economy, focusing on initiatives like Make in India,FDI inflows, infrastructure development, policy reforms, and sectors targeted for growth. It highlights the governments efforts to promote investment, innovation, and economic growth in India. If you need more specific information or details on a particular aspect of the Indian economy"}'

# Generate visualization (POST request)
curl -X POST http://localhost:8000/api/visualize \
  -H "Content-Type: application/json" \
  -d '{"query": "The provided context discusses various aspects of the Indian economy, focusing on initiatives like Make in India,FDI inflows, infrastructure development, policy reforms, and sectors targeted for growth. It highlights the governments efforts to promote investment, innovation, and economic growth in India. If you need more specific information or details on a particular aspect of the Indian economy"}'