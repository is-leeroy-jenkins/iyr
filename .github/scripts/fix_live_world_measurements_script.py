from pathlib import Path


path = Path( '.github/scripts/implement_live_world_measurements.py' )
text = path.read_text( encoding='utf-8' )
text = text.replace( "functions = r'''", 'functions = r"""', 1 )
text = text.replace(
    "\n'''\ntext = text.replace( marker, functions + marker, 1 )",
    '\n"""\ntext = text.replace( marker, functions + marker, 1 )', 1 )
path.write_text( text, encoding='utf-8' )
