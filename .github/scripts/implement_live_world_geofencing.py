from pathlib import Path


path = Path( 'live_world.py' )
text = path.read_text( encoding='utf-8' )

old = """AI_ADVANCED_TOOLS: Dict[ str, str ] = {
\t'cross_layer_analysis': '🧭 Cross-Layer Analysis',
}

AI_ADVANCED_PENDING_TOOLS: Dict[ str, str ] = {
\t'geofencing': '🛡️ Geofencing',
\t'agent_tools': '🤖 Agent Tools',
\t'historical_replay': '🕓 Historical Replay',
}
"""
new = """AI_ADVANCED_TOOLS: Dict[ str, str ] = {
\t'cross_layer_analysis': '🧭 Cross-Layer Analysis',
\t'geofencing': '🛡️ Geofencing',
}

AI_ADVANCED_PENDING_TOOLS: Dict[ str, str ] = {
\t'agent_tools': '🤖 Agent Tools',
\t'historical_replay': '🕓 Historical Replay',
}
"""
if old not in text:
    raise RuntimeError( 'Advanced tool constants anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t'live_world_analysis_limit': 100,
\t\t'live_world_refresh_requested': False,
"""
new = """\t\t'live_world_analysis_limit': 100,
\t\t'live_world_geofencing': False,
\t\t'live_world_geofence_origin': 'Current Location',
\t\t'live_world_geofence_custom_latitude': 0.0,
\t\t'live_world_geofence_custom_longitude': 0.0,
\t\t'live_world_geofence_radius_nm': 50,
\t\t'live_world_geofence_entity_types': [
\t\t\t'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel', 'Earthquake', 'Fire' ],
\t\t'live_world_geofence_event_limit': 100,
\t\t'live_world_geofence_events': [ ],
\t\t'live_world_geofence_snapshot': { },
\t\t'live_world_geofence_initialized': False,
\t\t'live_world_geofence_last_refresh_processed': '',
\t\t'live_world_refresh_requested': False,
"""
if old not in text:
    raise RuntimeError( 'Live World default state anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t\t\tst.slider( 'Analysis Result Limit', min_value=10, max_value=500,
\t\t\t\t\tstep=10, key='live_world_analysis_limit' )
\t\t\tfor label in AI_ADVANCED_PENDING_TOOLS.values( ):
"""
new = """\t\t\t\tst.slider( 'Analysis Result Limit', min_value=10, max_value=500,
\t\t\t\t\tstep=10, key='live_world_analysis_limit' )

\t\t\tst.checkbox( AI_ADVANCED_TOOLS[ 'geofencing' ], key='live_world_geofencing' )
\t\t\tif st.session_state[ 'live_world_geofencing' ]:
\t\t\t\tgeofence_options = get_live_world_geofence_origin_options( )
\t\t\t\tgeofence_keys = list( geofence_options.keys( ) )
\t\t\t\tif st.session_state[ 'live_world_geofence_origin' ] not in geofence_keys:
\t\t\t\t\tst.session_state[ 'live_world_geofence_origin' ] = 'Current Location'
\t\t\t\tst.selectbox( 'Geofence Origin', options=geofence_keys,
\t\t\t\t\tformat_func=lambda value: geofence_options[ value ],
\t\t\t\t\tkey='live_world_geofence_origin' )
\t\t\t\tif st.session_state[ 'live_world_geofence_origin' ] == 'Custom Point':
\t\t\t\t\tgeofence_c1, geofence_c2 = st.columns( 2 )
\t\t\t\t\twith geofence_c1:
\t\t\t\t\t\tst.number_input( 'Geofence Latitude', min_value=-90.0, max_value=90.0,
\t\t\t\t\t\t\tformat='%.6f', key='live_world_geofence_custom_latitude' )
\t\t\t\t\twith geofence_c2:
\t\t\t\t\t\tst.number_input( 'Geofence Longitude', min_value=-180.0, max_value=180.0,
\t\t\t\t\t\t\tformat='%.6f', key='live_world_geofence_custom_longitude' )
\t\t\t\tst.slider( 'Geofence Radius (NM)', min_value=5, max_value=1000,
\t\t\t\t\tstep=5, key='live_world_geofence_radius_nm' )
\t\t\t\tst.multiselect( 'Geofence Entity Types',
\t\t\t\t\toptions=[ 'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel',
\t\t\t\t\t\t'Earthquake', 'Fire' ],
\t\t\t\t\tkey='live_world_geofence_entity_types' )
\t\t\t\tst.slider( 'Geofence Event History', min_value=10, max_value=500,
\t\t\t\t\tstep=10, key='live_world_geofence_event_limit' )
\t\t\t\tif st.button( 'Clear Geofence Events', icon='🧹',
\t\t\t\t\t\tkey='live_world_geofence_clear_events', width='stretch' ):
\t\t\t\t\tclear_live_world_geofence_events( )
\t\t\tfor label in AI_ADVANCED_PENDING_TOOLS.values( ):
"""
if old not in text:
    raise RuntimeError( 'Advanced tool sidebar anchor not found.' )
text = text.replace( old, new, 1 )

insert_anchor = "\ndef clear_live_world_tracking( ) -> None:\n"
if insert_anchor not in text:
    raise RuntimeError( 'Geofencing function insertion anchor not found.' )
functions = r'''

def get_live_world_geofence_origin_options( ) -> Dict[ str, str ]:
	'''

		Purpose:
		--------
		Return selectable Geofencing origins from current location and loaded entities.

		Returns:
		--------
		Dict[str, str]: Geofence origin keys mapped to display labels.

	'''
	initialize_live_world_state( )
	options: Dict[ str, str ] = {
		'Current Location': 'Current Location',
		'Custom Point': 'Custom Point',
	}
	df_entities = st.session_state.get( 'live_world_df_entities', pd.DataFrame( ) )
	if df_entities is None or df_entities.empty:
		return options
	for _, row in df_entities.iterrows( ):
		entity_id = str( row[ 'EntityId' ] )
		entity_type = str( row[ 'EntityType' ] )
		name = str( row[ 'Name' ] )
		key = f'Entity::{entity_type}::{entity_id}'
		options[ key ] = f'{entity_type} | {name} | {entity_id}'
	return options


def resolve_live_world_geofence_origin( key: str, latitude: float,
		longitude: float ) -> Dict[ str, object ]:
	'''

		Purpose:
		--------
		Resolve the configured Geofencing origin into coordinates and a display label.

		Parameters:
		-----------
		key (str): Selected geofence origin key.
		latitude (float): Current Iyr/global latitude.
		longitude (float): Current Iyr/global longitude.

		Returns:
		--------
		Dict[str, object]: Resolved geofence origin.

	'''
	throw_if( 'key', key )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	if key == 'Current Location':
		return { 'Label': 'Current Location', 'Latitude': float( latitude ),
			'Longitude': float( longitude ), 'EntityType': '', 'EntityId': '' }
	if key == 'Custom Point':
		return {
			'Label': 'Custom Point',
			'Latitude': float( st.session_state[ 'live_world_geofence_custom_latitude' ] ),
			'Longitude': float( st.session_state[ 'live_world_geofence_custom_longitude' ] ),
			'EntityType': '',
			'EntityId': '',
		}
	if not key.startswith( 'Entity::' ):
		raise ValueError( f'Unknown geofence origin: {key}' )
	_, entity_type, entity_id = key.split( '::', 2 )
	df_entities = st.session_state.get( 'live_world_df_entities', pd.DataFrame( ) )
	df_match = df_entities[
		(df_entities[ 'EntityType' ].astype( str ) == entity_type)
		& (df_entities[ 'EntityId' ].astype( str ) == entity_id) ].copy( )
	if df_match.empty:
		raise ValueError( f'Geofence origin entity is no longer available: {entity_id}' )
	row = df_match.iloc[ 0 ]
	return {
		'Label': f'{entity_type} | {row[ "Name" ]}',
		'Latitude': float( row[ 'Latitude' ] ),
		'Longitude': float( row[ 'Longitude' ] ),
		'EntityType': entity_type,
		'EntityId': entity_id,
	}


def calculate_live_world_geofence( latitude: float, longitude: float ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Return loaded Live World entities currently inside the configured circular geofence.

		Parameters:
		-----------
		latitude (float): Current Iyr/global latitude.
		longitude (float): Current Iyr/global longitude.

		Returns:
		--------
		pd.DataFrame: Geofence members ordered by nearest distance.

	'''
	initialize_live_world_state( )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	columns = [ 'EntityId', 'EntityType', 'Name', 'Latitude', 'Longitude', 'Altitude',
		'Heading', 'Speed', 'Timestamp', 'Source', 'Metadata', 'DistanceNM',
		'DistanceKM', 'DistanceMiles', 'Bearing' ]
	df_entities = st.session_state.get( 'live_world_df_entities', pd.DataFrame( ) )
	if df_entities is None or df_entities.empty:
		return pd.DataFrame( columns=columns )
	entity_types = list( st.session_state.get( 'live_world_geofence_entity_types', [ ] ) or [ ] )
	if not entity_types:
		return pd.DataFrame( columns=columns )
	origin = resolve_live_world_geofence_origin(
		str( st.session_state[ 'live_world_geofence_origin' ] ), latitude, longitude )
	df_geofence = df_entities[ df_entities[ 'EntityType' ].isin( entity_types ) ].copy( )
	df_geofence[ 'Latitude' ] = pd.to_numeric( df_geofence[ 'Latitude' ], errors='coerce' )
	df_geofence[ 'Longitude' ] = pd.to_numeric( df_geofence[ 'Longitude' ], errors='coerce' )
	df_geofence = df_geofence.dropna( subset=[ 'Latitude', 'Longitude' ] )
	rows: List[ Dict[ str, object ] ] = [ ]
	for _, row in df_geofence.iterrows( ):
		if (str( origin[ 'EntityType' ] ) == str( row[ 'EntityType' ] )
				and str( origin[ 'EntityId' ] ) == str( row[ 'EntityId' ] )
				and str( origin[ 'EntityId' ] )):
			continue
		distance_nm = calculate_live_world_distance_nm(
			float( origin[ 'Latitude' ] ), float( origin[ 'Longitude' ] ),
			float( row[ 'Latitude' ] ), float( row[ 'Longitude' ] ) )
		if distance_nm > float( st.session_state[ 'live_world_geofence_radius_nm' ] ):
			continue
		lat_a = math.radians( float( origin[ 'Latitude' ] ) )
		lat_b = math.radians( float( row[ 'Latitude' ] ) )
		delta_lon = math.radians( float( row[ 'Longitude' ] ) - float( origin[ 'Longitude' ] ) )
		y = math.sin( delta_lon ) * math.cos( lat_b )
		x = (math.cos( lat_a ) * math.sin( lat_b )
			- math.sin( lat_a ) * math.cos( lat_b ) * math.cos( delta_lon ))
		bearing = (math.degrees( math.atan2( y, x ) ) + 360.0) % 360.0
		result = row.to_dict( )
		result[ 'DistanceNM' ] = distance_nm
		result[ 'DistanceKM' ] = distance_nm * 1.852
		result[ 'DistanceMiles' ] = distance_nm * 1.150779448
		result[ 'Bearing' ] = bearing
		rows.append( result )
	if not rows:
		return pd.DataFrame( columns=columns )
	return pd.DataFrame( rows ).sort_values(
		by='DistanceNM', ascending=True, kind='stable' ).reset_index( drop=True )


def update_live_world_geofence_events( df_geofence: pd.DataFrame ) -> None:
	'''

		Purpose:
		--------
		Record entity entry and exit transitions for the configured geofence after refreshes.

		Parameters:
		-----------
		df_geofence (pd.DataFrame): Current entities inside the configured geofence.

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )
	throw_if( 'df_geofence', df_geofence )
	current_snapshot: Dict[ str, Dict[ str, object ] ] = { }
	for _, row in df_geofence.iterrows( ):
		key = f'{row[ "EntityType" ]}::{row[ "EntityId" ]}'
		current_snapshot[ key ] = {
			'EntityId': str( row[ 'EntityId' ] ),
			'EntityType': str( row[ 'EntityType' ] ),
			'Name': str( row[ 'Name' ] ),
			'Latitude': float( row[ 'Latitude' ] ),
			'Longitude': float( row[ 'Longitude' ] ),
			'DistanceNM': float( row[ 'DistanceNM' ] ),
			'Source': str( row[ 'Source' ] ),
		}
	previous_snapshot = dict( st.session_state.get( 'live_world_geofence_snapshot', { } ) or { } )
	if not st.session_state[ 'live_world_geofence_initialized' ]:
		st.session_state[ 'live_world_geofence_snapshot' ] = current_snapshot
		st.session_state[ 'live_world_geofence_initialized' ] = True
		return
	entered = sorted( set( current_snapshot ) - set( previous_snapshot ) )
	exited = sorted( set( previous_snapshot ) - set( current_snapshot ) )
	events = list( st.session_state.get( 'live_world_geofence_events', [ ] ) or [ ] )
	observed_at = dt.datetime.now( dt.timezone.utc ).isoformat( )
	for key in entered:
		item = current_snapshot[ key ]
		events.append( {
			'Event': 'Entered', 'EntityId': item[ 'EntityId' ],
			'EntityType': item[ 'EntityType' ], 'Name': item[ 'Name' ],
			'Latitude': item[ 'Latitude' ], 'Longitude': item[ 'Longitude' ],
			'DistanceNM': item[ 'DistanceNM' ], 'Source': item[ 'Source' ],
			'ObservedAt': observed_at,
		} )
	for key in exited:
		item = previous_snapshot[ key ]
		events.append( {
			'Event': 'Exited', 'EntityId': item[ 'EntityId' ],
			'EntityType': item[ 'EntityType' ], 'Name': item[ 'Name' ],
			'Latitude': item[ 'Latitude' ], 'Longitude': item[ 'Longitude' ],
			'DistanceNM': item[ 'DistanceNM' ], 'Source': item[ 'Source' ],
			'ObservedAt': observed_at,
		} )
	limit = int( st.session_state[ 'live_world_geofence_event_limit' ] )
	st.session_state[ 'live_world_geofence_events' ] = events[ -limit: ]
	st.session_state[ 'live_world_geofence_snapshot' ] = current_snapshot


def clear_live_world_geofence_events( ) -> None:
	'''

		Purpose:
		--------
		Clear Geofencing event history and reset the transition baseline.

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )
	st.session_state[ 'live_world_geofence_events' ] = [ ]
	st.session_state[ 'live_world_geofence_snapshot' ] = { }
	st.session_state[ 'live_world_geofence_initialized' ] = False
	st.session_state[ 'live_world_geofence_last_refresh_processed' ] = ''


