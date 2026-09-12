from pathlib import Path


path = Path( 'live_world.py' )
text = path.read_text( encoding='utf-8' )

old = """\tst.session_state[ 'live_world_geofence_last_refresh_processed' ] = ''
\tst.session_state[ 'live_world_last_refresh' ] = ''
"""
new = """\tst.session_state[ 'live_world_geofence_last_refresh_processed' ] = ''
\tst.session_state[ 'live_world_agent_result' ] = { }
\tst.session_state[ 'live_world_agent_last_error' ] = ''
\tst.session_state[ 'live_world_last_refresh' ] = ''
"""
if old not in text:
    raise RuntimeError( 'Agent Tools clear anchor not found.' )
text = text.replace( old, new, 1 )

old = """\ttracking_tab, measurements_tab, analysis_tab, geofence_tab = st.tabs( [
\t\t'🎯 Tracking', '📏 Measurements', '🧭 Analysis', '🛡️ Geofence' ] )
"""
new = """\ttracking_tab, measurements_tab, analysis_tab, geofence_tab, agent_tools_tab = st.tabs( [
\t\t'🎯 Tracking', '📏 Measurements', '🧭 Analysis', '🛡️ Geofence', '🤖 Agent Tools' ] )
"""
if old not in text:
    raise RuntimeError( 'Agent Tools tab anchor not found.' )
text = text.replace( old, new, 1 )

agent_tab = r"""

	with agent_tools_tab:
		if not st.session_state[ 'live_world_agent_tools' ]:
			st.info( 'Enable Agent Tools in AI & Advanced Tools.' )
		else:
			st.markdown( '**Available Callable Tools**' )
			df_tools = pd.DataFrame( [
				{ 'Tool': name, 'Callable': callable( tool ) }
				for name, tool in LIVE_WORLD_AGENT_TOOLS.items( ) ] )
			st.data_editor( df_tools, key='live_world_agent_tools_table',
				use_container_width=True, disabled=True, hide_index=True )
			if st.session_state[ 'live_world_agent_last_error' ]:
				st.error( st.session_state[ 'live_world_agent_last_error' ] )
			else:
				result = st.session_state.get( 'live_world_agent_result', { } )
				if result:
					st.markdown( '**Latest Tool Result**' )
					st.json( result )
				else:
					st.info( 'Run an Agent Tool from the Live World sidebar to inspect its result.' )
"""
if 'with agent_tools_tab:' in text:
    raise RuntimeError( 'Agent Tools tab already exists.' )
text = text.rstrip( ) + agent_tab + '\n'
path.write_text( text, encoding='utf-8' )
