from pathlib import Path

path = Path( 'live_world.py' )
text = path.read_text( encoding='utf-8' )
old = """\tst.session_state[ 'live_world_df_fires' ] = pd.DataFrame( )
\tst.session_state[ 'live_world_aircraft_result' ] = { }
"""
new = """\tst.session_state[ 'live_world_df_fires' ] = pd.DataFrame( )
\tst.session_state[ 'live_world_df_infrastructure' ] = pd.DataFrame( )
\tst.session_state[ 'live_world_aircraft_result' ] = { }
"""
if old not in text:
    raise RuntimeError( 'Infrastructure clear DataFrame anchor not found.' )
text = text.replace( old, new, 1 )
old = """\tst.session_state[ 'live_world_firms_result' ] = { }
\tst.session_state[ 'live_world_tracking_history' ] = [ ]
"""
new = """\tst.session_state[ 'live_world_firms_result' ] = { }
\tst.session_state[ 'live_world_infrastructure_result' ] = { }
\tst.session_state[ 'live_world_tracking_history' ] = [ ]
"""
if old not in text:
    raise RuntimeError( 'Infrastructure clear result anchor not found.' )
text = text.replace( old, new, 1 )
path.write_text( text, encoding='utf-8' )
