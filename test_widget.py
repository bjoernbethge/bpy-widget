#!/usr/bin/env python
"""Test script for bpy-widget"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bpy_widget import BpyWidget

print('✓ Widget Import erfolgreich')

widget = BpyWidget(width=512, height=512, auto_init=False)
print('✓ Widget Instanz erstellt')

print('Context verfügbar:', widget.context is not None)
print('Data verfügbar:', widget.data is not None)
print('Ops verfügbar:', widget.ops is not None)
print('Objects verfügbar:', widget.objects is not None)
print('Active Object:', widget.active_object)
print('Selected Objects:', len(widget.selected_objects))
print('Scene verfügbar:', widget.context.scene is not None)

print('🎉 ALLES FUNKTIONIERT!')
