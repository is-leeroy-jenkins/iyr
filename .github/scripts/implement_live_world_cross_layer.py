from pathlib import Path


path = Path( 'live_world.py' )
text = path.read_text( encoding='utf-8' )

old = """AI_ADVANCED_TOOLS: Dict[ str, str ] = {
\t'cross_layer_analysis': '🧭 Cross-Layer Analysis',
\t'geofencing': '🛡️ Geofencing',
\t'agent_tools': '🤖 Agent Tools',
\t'historical_replay': '🕓 Historical Replay',
}
"""
new = """AI_ADVANCED_TOOLS: Dict[ str, str ] = {
\t'cross_layer_analysis': '🧭 Cross-Layer Analysis',
}

AI_ADVANCED_PENDING_TOOLS: Dict[ str, str ] = {
\t'geofencing': '🛡️ Geofencing',
\t'agent_tools': '🤖 Agent Tools',
\t'historical_replay': '🕓 Historical Replay',
}
"""
if old not in text:
    raise RuntimeError( 'Advanced tools dictionary anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t'live_world_annotations': [ ],
\t\t'live_world_refresh_requested': False,
"""
new = """\t\t'live_world_annotations': [ ],
\t\t'live_world_cross_layer_analysis': False,
\t\t'live_world_analysis_origin': 'Current Location',
\t\t'live_world_analysis_custom_latitude': 0.0,
\t\t'live_world_analysis_custom_longitude': 0.0,
\t\t'live_world_analysis_radius_nm': 250,
\t\t'live_world_analysis_entity_types': [
\t\t\t'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel', 'Earthquake', 'Fire' ],
\t\t'live_world_analysis_limit': 100,
\t\t'live_world_refresh_requested': False,
"""
if old not in text:
    raise RuntimeError( 'Cross-layer state anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\twith st.expander( 'AI & Advanced Tools', expanded=False ):
\t\t\tst.caption( 'Advanced tools activate after their dependent live layers are operational.' )
\t\t\tfor label in AI_ADVANCED_TOOLS.values( ):
\t\t\t\tst.checkbox( label, value=False, disabled=True )
"""
new = """\t\twith st.expander( 'AI & Advanced Tools', expanded=False ):
\t\t\tst.caption( 'Advanced tools operate on the currently loaded Live World entity frame.' )
\t\t\tst.checkbox( AI_ADVANCED_TOOLS[ 'cross_layer_analysis' ],
\t\t\t\tkey='live_world_cross_layer_analysis' )
\t\t\tif st.session_state[ 'live_world_cross_layer_analysis' ]:
\t\t\t\tanalysis_options = get_live_world_analysis_origin_options( )
\t\t\t\tanalysis_keys = list( analysis_options.keys( ) )
\t\t\t\tif st.session_state[ 'live_world_analysis_origin' ] not in analysis_keys:
\t\t\t\t\tst.session_state[ 'live_world_analysis_origin' ] = 'Current Location'
\t\t\t\tst.selectbox( 'Analysis Origin', options=analysis_keys,
\t\t\t\t\tformat_func=lambda value: analysis_options[ value ],
\t\t\t\t\tkey='live_world_analysis_origin' )
\t\t\t\tif st.session_state[ 'live_world_analysis_origin' ] == 'Custom Point':
\t\t\t\t\tanalysis_c1, analysis_c2 = st.columns( 2 )
\t\t\t\t\twith analysis_c1:
\t\t\t\t\t\tst.number_input( 'Analysis Latitude', min_value=-90.0, max_value=90.0,
\t\t\t\t\t\t\tformat='%.6f', key='live_world_analysis_custom_latitude' )
\t\t\t\t\twith analysis_c2:
\t\t\t\t\t\tst.number_input( 'Analysis Longitude', min_value=-180.0, max_value=180.0,
\t\t\t\t\t\t\tformat='%.6f', key='live_world_analysis_custom_longitude' )
\t\t\t\tst.slider( 'Analysis Radius (NM)', min_value=10, max_value=2500,
\t\t\t\t\tstep=10, key='live_world_analysis_radius_nm' )
\t\t\t\tst.multiselect( 'Entity Types',
\t\t\t\t\toptions=[ 'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel',
\t\t\t\t\t\t'Earthquake', 'Fire' ],
\t\t\t\t\tkey='live_world_analysis_entity_types' )
\t\t\t\tst.slider( 'Analysis Result Limit', min_value=10, max_value=500,
\t\t\t\t\tstep=10, key='live_world_analysis_limit' )
\t\t\tfor label in AI_ADVANCED_PENDING_TOOLS.values( ):
\t\t\t\tst.checkbox( label, value=False, disabled=True )
"""
if old not in text:
    raise RuntimeError( 'Advanced sidebar anchor not found.' )
text = text.replace( old, new, 1 )

marker = "\ndef clear_live_world_tracking( ) -> None:\n"
if marker not in text:
    raise RuntimeError( 'Tracking function anchor not found.' )
functions = r'''

def get_live_world_analysis_origin_options( ) -> Dict[ str, str ]:
	'''

		Purpose:
		--------
		Return selectable Cross-Layer Analysis origins from current location and loaded entities.

		Returns:
		--------
		Dict[str, str]: Analysis origin keys mapped to display labels.

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


def resolve_live_world_analysis_origin( key: str, latitude: float,
		longitude: float ) -> Dict[ str, object ]:
	'''

		Purpose:
		--------
		Resolve the configured Cross-Layer Analysis origin into coordinates and a label.

		Parameters:
		-----------
		key (str): Selected analysis origin key.
		latitude (float): Current Iyr/global latitude.
		longitude (float): Current Iyr/global longitude.

		Returns:
		--------
		Dict[str, object]: Resolved analysis origin.

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
			'Latitude': float( st.session_state[ 'live_world_analysis_custom_latitude' ] ),
			'Longitude': float( st.session_state[ 'live_world_analysis_custom_longitude' ] ),
			'EntityType': '',
			'EntityId': '',
		}
	if not key.startswith( 'Entity::' ):
		raise ValueError( f'Unknown analysis origin: {key}' )
	_, entity_type, entity_id = key.split( '::', 2 )
	df_entities = st.session_state.get( 'live_world_df_entities', pd.DataFrame( ) )
	df_match = df_entities[
		(df_entities[ 'EntityType' ].astype( str ) == entity_type)
		& (df_entities[ 'EntityId' ].astype( str ) == entity_id) ].copy( )
	if df_match.empty:
		raise ValueError( f'Analysis origin entity is no longer available: {entity_id}' )
	row = df_match.iloc[ 0 ]
	return {
		'Label': f'{entity_type} | {row[ "Name" ]}',
		'Latitude': float( row[ 'Latitude' ] ),
		'Longitude': float( row[ 'Longitude' ] ),
		'EntityType': entity_type,
		'EntityId': entity_id,
	}


def calculate_live_world_cross_layer_analysis( latitude: float,
		longitude: float ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Rank loaded Live World entities by distance from the configured analysis origin.

		Parameters:
		-----------
		latitude (float): Current Iyr/global latitude.
		longitude (float): Current Iyr/global longitude.

		Returns:
		--------
		pd.DataFrame: Radius-filtered entities ordered by nearest distance.

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
	entity_types = list( st.session_state.get( 'live_world_analysis_entity_types', [ ] ) or [ ] )
	if not entity_types:
		return pd.DataFrame( columns=columns )
	origin = resolve_live_world_analysis_origin(
		str( st.session_state[ 'live_world_analysis_origin' ] ), latitude, longitude )
	df_analysis = df_entities[ df_entities[ 'EntityType' ].isin( entity_types ) ].copy( )
	if df_analysis.empty:
		return pd.DataFrame( columns=columns )
	df_analysis[ 'Latitude' ] = pd.to_numeric( df_analysis[ 'Latitude' ], errors='coerce' )
	df_analysis[ 'Longitude' ] = pd.to_numeric( df_analysis[ 'Longitude' ], errors='coerce' )
	df_analysis = df_analysis.dropna( subset=[ 'Latitude', 'Longitude' ] )
	rows: List[ Dict[ str, object ] ] = [ ]
	for _, row in df_analysis.iterrows( ):
		if (str( origin[ 'EntityType' ] ) == str( row[ 'EntityType' ] )
				and str( origin[ 'EntityId' ] ) == str( row[ 'EntityId' ] )
				and str( origin[ 'EntityId' ] )):
			continue
		distance_nm = calculate_live_world_distance_nm(
			float( origin[ 'Latitude' ] ), float( origin[ 'Longitude' ] ),
			float( row[ 'Latitude' ] ), float( row[ 'Longitude' ] ) )
		if distance_nm > float( st.session_state[ 'live_world_analysis_radius_nm' ] ):
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
	df_result = pd.DataFrame( rows )
	df_result = df_result.sort_values( by='DistanceNM', ascending=True, kind='stable' )
	limit = int( st.session_state[ 'live_world_analysis_limit' ] )
	return df_result.head( limit ).reset_index( drop=True )
'''
text = text.replace( marker, functions + marker, 1 )

old = """\tdf_fires = df_map[ df_map[ 'EntityType' ] == 'Fire' ].copy( )

\tif not df_aircraft.empty:
"""
new = """\tdf_fires = df_map[ df_map[ 'EntityType' ] == 'Fire' ].copy( )

\tdf_analysis = pd.DataFrame( )
\tanalysis_origin: Dict[ str, object ] = { }
\tanalysis_error = ''
\tif st.session_state[ 'live_world_cross_layer_analysis' ]:
\t\ttry:
\t\t\tanalysis_origin = resolve_live_world_analysis_origin(
\t\t\t\tstr( st.session_state[ 'live_world_analysis_origin' ] ), latitude, longitude )
\t\t\tdf_analysis = calculate_live_world_cross_layer_analysis( latitude, longitude )
\t\t\tdf_analysis_origin = pd.DataFrame( [ analysis_origin ] )
\t\t\tdf_analysis_origin[ 'Radius' ] = float(
\t\t\t\tst.session_state[ 'live_world_analysis_radius_nm' ] ) * 1852.0
\t\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_analysis_origin,
\t\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',
\t\t\t\tget_fill_color=[ 80, 180, 255, 20 ], get_line_color=[ 80, 180, 255, 180 ],
\t\t\t\tline_width_min_pixels=2, radius_min_pixels=1,
\t\t\t\tfilled=True, stroked=True, pickable=False ) )
\t\t\tdf_analysis_origin[ 'Radius' ] = 12000.0 * point_scale
\t\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_analysis_origin,
\t\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',
\t\t\t\tget_fill_color=[ 80, 180, 255, 180 ], get_line_color=[ 255, 255, 255, 255 ],
\t\t\t\tline_width_min_pixels=2, radius_min_pixels=8, radius_max_pixels=30,
\t\t\t\tfilled=True, stroked=True, pickable=False ) )
\t\t\tif not df_analysis.empty:
\t\t\t\tdf_analysis_points = df_analysis.copy( )
\t\t\t\tdf_analysis_points[ 'Radius' ] = 11000.0 * point_scale
\t\t\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_analysis_points,
\t\t\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',
\t\t\t\t\tget_fill_color=[ 255, 255, 255, 35 ], get_line_color=[ 80, 180, 255, 255 ],
\t\t\t\t\tline_width_min_pixels=2, radius_min_pixels=7, radius_max_pixels=28,
\t\t\t\t\tfilled=True, stroked=True, pickable=True ) )
\t\texcept Exception as ex:
\t\t\tanalysis_error = str( ex )

\tif not df_aircraft.empty:
"""
if old not in text:
    raise RuntimeError( 'Map entity-frame anchor not found.' )
text = text.replace( old, new, 1 )

old = """\tif (st.session_state[ 'live_world_tracking' ]
\t\t\tand st.session_state[ 'live_world_tracking_follow' ]
\t\t\tand not df_tracking.empty):
"""
new = """\tif (st.session_state[ 'live_world_cross_layer_analysis' ] and analysis_origin):
\t\tcenter_latitude = float( analysis_origin[ 'Latitude' ] )
\t\tcenter_longitude = float( analysis_origin[ 'Longitude' ] )
\tif (st.session_state[ 'live_world_tracking' ]
\t\t\tand st.session_state[ 'live_world_tracking_follow' ]
\t\t\tand not df_tracking.empty):
"""
if old not in text:
    raise RuntimeError( 'Map centering anchor not found.' )
text = text.replace( old, new, 1 )

old = """\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, tracking_tab, measurements_tab = st.tabs(
\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
\t\t\t'📈 Earthquakes', '🔥 Fires', '🎯 Tracking', '📏 Measurements' ] )
"""
new = """\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, tracking_tab, measurements_tab, analysis_tab = st.tabs(
\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
\t\t\t'📈 Earthquakes', '🔥 Fires', '🎯 Tracking', '📏 Measurements', '🧭 Analysis' ] )
"""
if old not in text:
    raise RuntimeError( 'Tabs anchor not found.' )
text = text.replace( old, new, 1 )

marker = "\ndef get_metadata_number( metadata: object, key: str, default: float=0.0 ) -> float:\n"
if marker not in text:
    raise RuntimeError( 'Metadata function anchor not found.' )
analysis_tab = r'''

	with analysis_tab:
		if not st.session_state[ 'live_world_cross_layer_analysis' ]:
			st.info( 'Enable Cross-Layer Analysis in AI & Advanced Tools.' )
		elif analysis_error:
			st.error( f'Cross-Layer Analysis failed: {analysis_error}' )
		elif df_analysis.empty:
			st.info( 'No loaded entities match the selected radius and entity types.' )
		else:
			nearest = df_analysis.iloc[ 0 ]
			analysis_c1, analysis_c2, analysis_c3, analysis_c4 = st.columns( 4, border=True )
			analysis_c1.metric( 'Entities in Radius', f'{len( df_analysis ):,}' )
			analysis_c2.metric( 'Radius (NM)',
				f'{int( st.session_state[ "live_world_analysis_radius_nm" ] ):,}' )
			analysis_c3.metric( 'Nearest Entity', str( nearest[ 'Name' ] ) )
			analysis_c4.metric( 'Nearest Distance (NM)', f'{float( nearest[ "DistanceNM" ] ):,.2f}' )
			st.caption( f'Origin: {analysis_origin[ "Label" ]}' )
			df_nearest_by_type = df_analysis.sort_values( by='DistanceNM', kind='stable' ).groupby(
				'EntityType', as_index=False ).first( )
			st.markdown( '**Nearest by Entity Type**' )
			st.data_editor( make_live_world_display_frame( df_nearest_by_type ),
				key='live_world_analysis_nearest_by_type_table', use_container_width=True,
				disabled=True, hide_index=True )
			st.markdown( '**Entities Within Radius**' )
			st.data_editor( make_live_world_display_frame( df_analysis ),
				key='live_world_analysis_table', use_container_width=True,
				disabled=True, hide_index=True )
'''
text = text.replace( marker, analysis_tab + marker, 1 )

path.write_text( text, encoding='utf-8' )