def get_live_world_geofence_event_frame( ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Return current Geofencing transition events as a DataFrame.

		Returns:
		--------
		pd.DataFrame: Ordered Geofencing event history.

	'''
	initialize_live_world_state( )
	columns = [ 'Event', 'EntityId', 'EntityType', 'Name', 'Latitude', 'Longitude',
		'DistanceNM', 'Source', 'ObservedAt' ]
	return pd.DataFrame( st.session_state.get( 'live_world_geofence_events', [ ] ) or [ ],
		columns=columns )
'''
text = text.replace( insert_anchor, functions + insert_anchor, 1 )

old = """\tst.session_state[ 'live_world_annotations' ] = [ ]
\tst.session_state[ 'live_world_last_refresh' ] = ''
"""
new = """\tst.session_state[ 'live_world_annotations' ] = [ ]
\tst.session_state[ 'live_world_geofence_events' ] = [ ]
\tst.session_state[ 'live_world_geofence_snapshot' ] = { }
\tst.session_state[ 'live_world_geofence_initialized' ] = False
\tst.session_state[ 'live_world_geofence_last_refresh_processed' ] = ''
\tst.session_state[ 'live_world_last_refresh' ] = ''
"""
if old not in text:
    raise RuntimeError( 'Clear-state geofencing anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\texcept Exception as ex:
\t\t\tanalysis_error = str( ex )

\tif not df_aircraft.empty:
"""
new = """\t\texcept Exception as ex:
\t\t\tanalysis_error = str( ex )

\tdf_geofence = pd.DataFrame( )
\tgeofence_origin: Dict[ str, object ] = { }
\tgeofence_error = ''
\tif st.session_state[ 'live_world_geofencing' ]:
\t\ttry:
\t\t\tgeofence_origin = resolve_live_world_geofence_origin(
\t\t\t\tstr( st.session_state[ 'live_world_geofence_origin' ] ), latitude, longitude )
\t\t\tdf_geofence = calculate_live_world_geofence( latitude, longitude )
\t\t\tdf_geofence_origin = pd.DataFrame( [ geofence_origin ] )
\t\t\tdf_geofence_origin[ 'Radius' ] = float(
\t\t\t\tst.session_state[ 'live_world_geofence_radius_nm' ] ) * 1852.0
\t\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_geofence_origin,
\t\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',
\t\t\t\tget_fill_color=[ 255, 80, 80, 15 ], get_line_color=[ 255, 80, 80, 190 ],
\t\t\t\tline_width_min_pixels=2, radius_min_pixels=1,
\t\t\t\tfilled=True, stroked=True, pickable=False ) )
\t\t\tdf_geofence_origin[ 'Radius' ] = 12000.0 * point_scale
\t\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_geofence_origin,
\t\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',
\t\t\t\tget_fill_color=[ 255, 80, 80, 180 ], get_line_color=[ 255, 255, 255, 255 ],
\t\t\t\tline_width_min_pixels=2, radius_min_pixels=8, radius_max_pixels=30,
\t\t\t\tfilled=True, stroked=True, pickable=False ) )
\t\t\tif not df_geofence.empty:
\t\t\t\tdf_geofence_points = df_geofence.copy( )
\t\t\t\tdf_geofence_points[ 'Radius' ] = 11000.0 * point_scale
\t\t\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_geofence_points,
\t\t\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',
\t\t\t\t\tget_fill_color=[ 255, 80, 80, 45 ], get_line_color=[ 255, 80, 80, 255 ],
\t\t\t\t\tline_width_min_pixels=2, radius_min_pixels=7, radius_max_pixels=28,
\t\t\t\t\tfilled=True, stroked=True, pickable=True ) )
\t\t\tlast_refresh = str( st.session_state.get( 'live_world_last_refresh', '' ) or '' )
\t\t\tlast_processed = str( st.session_state.get(
\t\t\t\t'live_world_geofence_last_refresh_processed', '' ) or '' )
\t\t\tif not st.session_state[ 'live_world_geofence_initialized' ]:
\t\t\t\tupdate_live_world_geofence_events( df_geofence )
\t\t\t\tst.session_state[ 'live_world_geofence_last_refresh_processed' ] = last_refresh
\t\t\telif last_refresh and last_refresh != last_processed:
\t\t\t\tupdate_live_world_geofence_events( df_geofence )
\t\t\t\tst.session_state[ 'live_world_geofence_last_refresh_processed' ] = last_refresh
\t\texcept Exception as ex:
\t\t\tgeofence_error = str( ex )

