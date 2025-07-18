# TTS Performance Benchmark: Sequential vs Async

This benchmark demonstrates the performance difference between traditional sequential TTS processing and our optimized async preprocessing approach in Manim animations.

## 🎯 What This Benchmark Does

The benchmark creates two identical Manim animations with multiple voiceovers, using different TTS processing strategies:

1. **Sequential TTS Scene** (Traditional Approach)
   - TTS calls are made one by one during animation rendering
   - Each voiceover blocks until the TTS API call completes
   - This is how most Manim voiceover scripts work by default

2. **Async TTS Scene** (Optimized Approach)
   - All TTS texts are registered upfront
   - All TTS API calls are made in parallel before rendering starts
   - During rendering, pre-generated audio files are simply loaded from cache

## 🏗️ Architecture Comparison

### Sequential Approach Flow:
```
Start Animation → TTS Call 1 (wait) → Render → TTS Call 2 (wait) → Render → ... → End
```

### Async Preprocessing Flow:
```
Register All Texts → TTS Calls 1,2,3,4,5 (parallel) → Start Animation → Render (instant audio) → End
```

## 📋 Prerequisites

1. **DeepInfra API Key**: Get one from [deepinfra.com](https://deepinfra.com/)
2. **Required Python packages**:
   ```bash
   pip install manim manim-voiceover aiohttp aiofiles python-dotenv
   ```

## 🚀 How to Run the Benchmark

### Method 1: Using the Helper Script (Recommended)

1. The benchmark will automatically load your API key from `/root/manim_gemini/.env`
   
   If you need to update your API key, edit the .env file:
   ```bash
   nano /root/manim_gemini/.env
   ```

2. Run the benchmark:
   ```bash
   python run_tts_benchmark.py
   ```

### Method 2: Direct Execution

```bash
python benchmark_tts_performance.py
```

## 📊 Understanding the Results

The benchmark will output detailed timing information and performance analysis:

### Sample Output:
```
🏆 PERFORMANCE COMPARISON RESULTS
================================================================================
📊 Sequential TTS Time:  45.67 seconds
📊 Async TTS Time:       18.34 seconds  
📊 Time Saved:          27.33 seconds
📊 Speedup Factor:      2.49x
📊 Performance Gain:    59.8%

💡 ANALYSIS:
🚀 EXCELLENT! Async preprocessing is 2.5x faster!
   The async approach saved 27.3 seconds (59.8% improvement)

🎯 KEY INSIGHTS:
   • Sequential approach: TTS calls block animation rendering
   • Async approach: All TTS processed in parallel upfront  
   • Speedup increases with more voiceover segments
   • Network latency has major impact on sequential approach
```

## 📁 Output Files

The benchmark generates:
- `benchmark_output/sequential_tts_scene.mp4` - Traditional approach video
- `benchmark_output/async_tts_scene.mp4` - Optimized approach video
- Audio cache files in the respective cache directories

## 🔧 Technical Details

### Files Involved:

1. **`benchmark_tts_performance.py`** - Main benchmark script
   - Contains both scene classes
   - Timing and measurement logic
   - Performance analysis and reporting

2. **`run_tts_benchmark.py`** - Helper script for easy execution
   - Environment validation
   - Dependency checking
   - User-friendly error messages

3. **`deepinfra_service.py`** - Sequential TTS service
   - Traditional synchronous API calls
   - One-at-a-time processing

4. **`async_deepinfra_service.py`** - Async TTS service
   - Parallel API calls with rate limiting
   - Batch processing capabilities
   - Concurrent request management

5. **`async_voiceover_scene.py`** - Async-enabled Scene class
   - Voiceover registration system
   - Preprocessing workflow
   - Integration with async TTS service

### Key Performance Factors:

1. **Network Latency**: Higher latency = bigger speedup with async approach
2. **Number of Voiceovers**: More segments = more dramatic improvement
3. **TTS Service Response Time**: Slower service = bigger parallel benefits
4. **Concurrent Request Limits**: Balanced for optimal throughput

## 🎭 Scene Content

Both scenes create identical animations featuring:
- Animated title text
- Geometric shapes (circle, square)
- Mathematical equation (E=mc²)
- Coordinated voiceover narration
- Visual transformations and effects

## 📈 Expected Performance Gains

Typical speedup factors based on number of voiceover segments:

| Voiceover Segments | Expected Speedup | Use Case |
|-------------------|------------------|----------|
| 2-3 segments      | 1.5-2.0x        | Short clips |
| 4-6 segments      | 2.0-3.0x        | Medium videos |
| 7-10 segments     | 3.0-4.0x        | Long explanations |
| 10+ segments      | 4.0x+           | Lecture videos |

## 🐛 Troubleshooting

### Common Issues:

1. **API Key Not Set**:
   ```
   Error: DEEPINFRA_API_KEY environment variable not set
   ```
   **Solution**: Set the environment variable or create a `.env` file

2. **Missing Dependencies**:
   ```
   Error: Missing packages
   ```
   **Solution**: Install required packages with pip

3. **Rate Limiting**:
   ```
   Error: API request failed with status 429
   ```
   **Solution**: The async service includes rate limiting, but you may need to adjust `max_requests_per_second`

4. **Memory Issues**:
   **Solution**: Reduce `max_concurrent_requests` in the AsyncDeepInfraService

### Performance Debugging:

- Check your internet connection speed
- Monitor API response times
- Verify cache directory permissions
- Look for manim rendering errors

## 🔮 Future Enhancements

Potential improvements to the async approach:
- Intelligent batching based on text similarity
- Progressive loading during animation
- Multi-voice parallel processing
- Smart cache warming strategies
- Adaptive concurrency based on API performance

## 📝 Notes

- The benchmark uses Kokoro TTS model via DeepInfra
- Cache files are reused between runs for consistency
- Rendering quality is set to 720p for faster benchmarking
- Both scenes produce visually identical output

## 🤝 Contributing

To extend this benchmark:
1. Add more complex scenes with varied voiceover patterns
2. Test different TTS services and models
3. Implement additional performance metrics
4. Add memory usage tracking
5. Create visualizations of the performance data

---

**Happy benchmarking! 🚀** 