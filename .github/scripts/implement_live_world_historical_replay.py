from pathlib import Path


path = Path( 'live_world.py' )
text = path.read_text( encoding='utf-8' )

old = "from live_world_sources import AdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive\n"
new = """from live_world_history import (
\tclear_live_world_history, get_live_world_history_snapshots, get_live_world_history_summary,
\tload_live_world_history, persist_live_world_history, purge_live_world_history )
from live_world_sources import AdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive
"""
if old not in text:
    raise RuntimeError( 'Historical Replay import anchor not found.' )
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
\t'historical_replay': '🕓 Historical Replay',
}

AI_ADVANCED_PENDING_TOOLS: Dict[ str, str ] = {
\t'agent_tools': '🤖 Agent Tools',
}
"""
if old not in text:
    raise RuntimeError( 'Historical Replay tool constants anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t'live_world_geofence_last_refresh_processed': '',
\t\t'live_world_refresh_requested': False,
"""
new = """\t\t'live_world_geofence_last_refresh_processed': '',
\t\t'live_world_historical_replay': False,
\t\t'live_world_history_persist': True,
\t\t'live_world_history_retention_days': 30,
\t\t'live_world_history_window': '24 Hours',
\t\t'live_world_history_entity_types': [
\t\t\t'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel', 'Earthquake', 'Fire' ],
\t\t'live_world_history_limit': 5000,
\t\t'live_world_history_snapshot': '',
\t\t'live_world_history_last_saved': 0,
\t\t'live_world_history_last_error': '',
\t\t'live_world_refresh_requested': False,
"""
if old not in text:
    raise RuntimeError( 'Historical Replay state anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t\t\tif st.button( 'Clear Geofence Events', icon='🧹',
\t\t\t\t\t\tkey='live_world_geofence_clear_events', width='stretch' ):
\t\t\t\t\tclear_live_world_geofence_events( )
\t\t\tfor label in AI_ADVANCED_PENDING_TOOLS.values( ):
"""
new = """\t\t\t\tif st.button( 'Clear Geofence Events', icon='🧹',
\t\t\t\t\t\tkey='live_world_geofence_clear_events', width='stretch' ):
\t\t\t\t\tclear_live_world_geofence_events( )

\t\t\tst.checkbox( AI_ADVANCED_TOOLS[ 'historical_replay' ],
\t\t\t\tkey='live_world_historical_replay' )
\t\t\tif st.session_state[ 'live_world_historical_replay' ]:
\t\t\t\tst.checkbox( 'Persist Live World Refreshes', key='live_world_history_persist' )
\t\t\t\thistory_c1, history_c2 = st.columns( 2 )
\t\t\t\twith history_c1:
\t\t\t\t\tst.selectbox( 'Replay Window',
\t\t\t\t\t\toptions=[ '1 Hour', '6 Hours', '24 Hours', '7 Days', '30 Days', 'All Retained' ],
\t\t\t\t\t\tkey='live_world_history_window' )
\t\t\t\twith history_c2:
\t\t\t\t\tst.slider( 'Retention (Days)', min_value=1, max_value=365, step=1,
\t\t\t\t\t\tkey='live_world_history_retention_days' )
\t\t\t\tst.multiselect( 'Replay Entity Types',
\t\t\t\t\toptions=[ 'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel',
\t\t\t\t\t\t'Earthquake', 'Fire' ], key='live_world_history_entity_types' )
\t\t\t\tst.slider( 'Replay Record Limit', min_value=100, max_value=25000, step=100,
\t\t\t\t\tkey='live_world_history_limit' )
\t\t\t\thistory_hours = get_live_world_history_window_hours(
\t\t\t\t\tstr( st.session_state[ 'live_world_history_window' ] ) )
\t\t\t\tsnapshot_options = get_live_world_history_snapshots( history_hours )
\t\t\t\tif snapshot_options:
\t\t\t\t\tif st.session_state[ 'live_world_history_snapshot' ] not in snapshot_options:
\t\t\t\t\t\tst.session_state[ 'live_world_history_snapshot' ] = snapshot_options[ 0 ]
\t\t\t\t\tst.selectbox( 'Replay Snapshot', options=snapshot_options,
\t\t\t\t\t\tkey='live_world_history_snapshot' )
\t\t\t\telse:
\t\t\t\t\tst.session_state[ 'live_world_history_snapshot' ] = ''
\t\t\t\t\tst.caption( 'No persisted Live World snapshots are available in this window.' )
\t\t\t\thistory_b1, history_b2 = st.columns( 2 )
\t\t\t\twith history_b1:
\t\t\t\t\tif st.button( 'Purge Expired', icon='🧹', key='live_world_history_purge',
\t\t\t\t\t\t\twidth='stretch' ):
\t\t\t\t\t\tpurge_live_world_history(
\t\t\t\t\t\t\tint( st.session_state[ 'live_world_history_retention_days' ] ) )
\t\t\t\twith history_b2:
\t\t\t\t\tif st.button( 'Clear History', icon='🗑️', key='live_world_history_clear',
\t\t\t\t\t\t\twidth='stretch' ):
\t\t\t\t\t\tclear_live_world_history( )
\t\t\t\t\t\tst.session_state[ 'live_world_history_snapshot' ] = ''
\t\t\tfor label in AI_ADVANCED_PENDING_TOOLS.values( ):
"""
if old not in text:
    raise RuntimeError( 'Historical Replay sidebar anchor not found.' )
text = text.replace( old, new, 1 )

anchor = "\ndef clear_live_world_tracking( ) -> None:\n"
if anchor not in text:
    raise RuntimeError( 'Historical Replay helper function anchor not found.' )
functions = r"""

