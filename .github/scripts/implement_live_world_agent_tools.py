from pathlib import Path


path = Path( 'live_world.py' )
text = path.read_text( encoding='utf-8' )

old = "from live_world_sources import AdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive\n"
new = "from live_world_agent_tools import LIVE_WORLD_AGENT_TOOLS, LIVE_WORLD_ENTITY_TYPES\nfrom live_world_sources import AdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive\n"
if old not in text:
    raise RuntimeError( 'Agent Tools import anchor not found.' )
text = text.replace( old, new, 1 )

old = """AI_ADVANCED_TOOLS: Dict[ str, str ] = {
\t'cross_layer_analysis': '🧭 Cross-Layer Analysis',
\t'geofencing': '🛡️ Geofencing',
}

AI_ADVANCED_PENDING_TOOLS: Dict[ str, str ] = {
\t'agent_tools': '🤖 Agent Tools',
\t'historical_replay': '🕓 Historical Replay',
}
"""
new = """AI_ADVANCED_TOOLS: Dict[ str, str ] = {
\t'cross_layer_analysis': '🧭 Cross-Layer Analysis',
\t'geofencing': '🛡️ Geofencing',
\t'agent_tools': '🤖 Agent Tools',
}

AI_ADVANCED_PENDING_TOOLS: Dict[ str, str ] = {
\t'historical_replay': '🕓 Historical Replay',
}
"""
if old not in text:
    raise RuntimeError( 'Advanced tool constants anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t'live_world_geofence_last_refresh_processed': '',
\t\t'live_world_refresh_requested': False,
"""
new = """\t\t'live_world_geofence_last_refresh_processed': '',
\t\t'live_world_agent_tools': False,
\t\t'live_world_agent_tool': 'get_live_world_status',
\t\t'live_world_agent_entity_type': 'All',
\t\t'live_world_agent_query': '',
\t\t'live_world_agent_latitude': 0.0,
\t\t'live_world_agent_longitude': 0.0,
\t\t'live_world_agent_radius_nm': 250,
\t\t'live_world_agent_limit': 50,
\t\t'live_world_agent_result': { },
\t\t'live_world_agent_last_error': '',
\t\t'live_world_refresh_requested': False,
"""
if old not in text:
    raise RuntimeError( 'Agent Tools state anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t\t\tif st.button( 'Clear Geofence Events', icon='🧹',
\t\t\t\t\t\tkey='live_world_geofence_clear_events', width='stretch' ):
\t\t\t\t\tclear_live_world_geofence_events( )
\t\t\tfor label in AI_ADVANCED_PENDING_TOOLS.values( ):
"""
new = """\t\t\t\tif st.button( 'Clear Geofence Events', icon='🧹',
\t\t\t\t\t\tkey='live_world_geofence_clear_events', width='stretch' ):
\t\t\t\t\tclear_live_world_geofence_events( )

\t\t\tst.checkbox( AI_ADVANCED_TOOLS[ 'agent_tools' ], key='live_world_agent_tools' )
\t\t\tif st.session_state[ 'live_world_agent_tools' ]:
\t\t\t\tst.selectbox( 'Agent Tool', options=list( LIVE_WORLD_AGENT_TOOLS.keys( ) ),
\t\t\t\t\tkey='live_world_agent_tool' )
\t\t\t\tagent_tool = st.session_state[ 'live_world_agent_tool' ]
\t\t\t\tif agent_tool in [ 'list_live_world_entities', 'search_live_world_entities',
\t\t\t\t\t\t'find_live_world_nearest' ]:
\t\t\t\t\tst.selectbox( 'Agent Entity Type', options=[ 'All' ] + LIVE_WORLD_ENTITY_TYPES,
\t\t\t\t\t\tkey='live_world_agent_entity_type' )
\t\t\t\tif agent_tool == 'search_live_world_entities':
\t\t\t\t\tst.text_input( 'Agent Search Query', key='live_world_agent_query' )
\t\t\t\tif agent_tool == 'find_live_world_nearest':
\t\t\t\t\tagent_c1, agent_c2 = st.columns( 2 )
\t\t\t\t\twith agent_c1:
\t\t\t\t\t\tst.number_input( 'Agent Latitude', min_value=-90.0, max_value=90.0,
\t\t\t\t\t\t\tformat='%.6f', key='live_world_agent_latitude' )
\t\t\t\t\twith agent_c2:
\t\t\t\t\t\tst.number_input( 'Agent Longitude', min_value=-180.0, max_value=180.0,
\t\t\t\t\t\t\tformat='%.6f', key='live_world_agent_longitude' )
\t\t\t\t\tst.slider( 'Agent Radius (NM)', min_value=5, max_value=2500,
\t\t\t\t\t\tstep=5, key='live_world_agent_radius_nm' )
\t\t\t\tif agent_tool in [ 'list_live_world_entities', 'search_live_world_entities',
\t\t\t\t\t\t'find_live_world_nearest' ]:
\t\t\t\t\tst.slider( 'Agent Result Limit', min_value=1, max_value=500,
\t\t\t\t\t\tstep=1, key='live_world_agent_limit' )
\t\t\t\tif st.button( 'Run Agent Tool', icon='▶️', key='live_world_agent_run',
\t\t\t\t\t\twidth='stretch' ):
\t\t\t\t\trun_live_world_agent_tool( )
\t\t\tfor label in AI_ADVANCED_PENDING_TOOLS.values( ):
"""
if old not in text:
    raise RuntimeError( 'Agent Tools sidebar anchor not found.' )
text = text.replace( old, new, 1 )

anchor = "\ndef clear_live_world_tracking( ) -> None:\n"
if anchor not in text:
    raise RuntimeError( 'Agent Tools function anchor not found.' )
functions = r"""

def run_live_world_agent_tool( ) -> None:
	'''

		Purpose:
		--------
		Execute the selected provider-neutral Live World agent tool from the diagnostic UI.

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )
	tool_name = str( st.session_state[ 'live_world_agent_tool' ] )
	throw_if( 'tool_name', tool_name )
	if tool_name not in LIVE_WORLD_AGENT_TOOLS:
		raise ValueError( f'Unknown Live World agent tool: {tool_name}' )
	tool = LIVE_WORLD_AGENT_TOOLS[ tool_name ]
	try:
		if tool_name == 'get_live_world_status':
			result = tool( )
		elif tool_name == 'list_live_world_entities':
			result = tool(
				str( st.session_state[ 'live_world_agent_entity_type' ] ),
				int( st.session_state[ 'live_world_agent_limit' ] ) )
		elif tool_name == 'search_live_world_entities':
			result = tool(
				str( st.session_state[ 'live_world_agent_query' ] ),
				str( st.session_state[ 'live_world_agent_entity_type' ] ),
				int( st.session_state[ 'live_world_agent_limit' ] ) )
		elif tool_name == 'find_live_world_nearest':
			result = tool(
				float( st.session_state[ 'live_world_agent_latitude' ] ),
				float( st.session_state[ 'live_world_agent_longitude' ] ),
				float( st.session_state[ 'live_world_agent_radius_nm' ] ),
				str( st.session_state[ 'live_world_agent_entity_type' ] ),
				int( st.session_state[ 'live_world_agent_limit' ] ) )
		elif tool_name == 'get_live_world_geofence_status':
			result = tool( )
		elif tool_name == 'get_live_world_tracking_status':
			result = tool( )
		else:
			raise ValueError( f'Unsupported Live World agent tool: {tool_name}' )
		st.session_state[ 'live_world_agent_result' ] = result
		st.session_state[ 'live_world_agent_last_error' ] = ''
	except Exception as ex:
		st.session_state[ 'live_world_agent_result' ] = { }
		st.session_state[ 'live_world_agent_last_error' ] = str( ex )

"""
text = text.replace( anchor, functions + anchor, 1 )

old = """\t\tst.session_state[ 'live_world_geofence_last_refresh_processed' ] = ''
\t\tst.session_state[ 'live_world_last_refresh' ] = ''
"""
new = """\t\tst.session_state[ 'live_world_geofence_last_refresh_processed' ] = ''
\t\tst.session_state[ 'live_world_agent_result' ] = { }
\t\tst.session_state[ 'live_world_agent_last_error' ] = ''
\t\tst.session_state[ 'live_world_last_refresh' ] = ''
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

anchor = "\n\twith geofence_tab:\n"
if anchor not in text:
    raise RuntimeError( 'Agent Tools tab insertion anchor not found.' )
# Agent tab belongs after the complete Geofence block, so append it immediately before function end.
# The render function is the final function in live_world.py.
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
text = text.rstrip( ) + agent_tab + '\n'

path.write_text( text, encoding='utf-8' )
