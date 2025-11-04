import bpy

print("Available extension operations:")
ops = [x for x in dir(bpy.ops.extensions) if not x.startswith('_')]
for op_name in sorted(ops):
    if 'package' in op_name or 'theme' in op_name:
        print(f"\n{op_name}:")
        op = getattr(bpy.ops.extensions, op_name)
        try:
            # Try to get properties
            props = op.get_rna_type().properties if hasattr(op, 'get_rna_type') else None
            if props:
                print(f"  Properties: {[p.identifier for p in props]}")
        except:
            pass

# Test package_disable without parameters
print("\n\nTesting package_disable() without parameters:")
try:
    result = bpy.ops.extensions.package_disable()
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")


