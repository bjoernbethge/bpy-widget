#!/usr/bin/env python
"""
BPY Widget - Rendering Performance Benchmark

Tests rendering performance with different configurations:
- GPU Backends: VULKAN vs OPENGL
- Render Engines: EEVEE Next vs Cycles
- With/without GPU Compositing

Run with: marimo run examples/rendering_benchmark.py
"""

import time

import marimo

__generated_with = "0.17.6"
app = marimo.App(
    app_title="bpy-widget-benchmark",
    auto_download=["ipynb"],
)

with app.setup:
    """Setup"""
    import marimo as mo

    from bpy_widget import BpyWidget
    
    widget = BpyWidget(width=800, height=600, auto_init=True)


@app.cell
def benchmark_info():
    """Benchmark Info"""
    mo.md("""
    # 🚀 Rendering Performance Benchmark
    
    This benchmark tests rendering performance with different GPU backends and render engines.
    
    **Test Configurations:**
    - GPU Backends: VULKAN vs OPENGL
    - Render Engines: EEVEE Next vs Cycles
    - GPU Compositing: Enabled/Disabled
    
    Click "Run Benchmark" to start the test.
    """)


@app.cell
def benchmark_controls():
    """Benchmark Controls"""
    run_benchmark_btn = mo.ui.button(
        label="Run Benchmark",
        kind="success"
    )
    
    resolution_slider = mo.ui.slider(
        start=256, stop=1024, value=512, step=128,
        label="Test Resolution"
    )
    
    iterations_slider = mo.ui.slider(
        start=1, stop=10, value=3, step=1,
        label="Iterations per Test"
    )
    
    mo.vstack([
        mo.md("**Benchmark Settings**"),
        resolution_slider,
        iterations_slider,
        run_benchmark_btn,
    ])
    return iterations_slider, resolution_slider, run_benchmark_btn


@app.cell
def run_benchmark(iterations_slider, resolution_slider, run_benchmark_btn):
    """Run Benchmark"""
    def benchmark_configuration(backend, engine, use_gpu_compositing=True):
        """Benchmark a specific configuration"""
        times = []
        
        # Setup configuration
        widget.set_gpu_backend(backend)
        widget.set_render_engine(engine)
        widget.set_resolution(resolution_slider.value, resolution_slider.value)
        
        # Enable/disable GPU compositing
        if use_gpu_compositing:
            from bpy_widget.core.rendering import enable_compositor_gpu
            enable_compositor_gpu()
        
        # Warm-up render
        widget.render()
        
        # Run benchmark iterations
        for i in range(iterations_slider.value):
            start_time = time.time()
            widget.render()
            render_time = time.time() - start_time
            times.append(render_time)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        return {
            'avg': avg_time,
            'min': min_time,
            'max': max_time,
            'times': times
        }
    
    results = {}
    
    if run_benchmark_btn.value:
        # Test configurations
        configs = [
            ("VULKAN", "BLENDER_EEVEE_NEXT", True),
            ("OPENGL", "BLENDER_EEVEE_NEXT", True),
            ("VULKAN", "BLENDER_EEVEE_NEXT", False),
            ("OPENGL", "BLENDER_EEVEE_NEXT", False),
            ("VULKAN", "CYCLES", True),
            ("OPENGL", "CYCLES", True),
        ]
        
        mo.md("**Running benchmark...** This may take a moment.")
        
        for backend, engine, gpu_comp in configs:
            config_name = f"{backend}_{engine}_{'GPU' if gpu_comp else 'CPU'}"
            try:
                result = benchmark_configuration(backend, engine, gpu_comp)
                results[config_name] = result
            except Exception as e:
                results[config_name] = {'error': str(e)}
    
    results


@app.cell
def display_results(run_benchmark):
    """Display Benchmark Results"""
    def format_results(results):
        """Format benchmark results as markdown table"""
        if not results:
            return "No results yet."
        
        # Create table header
        table = "## 📊 Benchmark Results\n\n"
        table += "| Configuration | Avg Time | Min Time | Max Time |\n"
        table += "|---------------|----------|----------|----------|\n"
        
        # Sort by average time (fastest first)
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].get('avg', float('inf')) if isinstance(x[1], dict) and 'avg' in x[1] else float('inf')
        )
        
        for config_name, result in sorted_results:
            if isinstance(result, dict) and 'error' in result:
                table += f"| {config_name} | ❌ Error | - | - |\n"
            elif isinstance(result, dict) and 'avg' in result:
                avg = result['avg']
                min_t = result['min']
                max_t = result['max']
                table += f"| {config_name} | {avg:.3f}s | {min_t:.3f}s | {max_t:.3f}s |\n"
        
        return table
    
    if not run_benchmark or not isinstance(run_benchmark, dict):
        mo.md("**No benchmark results yet** - Click 'Run Benchmark' to start")
    else:
        results_text = format_results(run_benchmark)
        
        # Add summary
        valid_results = {
            k: v for k, v in run_benchmark.items()
            if isinstance(v, dict) and 'avg' in v
        }
        
        if valid_results:
            fastest = min(valid_results.items(), key=lambda x: x[1]['avg'])
            slowest = max(valid_results.items(), key=lambda x: x[1]['avg'])
            
            speedup = slowest[1]['avg'] / fastest[1]['avg']
            
            summary = f"""
### 🏆 Summary

- **Fastest:** {fastest[0]} ({fastest[1]['avg']:.3f}s)
- **Slowest:** {slowest[0]} ({slowest[1]['avg']:.3f}s)
- **Speedup:** {speedup:.2f}x faster

**Current GPU Backend:** {widget.get_gpu_backend() or 'Unknown'}
            """
            results_text += summary
        
        mo.md(results_text)


@app.cell
def detailed_stats(run_benchmark):
    """Detailed Statistics"""
    def format_detailed_stats(results):
        """Format detailed statistics"""
        stats_text = "## 📈 Detailed Statistics\n\n"
        
        for config_name, result in sorted(results.items()):
            if isinstance(result, dict) and 'times' in result:
                times = result['times']
                stats_text += f"### {config_name}\n\n"
                stats_text += f"- Iterations: {len(times)}\n"
                stats_text += f"- Times: {', '.join([f'{t:.3f}s' for t in times])}\n"
                stats_text += f"- Average: {result['avg']:.3f}s\n"
                stats_text += f"- Min: {result['min']:.3f}s\n"
                stats_text += f"- Max: {result['max']:.3f}s\n\n"
        
        return stats_text
    
    if not run_benchmark or not isinstance(run_benchmark, dict):
        mo.md("")
    else:
        detailed = format_detailed_stats(run_benchmark)
        mo.md(detailed)


@app.cell
def system_info():
    """System Information"""
    try:
        import bpy
        
        info = f"""
## 💻 System Information

- **Blender Version:** {bpy.app.version_string}
- **GPU Backend:** {widget.get_gpu_backend() or 'Unknown'}
- **Render Engine:** {widget.render_engine}
- **Resolution:** {widget.width}x{widget.height}
        """
        
        # Try to get GPU info
        try:
            from bpy_widget.core.rendering import initialize_gpu
            if initialize_gpu():
                import gpu
                if hasattr(gpu, 'capabilities'):
                    caps = gpu.capabilities
                    if hasattr(caps, 'GL_MAX_TEXTURE_SIZE'):
                        info += f"\n- **Max Texture Size:** {caps.GL_MAX_TEXTURE_SIZE}"
        except Exception:
            pass
        
        mo.md(info)
    except Exception as e:
        mo.md(f"**System Info Error:** {e}")


if __name__ == "__main__":
    app.run()

