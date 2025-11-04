import bpy

# Check package_enable parameters
print("Testing package_enable:")
try:
    # Try to get the signature
    print("package_enable exists:", hasattr(bpy.ops.extensions, 'package_enable'))
    
    # Try to inspect it
    op = bpy.ops.extensions.package_enable
    print("Operation:", op)
    
    # Try calling it with dummy parameters to see what it expects
    # (This will fail but show us the error message with parameters)
    try:
        result = op(pkg_id='test', repo_index=-1)
        print("Result:", result)
    except Exception as e:
        print("Error when calling:", e)
        print("Error type:", type(e).__name__)
        
except Exception as e:
    print("Error accessing package_enable:", e)

print("\nTesting package_disable:")
try:
    op = bpy.ops.extensions.package_disable
    print("Operation:", op)
    try:
        result = op(pkg_id='test', repo_index=-1)
        print("Result:", result)
    except Exception as e:
        print("Error when calling:", e)
except Exception as e:
    print("Error:", e)