def get_live_world_history_window_hours( window: str ) -> int:
	'''

		Purpose:
		--------
		Translate the Historical Replay window label into a lookback duration in hours.

		Parameters:
		-----------
		window (str): Historical Replay window label.

		Returns:
		--------
		int: Lookback duration in hours; zero means all retained history.

	'''
	throw_if( 'window', window )
	windows: Dict[ str, int ] = {
		'1 Hour': 1,
		'6 Hours': 6,
		'24 Hours': 24,
		'7 Days': 168,
		'30 Days': 720,
		'All Retained': 0,
	}
	if window not in windows:
		raise ValueError( f'Unsupported Historical Replay window: {window}' )
	return windows[ window ]


def load_live_world_replay_frame( ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Load Historical Replay observations using the current sidebar configuration.

		Returns:
		--------
		pd.DataFrame: Persisted observations through the selected replay snapshot.

	'''
	initialize_live_world_state( )
	snapshot = str( st.session_state.get( 'live_world_history_snapshot', '' ) or '' )
	if not snapshot:
		return pd.DataFrame( )
	entity_types = list( st.session_state.get( 'live_world_history_entity_types', [ ] ) or [ ] )
	if not entity_types:
		return pd.DataFrame( )
	hours = get_live_world_history_window_hours(
		str( st.session_state[ 'live_world_history_window' ] ) )
	return load_live_world_history( hours, entity_types, snapshot,
		int( st.session_state[ 'live_world_history_limit' ] ) )

"""
text = text.replace( anchor, functions + anchor, 1 )

old = """\t\tst.session_state[ 'live_world_df_entities' ] = df_entities
\t\tupdate_live_world_tracking( df_entities )
\t\tst.session_state[ 'live_world_last_refresh' ] = dt.datetime.now( ).strftime(
\t\t\t'%Y-%m-%d %H:%M:%S' )
\t\tst.session_state[ 'live_world_refresh_requested' ] = False
"""
new = """\t\tst.session_state[ 'live_world_df_entities' ] = df_entities
\t\tupdate_live_world_tracking( df_entities )
\t\tobserved_at = dt.datetime.now( dt.timezone.utc ).isoformat( )
\t\tst.session_state[ 'live_world_last_refresh' ] = dt.datetime.now( ).strftime(
\t\t\t'%Y-%m-%d %H:%M:%S' )
\t\tif st.session_state[ 'live_world_history_persist' ]:
\t\t\ttry:
\t\t\t\tst.session_state[ 'live_world_history_last_saved' ] = persist_live_world_history(
\t\t\t\t\tdf_entities, observed_at, observed_at )
\t\t\t\tpurge_live_world_history(
\t\t\t\t\tint( st.session_state[ 'live_world_history_retention_days' ] ) )
\t\t\t\tst.session_state[ 'live_world_history_last_error' ] = ''
\t\t\texcept Exception as history_ex:
\t\t\t\tst.session_state[ 'live_world_history_last_saved' ] = 0
\t\t\t\tst.session_state[ 'live_world_history_last_error' ] = str( history_ex )
\t\tst.session_state[ 'live_world_refresh_requested' ] = False
"""
if old not in text:
    raise RuntimeError( 'Historical Replay persistence anchor not found.' )
text = text.replace( old, new, 1 )

old = """\tif df_map.empty and not st.session_state[ 'live_world_measurements' ]:
\t\tst.info( 'Live World data does not contain usable map coordinates.' )
\t\treturn
"""
new = """\tif (df_map.empty and not st.session_state[ 'live_world_measurements' ]
\t\t\tand not st.session_state[ 'live_world_historical_replay' ]):
\t\tst.info( 'Live World data does not contain usable map coordinates.' )
\t\treturn
"""
if old not in text:
    raise RuntimeError( 'Historical Replay empty-map anchor not found.' )
text = text.replace( old, new, 1 )

old = """\tdeck = pdk.Deck( layers=layers, initial_view_state=view_state,
\t\tmap_style=map_style_options[ st.session_state[ 'live_world_map_style' ] ], tooltip=tooltip )
"""
new = """\tdf_history = pd.DataFrame( )
\tdf_history_latest = pd.DataFrame( )
\tif st.session_state[ 'live_world_historical_replay' ]:
\t\ttry:
\t\t\tdf_history = load_live_world_replay_frame( )
\t\t\tif not df_history.empty:
\t\t\t\tdf_history_latest = df_history.sort_values( by='ObservedAt', kind='stable' ).groupby(
\t\t\t\t\t[ 'EntityType', 'EntityId' ], as_index=False ).last( )
\t\t\t\tdf_replay_points = df_history_latest.copy( )
\t\t\t\tdf_replay_points[ 'Radius' ] = 7000.0 * float(
\t\t\t\t\tst.session_state[ 'live_world_point_scale' ] )
\t\t\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_replay_points,
\t\t\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',
\t\t\t\t\tget_fill_color=[ 180, 120, 255, 180 ], get_line_color=[ 240, 220, 255, 255 ],
\t\t\t\t\tline_width_min_pixels=1, stroked=True, pickable=True ) )
\t\t\t\tmoving_types = [ 'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel' ]
\t\t\t\tpath_rows: List[ Dict[ str, object ] ] = [ ]
\t\t\t\tfor (entity_type, entity_id), group in df_history[
\t\t\t\t\tdf_history[ 'EntityType' ].isin( moving_types ) ].groupby(
\t\t\t\t\t\t[ 'EntityType', 'EntityId' ], sort=False ):
\t\t\t\t\tgroup = group.sort_values( by='ObservedAt', kind='stable' )
\t\t\t\t\tpath_points = group[ [ 'Longitude', 'Latitude' ] ].values.tolist( )
\t\t\t\t\tif len( path_points ) > 1:
\t\t\t\t\t\tpath_rows.append( { 'EntityType': entity_type, 'EntityId': entity_id,
\t\t\t\t\t\t\t'Path': path_points } )
\t\t\t\tif path_rows:
\t\t\t\t\tlayers.append( pdk.Layer( 'PathLayer', data=pd.DataFrame( path_rows ),
\t\t\t\t\t\tget_path='Path', get_color=[ 180, 120, 255, 210 ],
\t\t\t\t\t\tget_width=3, width_min_pixels=2, pickable=True ) )
\t\texcept Exception as history_ex:
\t\t\tst.session_state[ 'live_world_history_last_error' ] = str( history_ex )

\tdeck = pdk.Deck( layers=layers, initial_view_state=view_state,
\t\tmap_style=map_style_options[ st.session_state[ 'live_world_map_style' ] ], tooltip=tooltip )
"""
if old not in text:
    raise RuntimeError( 'Historical Replay map-layer anchor not found.' )
text = text.replace( old, new, 1 )

old = """\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, tracking_tab, measurements_tab, analysis_tab, geofence_tab = st.tabs(
\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
\t\t\t'📈 Earthquakes', '🔥 Fires', '🎯 Tracking', '📏 Measurements', '🧭 Analysis',
\t\t\t'🛡️ Geofence' ] )
"""
new = """\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, tracking_tab, measurements_tab, analysis_tab, geofence_tab, history_tab = st.tabs(
\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
\t\t\t'📈 Earthquakes', '🔥 Fires', '🎯 Tracking', '📏 Measurements', '🧭 Analysis',
\t\t\t'🛡️ Geofence', '🕓 Historical Replay' ] )
"""
if old not in text:
    raise RuntimeError( 'Historical Replay tab anchor not found.' )
text = text.replace( old, new, 1 )

history_tab = r"""

	with history_tab:
		if not st.session_state[ 'live_world_historical_replay' ]:
			st.info( 'Enable Historical Replay in AI & Advanced Tools.' )
		else:
			history_summary = get_live_world_history_summary( )
			history_c1, history_c2, history_c3, history_c4 = st.columns( 4, border=True )
			history_c1.metric( 'Observations', f'{int( history_summary[ "ObservationCount" ] ):,}' )
			history_c2.metric( 'Snapshots', f'{int( history_summary[ "SnapshotCount" ] ):,}' )
			history_c3.metric( 'Replay Records', f'{len( df_history ):,}' )
			history_c4.metric( 'Replay Entities', f'{len( df_history_latest ):,}' )
			if st.session_state[ 'live_world_history_last_error' ]:
				st.error( f'Historical Replay failed: {st.session_state[ "live_world_history_last_error" ]}' )
			st.caption( f'Replay snapshot: {st.session_state.get( "live_world_history_snapshot", "" ) or "None"}' )
			st.caption( f'Last refresh inserted {int( st.session_state.get( "live_world_history_last_saved", 0 ) ):,} historical observations.' )
			if df_history.empty:
				st.info( 'No persisted observations match the selected replay window and entity types.' )
			else:
				st.markdown( '**Replay Positions**' )
				st.data_editor( make_live_world_display_frame( df_history_latest ),
					key='live_world_history_latest_table', use_container_width=True,
					disabled=True, hide_index=True )
				st.markdown( '**Historical Observations**' )
				st.data_editor( make_live_world_display_frame( df_history ),
					key='live_world_history_table', use_container_width=True,
					disabled=True, hide_index=True )
"""
text = text.rstrip( ) + history_tab + '\n'

path.write_text( text, encoding='utf-8' )
