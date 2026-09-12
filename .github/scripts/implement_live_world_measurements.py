from pathlib import Path


path = Path( 'live_world.py' )
text = path.read_text( encoding='utf-8' )

old = """LIVE_WORLD_LAYERS: Dict[ str, str ] = {
\t'aircraft': '✈️ Aircraft (Live)',
\t'military_aircraft': '🛩️ Military Aircraft',
\t'satellites': '🛰️ Satellites',
\t'vessels': '🚢 Vessels & Ships',
\t'earthquakes': '📈 Earthquakes',
\t'fires': '🔥 Fires (Wildfires)',
\t'tracking': '🎯 Tracking & Trails',
}
"""
new = """LIVE_WORLD_LAYERS: Dict[ str, str ] = {
\t'aircraft': '✈️ Aircraft (Live)',
\t'military_aircraft': '🛩️ Military Aircraft',
\t'satellites': '🛰️ Satellites',
\t'vessels': '🚢 Vessels & Ships',
\t'earthquakes': '📈 Earthquakes',
\t'fires': '🔥 Fires (Wildfires)',
\t'tracking': '🎯 Tracking & Trails',
\t'measurements': '📏 Measurements & Annotations',
}
"""
if old not in text:
    raise RuntimeError( 'Implemented layer anchor not found.' )
text = text.replace( old, new, 1 )

old = """LIVE_WORLD_PENDING_LAYERS: Dict[ str, str ] = {
\t'cameras': '📷 CCTV / Web Cameras',
\t'infrastructure': '📡 Infrastructure (Airports, Ports, etc.)',
\t'measurements': '📏 Measurements & Annotations',
\t'map_layers': '🗺️ Additional Map Layers',
}
"""
new = """LIVE_WORLD_PENDING_LAYERS: Dict[ str, str ] = {
\t'cameras': '📷 CCTV / Web Cameras',
\t'infrastructure': '📡 Infrastructure (Airports, Ports, etc.)',
\t'map_layers': '🗺️ Additional Map Layers',
}
"""
if old not in text:
    raise RuntimeError( 'Pending layer anchor not found.' )
text = text.replace( old, new, 1 )

old = "\t\t'live_world_tracking_history': [ ],\n\t\t'live_world_refresh_requested': False,"
new = "\t\t'live_world_tracking_history': [ ],\n\t\t'live_world_measurements': False,\n\t\t'live_world_measurement_start': 'Current Location',\n\t\t'live_world_measurement_end': 'Current Location',\n\t\t'live_world_measurement_custom_start_latitude': 0.0,\n\t\t'live_world_measurement_custom_start_longitude': 0.0,\n\t\t'live_world_measurement_custom_end_latitude': 0.0,\n\t\t'live_world_measurement_custom_end_longitude': 0.0,\n\t\t'live_world_annotation_label': '',\n\t\t'live_world_annotation_latitude': 0.0,\n\t\t'live_world_annotation_longitude': 0.0,\n\t\t'live_world_annotations': [ ],\n\t\t'live_world_refresh_requested': False,"
if old not in text:
    raise RuntimeError( 'Measurement state anchor not found.' )
text = text.replace( old, new, 1 )

old = "\t\tst.checkbox( LIVE_WORLD_LAYERS[ 'tracking' ], key='live_world_tracking' )\n\t\tif st.session_state[ 'live_world_tracking' ]:"
if old not in text:
    raise RuntimeError( 'Tracking sidebar anchor not found.' )
