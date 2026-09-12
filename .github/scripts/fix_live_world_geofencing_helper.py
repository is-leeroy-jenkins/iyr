from pathlib import Path


path = Path( '.github/scripts/implement_live_world_geofencing.py' )
text = path.read_text( encoding='utf-8' )
old_start = "functions = r'''\n"
new_start = 'functions = r"""\n'
if old_start not in text:
    raise RuntimeError( 'Geofencing helper opening delimiter not found.' )
text = text.replace( old_start, new_start, 1 )
old_end = "\tcolumns=columns )\n'''\ntext = text.replace( insert_anchor, functions + insert_anchor, 1 )"
new_end = "\tcolumns=columns )\n\"\"\"\ntext = text.replace( insert_anchor, functions + insert_anchor, 1 )"
if old_end not in text:
    raise RuntimeError( 'Geofencing helper closing delimiter not found.' )
text = text.replace( old_end, new_end, 1 )
path.write_text( text, encoding='utf-8' )
