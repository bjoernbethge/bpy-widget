import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    // Output directory
    outDir: '../src/bpy_widget/static',
    
    // Clean output directory before build
    emptyOutDir: true,
    
    // Build as ES module for anywidget
    lib: {
      entry: resolve(__dirname, 'src/widget.js'),
      formats: ['es'],
      fileName: () => 'widget.js'
    },
    
    // Rollup options
    rollupOptions: {
      output: {
        // Single file output - bundle all modules
        inlineDynamicImports: true,
        
        // Preserve the module structure for anywidget
        format: 'es',
        
        // CSS output name
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) {
            return 'widget.css';
          }
          return assetInfo.name;
        },
        
        // Manual chunks - bundle everything into widget.js
        manualChunks: undefined,
      },
      
      // No external dependencies - bundle everything
      external: [],
      
      // Tree-shake unused code
      treeshake: true
    },
    
    // Target modern browsers
    target: 'es2020',
    
    // Minify
    minify: 'esbuild',
    
    // No sourcemaps for cleaner output
    sourcemap: false,
    
    // Inline smaller assets
    assetsInlineLimit: 4096,
  },
  
  // Resolve aliases
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  },
  
  // CSS options
  css: {
    // Extract CSS to separate file
    extract: 'widget.css',
    
    // Minify CSS
    minify: true
  }
});