measurement_sidebar = """\t\tst.checkbox( LIVE_WORLD_LAYERS[ 'measurements' ], key='live_world_measurements' )
\t\tif st.session_state[ 'live_world_measurements' ]:
\t\t\tmeasurement_options = get_live_world_measurement_options( )
\t\t\tmeasurement_keys = list( measurement_options.keys( ) )
\t\t\tif st.session_state[ 'live_world_measurement_start' ] not in measurement_keys:
\t\t\t\tst.session_state[ 'live_world_measurement_start' ] = 'Current Location'
\t\t\tif st.session_state[ 'live_world_measurement_end' ] not in measurement_keys:
\t\t\t\tst.session_state[ 'live_world_measurement_end' ] = 'Current Location'
\t\t\tmeasure_c1, measure_c2 = st.columns( 2 )
\t\t\twith measure_c1:
\t\t\t\tst.selectbox( 'Measure From', options=measurement_keys,
\t\t\t\t\tformat_func=lambda value: measurement_options[ value ],
\t\t\t\t\tkey='live_world_measurement_start' )
\t\t\twith measure_c2:
\t\t\t\tst.selectbox( 'Measure To', options=measurement_keys,
\t\t\t\t\tformat_func=lambda value: measurement_options[ value ],
\t\t\t\t\tkey='live_world_measurement_end' )
\t\t\tif st.session_state[ 'live_world_measurement_start' ] == 'Custom Point':
\t\t\t\tcustom_start_c1, custom_start_c2 = st.columns( 2 )
\t\t\t\twith custom_start_c1:
\t\t\t\t\tst.number_input( 'Start Latitude', min_value=-90.0, max_value=90.0,
\t\t\t\t\t\tformat='%.6f', key='live_world_measurement_custom_start_latitude' )
\t\t\t\twith custom_start_c2:
\t\t\t\t\tst.number_input( 'Start Longitude', min_value=-180.0, max_value=180.0,
\t\t\t\t\t\tformat='%.6f', key='live_world_measurement_custom_start_longitude' )
\t\t\tif st.session_state[ 'live_world_measurement_end' ] == 'Custom Point':
\t\t\t\tcustom_end_c1, custom_end_c2 = st.columns( 2 )
\t\t\t\twith custom_end_c1:
\t\t\t\t\tst.number_input( 'End Latitude', min_value=-90.0, max_value=90.0,
\t\t\t\t\t\tformat='%.6f', key='live_world_measurement_custom_end_latitude' )
\t\t\t\twith custom_end_c2:
\t\t\t\t\tst.number_input( 'End Longitude', min_value=-180.0, max_value=180.0,
\t\t\t\t\t\tformat='%.6f', key='live_world_measurement_custom_end_longitude' )

\t\t\tst.caption( 'Annotations' )
\t\t\tst.text_input( 'Annotation Label', key='live_world_annotation_label' )
\t\t\tannotation_c1, annotation_c2 = st.columns( 2 )
\t\t\twith annotation_c1:
\t\t\t\tst.number_input( 'Annotation Latitude', min_value=-90.0, max_value=90.0,
\t\t\t\t\tformat='%.6f', key='live_world_annotation_latitude' )
\t\t\twith annotation_c2:
\t\t\t\tst.number_input( 'Annotation Longitude', min_value=-180.0, max_value=180.0,
\t\t\t\t\tformat='%.6f', key='live_world_annotation_longitude' )
\t\t\tannotation_button_c1, annotation_button_c2 = st.columns( 2 )
\t\t\twith annotation_button_c1:
\t\t\t\tif st.button( 'Add Annotation', icon='📍', key='live_world_annotation_add',
\t\t\t\t\t\twidth='stretch' ):
\t\t\t\t\tadd_live_world_annotation( )
\t\t\twith annotation_button_c2:
\t\t\t\tif st.button( 'Clear Annotations', icon='🧹', key='live_world_annotation_clear',
\t\t\t\t\t\twidth='stretch' ):
\t\t\t\t\tclear_live_world_annotations( )

"""
text = text.replace( old, measurement_sidebar + old, 1 )

marker = "\ndef clear_live_world_tracking( ) -> None:\n"
if marker not in text:
    raise RuntimeError( 'Tracking function marker not found.' )
functions = r'''


def get_live_world_measurement_options( ) -> Dict[ str, str ]:
	'''

		Purpose:
		--------
		Return selectable measurement endpoints from current location and loaded entities.

		Returns:
		--------
		Dict[str, str]: Measurement endpoint keys mapped to display labels.

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


