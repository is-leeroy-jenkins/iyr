from pathlib import Path

path = Path( '.github/scripts/implement_additional_map_layers.py' )
text = path.read_text( encoding='utf-8' )
old = "\\t\\t\\t'📈 Earthquakes', '🔥 Fires', '📡 Infrastructure', '📷 Cameras', '🎯 Tracking', '📏 Measurements',"
new = "\\t\\t\\t'📈 Earthquakes', '🔥 Fires', '📡 Infrastructure', '📷 Cameras', '🎯 Tracking',\\n\\t\\t\\t'📏 Measurements',"
if old not in text:
	raise RuntimeError( 'Missing tab-label helper anchor.' )
text = text.replace( old, new, 1 )
old = "\\t\\t\\t'📈 Earthquakes', '🔥 Fires', '📡 Infrastructure', '📷 Cameras', '🗺️ Map Layers', '🎯 Tracking', '📏 Measurements',"
new = "\\t\\t\\t'📈 Earthquakes', '🔥 Fires', '📡 Infrastructure', '📷 Cameras', '🗺️ Map Layers', '🎯 Tracking',\\n\\t\\t\\t'📏 Measurements',"
if old not in text:
	raise RuntimeError( 'Missing replacement tab-label helper anchor.' )
text = text.replace( old, new, 1 )
path.write_text( text, encoding='utf-8' )
