from pathlib import Path


path = Path( 'live_world.py' )
text = path.read_text( encoding='utf-8' )
old = "\tst.session_state[ 'live_world_tracking_history' ] = [ ]\n\tst.session_state[ 'live_world_tracking_active_entity' ] = ''\n\tst.session_state[ 'live_world_last_refresh' ] = ''"
new = "\tst.session_state[ 'live_world_tracking_history' ] = [ ]\n\tst.session_state[ 'live_world_tracking_active_entity' ] = ''\n\tst.session_state[ 'live_world_annotations' ] = [ ]\n\tst.session_state[ 'live_world_last_refresh' ] = ''"
if old not in text:
    raise RuntimeError( 'Live World clear-state anchor not found.' )
text = text.replace( old, new, 1 )
path.write_text( text, encoding='utf-8' )