def resolve_live_world_measurement_point( key: str, latitude: float,
		longitude: float, endpoint: str ) -> Dict[ str, object ]:
	'''

		Purpose:
		--------
		Resolve one configured measurement endpoint into coordinates and a display label.

		Parameters:
		-----------
		key (str): Selected endpoint key.
		latitude (float): Current Iyr/global latitude.
		longitude (float): Current Iyr/global longitude.
		endpoint (str): Endpoint selector, either start or end.

		Returns:
		--------
		Dict[str, object]: Resolved endpoint label and coordinates.

	'''
	throw_if( 'key', key )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	throw_if( 'endpoint', endpoint )
	if key == 'Current Location':
		return { 'Label': 'Current Location', 'Latitude': float( latitude ),
			'Longitude': float( longitude ) }
	if key == 'Custom Point':
		if endpoint == 'start':
			return {
				'Label': 'Custom Start',
				'Latitude': float( st.session_state[ 'live_world_measurement_custom_start_latitude' ] ),
				'Longitude': float( st.session_state[ 'live_world_measurement_custom_start_longitude' ] ),
			}
		return {
			'Label': 'Custom End',
			'Latitude': float( st.session_state[ 'live_world_measurement_custom_end_latitude' ] ),
			'Longitude': float( st.session_state[ 'live_world_measurement_custom_end_longitude' ] ),
		}
	if not key.startswith( 'Entity::' ):
		raise ValueError( f'Unknown measurement endpoint: {key}' )
	_, entity_type, entity_id = key.split( '::', 2 )
	df_entities = st.session_state.get( 'live_world_df_entities', pd.DataFrame( ) )
	df_match = df_entities[
		(df_entities[ 'EntityType' ].astype( str ) == entity_type)
		& (df_entities[ 'EntityId' ].astype( str ) == entity_id) ].copy( )
	if df_match.empty:
		raise ValueError( f'Measurement entity is no longer available: {entity_id}' )
	row = df_match.iloc[ 0 ]
	return {
		'Label': f'{entity_type} | {row[ "Name" ]}',
		'Latitude': float( row[ 'Latitude' ] ),
		'Longitude': float( row[ 'Longitude' ] ),
	}


def calculate_live_world_measurement( latitude: float, longitude: float ) -> Dict[ str, object ]:
	'''

		Purpose:
		--------
		Calculate distance and initial bearing between the configured measurement endpoints.

		Parameters:
		-----------
		latitude (float): Current Iyr/global latitude.
		longitude (float): Current Iyr/global longitude.

		Returns:
		--------
		Dict[str, object]: Resolved endpoints, distances, and initial bearing.

	'''
	start = resolve_live_world_measurement_point(
		str( st.session_state[ 'live_world_measurement_start' ] ), latitude, longitude, 'start' )
	end = resolve_live_world_measurement_point(
		str( st.session_state[ 'live_world_measurement_end' ] ), latitude, longitude, 'end' )
	distance_nm = calculate_live_world_distance_nm(
		float( start[ 'Latitude' ] ), float( start[ 'Longitude' ] ),
		float( end[ 'Latitude' ] ), float( end[ 'Longitude' ] ) )
	lat_a = math.radians( float( start[ 'Latitude' ] ) )
	lat_b = math.radians( float( end[ 'Latitude' ] ) )
	delta_lon = math.radians( float( end[ 'Longitude' ] ) - float( start[ 'Longitude' ] ) )
	y = math.sin( delta_lon ) * math.cos( lat_b )
	x = (math.cos( lat_a ) * math.sin( lat_b )
		- math.sin( lat_a ) * math.cos( lat_b ) * math.cos( delta_lon ))
	bearing = (math.degrees( math.atan2( y, x ) ) + 360.0) % 360.0
	return {
		'Start': start,
		'End': end,
		'DistanceNM': distance_nm,
		'DistanceKM': distance_nm * 1.852,
		'DistanceMiles': distance_nm * 1.150779448,
		'Bearing': bearing,
	}