\tif not df_aircraft.empty:
"""
if old not in text:
    raise RuntimeError( 'Map geofencing insertion anchor not found.' )
text = text.replace( old, new, 1 )

old = """\tif (st.session_state[ 'live_world_cross_layer_analysis' ] and analysis_origin):
\t\tcenter_latitude = float( analysis_origin[ 'Latitude' ] )
\t\tcenter_longitude = float( analysis_origin[ 'Longitude' ] )
"""
new = """\tif (st.session_state[ 'live_world_geofencing' ] and geofence_origin
\t\t\tand not st.session_state[ 'live_world_cross_layer_analysis' ]):
\t\tcenter_latitude = float( geofence_origin[ 'Latitude' ] )
\t\tcenter_longitude = float( geofence_origin[ 'Longitude' ] )
\tif (st.session_state[ 'live_world_cross_layer_analysis' ] and analysis_origin):
\t\tcenter_latitude = float( analysis_origin[ 'Latitude' ] )
\t\tcenter_longitude = float( analysis_origin[ 'Longitude' ] )
"""
if old not in text:
    raise RuntimeError( 'Map center geofencing anchor not found.' )
text = text.replace( old, new, 1 )

old = """\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, tracking_tab, measurements_tab, analysis_tab = st.tabs(
\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
\t\t\t'📈 Earthquakes', '🔥 Fires', '🎯 Tracking', '📏 Measurements', '🧭 Analysis' ] )
"""
new = """\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, tracking_tab, measurements_tab, analysis_tab, geofence_tab = st.tabs(
\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
\t\t\t'📈 Earthquakes', '🔥 Fires', '🎯 Tracking', '📏 Measurements', '🧭 Analysis',
\t\t\t'🛡️ Geofence' ] )
"""
if old not in text:
    raise RuntimeError( 'Geofencing tab declaration anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t\tst.data_editor( make_live_world_display_frame( df_analysis ),
\t\t\t\tkey='live_world_analysis_table', use_container_width=True,
\t\t\t\tdisabled=True, hide_index=True )

def get_metadata_number( metadata: object, key: str, default: float=0.0 ) -> float:
"""
new = """\t\t\tst.data_editor( make_live_world_display_frame( df_analysis ),
\t\t\t\tkey='live_world_analysis_table', use_container_width=True,
\t\t\t\tdisabled=True, hide_index=True )

\twith geofence_tab:
\t\tif not st.session_state[ 'live_world_geofencing' ]:
\t\t\tst.info( 'Enable Geofencing in AI & Advanced Tools.' )
\t\telif geofence_error:
\t\t\tst.error( f'Geofencing failed: {geofence_error}' )
\t\telse:
\t\t\tdf_geofence_events = get_live_world_geofence_event_frame( )
\t\t\tgeofence_c1, geofence_c2, geofence_c3, geofence_c4 = st.columns( 4, border=True )
\t\t\tgeofence_c1.metric( 'Inside Geofence', f'{len( df_geofence ):,}' )
\t\t\tgeofence_c2.metric( 'Radius (NM)',
\t\t\t\tf'{float( st.session_state[ "live_world_geofence_radius_nm" ] ):,.0f}' )
\t\t\tgeofence_c3.metric( 'Events', f'{len( df_geofence_events ):,}' )
\t\t\tlast_event = str( df_geofence_events.iloc[ -1 ][ 'Event' ] ) if not df_geofence_events.empty else 'None'
\t\t\tgeofence_c4.metric( 'Last Event', last_event )
\t\t\tif geofence_origin:
\t\t\t\tst.caption( f'Origin: {geofence_origin[ "Label" ]}' )
\t\t\tif df_geofence.empty:
\t\t\t\tst.info( 'No selected Live World entities are currently inside the geofence.' )
\t\t\telse:
\t\t\t\tst.markdown( '**Entities Inside Geofence**' )
\t\t\t\tst.data_editor( make_live_world_display_frame( df_geofence ),
\t\t\t\t\tkey='live_world_geofence_table', use_container_width=True,
\t\t\t\t\tdisabled=True, hide_index=True )
\t\t\tst.markdown( '**Entry / Exit Events**' )
\t\t\tif df_geofence_events.empty:
\t\t\t\tst.info( 'No geofence transition events have been recorded.' )
\t\t\telse:
\t\t\t\tst.data_editor( df_geofence_events, key='live_world_geofence_events_table',
\t\t\t\t\tuse_container_width=True, disabled=True, hide_index=True )


def get_metadata_number( metadata: object, key: str, default: float=0.0 ) -> float:
"""
if old not in text:
    raise RuntimeError( 'Geofencing tab content anchor not found.' )
text = text.replace( old, new, 1 )

path.write_text( text, encoding='utf-8' )