def add_live_world_annotation( ) -> None:
	'''

		Purpose:
		--------
		Add one labeled annotation to the in-session Live World annotation collection.

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )
	label = str( st.session_state.get( 'live_world_annotation_label', '' ) or '' ).strip( )
	throw_if( 'live_world_annotation_label', label )
	latitude = float( st.session_state[ 'live_world_annotation_latitude' ] )
	longitude = float( st.session_state[ 'live_world_annotation_longitude' ] )
	annotations = list( st.session_state.get( 'live_world_annotations', [ ] ) or [ ] )
	annotations.append( {
		'AnnotationId': f'ANNOTATION-{len( annotations ) + 1}',
		'Label': label,
		'Latitude': latitude,
		'Longitude': longitude,
		'CreatedAt': dt.datetime.now( dt.timezone.utc ).isoformat( ),
	} )
	st.session_state[ 'live_world_annotations' ] = annotations


def clear_live_world_annotations( ) -> None:
	'''

		Purpose:
		--------
		Clear all in-session Live World annotations.

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )
	st.session_state[ 'live_world_annotations' ] = [ ]


def get_live_world_annotation_frame( ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Return current Live World annotations as a DataFrame.

		Returns:
		--------
		pd.DataFrame: Annotation records.

	'''
	initialize_live_world_state( )
	columns = [ 'AnnotationId', 'Label', 'Latitude', 'Longitude', 'CreatedAt' ]
	return pd.DataFrame( st.session_state.get( 'live_world_annotations', [ ] ) or [ ],
		columns=columns )
'''
text = text.replace( marker, functions + marker, 1 )

old = """\tdf_entities = st.session_state.get( 'live_world_df_entities', pd.DataFrame( ) )
\tif df_entities is None or df_entities.empty:
\t\tst.info( 'No Live World data has been loaded. Select Refresh in the sidebar.' )
\t\treturn

\tdf_map = df_entities.copy( )
"""
new = """\tdf_entities = st.session_state.get( 'live_world_df_entities', pd.DataFrame( ) )
\tif df_entities is None or df_entities.empty:
\t\tif not st.session_state[ 'live_world_measurements' ]:
\t\t\tst.info( 'No Live World data has been loaded. Select Refresh in the sidebar.' )
\t\t\treturn
\t\tdf_entities = entities_to_dataframe( [ ] )

\tdf_map = df_entities.copy( )
"""
if old not in text:
    raise RuntimeError( 'Empty data anchor not found.' )
text = text.replace( old, new, 1 )

old = """\tdf_map = df_map.dropna( subset=[ 'Latitude', 'Longitude' ] )
\tif df_map.empty:
\t\tst.info( 'Live World data does not contain usable map coordinates.' )
\t\treturn
"""
new = """\tdf_map = df_map.dropna( subset=[ 'Latitude', 'Longitude' ] )
\tif df_map.empty and not st.session_state[ 'live_world_measurements' ]:
\t\tst.info( 'Live World data does not contain usable map coordinates.' )
\t\treturn
"""
if old not in text:
    raise RuntimeError( 'Empty map anchor not found.' )
text = text.replace( old, new, 1 )

old = "\tdf_tracking = get_live_world_tracking_frame( )\n\tif st.session_state[ 'live_world_tracking' ] and not df_tracking.empty:"
if old not in text:
    raise RuntimeError( 'Map tracking anchor not found.' )
map_measurements = """\tdf_measurement = pd.DataFrame( )
\tmeasurement_result: Dict[ str, object ] = { }
\tif st.session_state[ 'live_world_measurements' ]:
\t\ttry:
\t\t\tmeasurement_result = calculate_live_world_measurement( latitude, longitude )
\t\t\tstart = measurement_result[ 'Start' ]
\t\t\tend = measurement_result[ 'End' ]
\t\t\tdf_measurement = pd.DataFrame( [ start, end ] )
\t\t\tpath_data = [ { 'Path': [
\t\t\t\t[ float( start[ 'Longitude' ] ), float( start[ 'Latitude' ] ) ],
\t\t\t\t[ float( end[ 'Longitude' ] ), float( end[ 'Latitude' ] ) ] ] } ]
\t\t\tlayers.append( pdk.Layer( 'PathLayer', data=path_data, get_path='Path',
\t\t\t\tget_color=[ 255, 255, 255, 230 ], get_width=4,
\t\t\t\twidth_min_pixels=2, width_max_pixels=7, pickable=False ) )
\t\t\tdf_measurement[ 'Radius' ] = 10000.0 * point_scale
\t\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_measurement,
\t\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',
\t\t\t\tget_fill_color=[ 255, 255, 255, 80 ], get_line_color=[ 255, 255, 255, 255 ],
\t\t\t\tline_width_min_pixels=2, radius_min_pixels=7, radius_max_pixels=28,
\t\t\t\tfilled=True, stroked=True, pickable=False ) )
\t\texcept Exception as ex:
\t\t\tmeasurement_result = { 'Error': str( ex ) }

\tdf_annotations = get_live_world_annotation_frame( )
\tif st.session_state[ 'live_world_measurements' ] and not df_annotations.empty:
\t\tdf_annotation_points = df_annotations.copy( )
\t\tdf_annotation_points[ 'Radius' ] = 9000.0 * point_scale
\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_annotation_points,
\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',
\t\t\tget_fill_color=[ 255, 210, 0, 180 ], get_line_color=[ 255, 255, 255, 255 ],
\t\t\tline_width_min_pixels=2, radius_min_pixels=7, radius_max_pixels=28,
\t\t\tfilled=True, stroked=True, pickable=True ) )
\t\tlayers.append( pdk.Layer( 'TextLayer', data=df_annotations,
\t\t\tget_position='[Longitude, Latitude]', get_text='Label', get_size=14,
\t\t\tget_color=[ 255, 255, 255, 255 ], get_angle=0,
\t\t\tget_text_anchor='middle', get_alignment_baseline='bottom', pickable=False ) )

"""
text = text.replace( old, map_measurements + old, 1 )

old = """\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, tracking_tab = st.tabs(
\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
\t\t\t'📈 Earthquakes', '🔥 Fires', '🎯 Tracking' ] )
"""
new = """\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, tracking_tab, measurements_tab = st.tabs(
\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
\t\t\t'📈 Earthquakes', '🔥 Fires', '🎯 Tracking', '📏 Measurements' ] )
"""
if old not in text:
    raise RuntimeError( 'Tabs anchor not found.' )
text = text.replace( old, new, 1 )

marker = "\n\ndef get_metadata_number( metadata: object, key: str, default: float=0.0 ) -> float:\n"
if marker not in text:
    raise RuntimeError( 'Metadata function marker not found.' )
tab = r'''

	with measurements_tab:
		if not st.session_state[ 'live_world_measurements' ]:
			st.info( 'Enable Measurements & Annotations in the sidebar.' )
		else:
			if 'Error' in measurement_result:
				st.error( f'Measurement failed: {measurement_result[ "Error" ]}' )
			elif measurement_result:
				measure_c1, measure_c2, measure_c3, measure_c4 = st.columns( 4, border=True )
				measure_c1.metric( 'Nautical Miles', f'{measurement_result[ "DistanceNM" ]:,.2f}' )
				measure_c2.metric( 'Kilometers', f'{measurement_result[ "DistanceKM" ]:,.2f}' )
				measure_c3.metric( 'Miles', f'{measurement_result[ "DistanceMiles" ]:,.2f}' )
				measure_c4.metric( 'Bearing', f'{measurement_result[ "Bearing" ]:,.1f}°' )
				st.data_editor( df_measurement, key='live_world_measurement_table',
					use_container_width=True, disabled=True, hide_index=True )
			st.caption( 'Annotations' )
			if df_annotations.empty:
				st.info( 'No annotations have been added.' )
			else:
				st.data_editor( df_annotations, key='live_world_annotation_table',
					use_container_width=True, disabled=True, hide_index=True )
'''
text = text.replace( marker, tab + marker, 1 )

path.write_text( text, encoding='utf-8' )
