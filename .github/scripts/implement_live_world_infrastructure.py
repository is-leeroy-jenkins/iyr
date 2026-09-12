from pathlib import Path


sources_path = Path( 'live_world_sources.py' )
sources = sources_path.read_text( encoding='utf-8' )

if 'class OverpassInfrastructure:' not in sources:
    provider = r"""


class OverpassInfrastructure:
	'''

		Purpose:
		--------
		Retrieve nearby public infrastructure features from OpenStreetMap through the
		Overpass API using explicit infrastructure categories.

	'''
	timeout: int
	url: str
	response: Response | None
	category_filters: Dict[ str, List[ str ] ]

	def __init__( self, timeout: int=30 ) -> None:
		'''

			Purpose:
			--------
			Initialize OpenStreetMap Overpass infrastructure access.

			Parameters:
			-----------
			timeout (int): HTTP timeout in seconds.

			Returns:
			--------
			None

		'''
		self.timeout = timeout
		self.url = 'https://overpass-api.de/api/interpreter'
		self.response = None
		self.category_filters = {
			'Airports': [ '["aeroway"="aerodrome"]', '["aeroway"="heliport"]' ],
			'Ports': [ '["harbour"="yes"]', '["amenity"="ferry_terminal"]' ],
			'Power Plants': [ '["power"="plant"]' ],
			'Dams': [ '["waterway"="dam"]' ],
			'Data Centers': [ '["telecom"="data_center"]', '["building"="data_center"]' ],
			'Military Installations': [ '["landuse"="military"]', '["military"]' ],
		}

	def fetch_infrastructure( self, latitude: float, longitude: float,
			radius_km: float, categories: List[ str ], max_results: int ) -> Dict[ str, Any ]:
		'''

			Purpose:
			--------
			Retrieve tagged OpenStreetMap infrastructure within a circular search radius.

			Parameters:
			-----------
			latitude (float): Search-origin latitude.
			longitude (float): Search-origin longitude.
			radius_km (float): Search radius in kilometers.
			categories (List[str]): Infrastructure categories to retrieve.
			max_results (int): Maximum normalized Overpass elements to return.

			Returns:
			--------
			Dict[str, Any]: Overpass elements with an added InfrastructureCategory field.

		'''
		throw_if( 'latitude', latitude )
		throw_if( 'longitude', longitude )
		throw_if( 'radius_km', radius_km )
		throw_if( 'categories', categories )
		throw_if( 'max_results', max_results )
		self.latitude = float( latitude )
		self.longitude = float( longitude )
		self.radius_km = float( radius_km )
		self.categories = list( categories )
		self.max_results = int( max_results )
		if self.latitude < -90.0 or self.latitude > 90.0:
			raise ValueError( 'Argument "latitude" must be between -90 and 90.' )
		if self.longitude < -180.0 or self.longitude > 180.0:
			raise ValueError( 'Argument "longitude" must be between -180 and 180.' )
		if self.radius_km <= 0.0:
			raise ValueError( 'Argument "radius_km" must be greater than zero.' )
		if self.max_results < 1:
			raise ValueError( 'Argument "max_results" must be greater than zero.' )
		for category in self.categories:
			if category not in self.category_filters:
				raise ValueError( f'Unsupported infrastructure category: {category}' )

		radius_meters = int( self.radius_km * 1000.0 )
		selectors: List[ str ] = [ ]
		for category in self.categories:
			for tag_filter in self.category_filters[ category ]:
				selectors.append(
					f'nwr(around:{radius_meters},{self.latitude:.6f},{self.longitude:.6f})'
					f'{tag_filter};' )
		query = '[out:json][timeout:25];(' + ''.join( selectors ) + ');out center tags qt;'
		self.response = requests.post( self.url, data={ 'data': query }, timeout=self.timeout )
		self.response.raise_for_status( )
		payload = self.response.json( ) or { }
		if not isinstance( payload, dict ):
			raise TypeError( 'Overpass response must be a dictionary.' )
		elements = payload.get( 'elements', [ ] ) or [ ]
		if not isinstance( elements, list ):
			raise TypeError( 'Overpass elements must be a list.' )

		rows: List[ Dict[ str, Any ] ] = [ ]
		seen: set[ str ] = set( )
		for element in elements:
			if not isinstance( element, dict ):
				continue
			tags = element.get( 'tags', { } ) or { }
			category = self.classify_infrastructure( tags )
			if not category or category not in self.categories:
				continue
			entity_key = f'{element.get( "type", "" )}:{element.get( "id", "" )}'
			if entity_key in seen:
				continue
			seen.add( entity_key )
			row = dict( element )
			row[ 'InfrastructureCategory' ] = category
			rows.append( row )
			if len( rows ) >= self.max_results:
				break
		payload[ 'elements' ] = rows
		return payload

	def classify_infrastructure( self, tags: Dict[ str, Any ] ) -> str:
		'''

			Purpose:
			--------
			Classify one OpenStreetMap tag collection into a supported infrastructure category.

			Parameters:
			-----------
			tags (Dict[str, Any]): OpenStreetMap feature tags.

			Returns:
			--------
			str: Infrastructure category, or an empty string when unsupported.

		'''
		throw_if( 'tags', tags )
		if tags.get( 'aeroway' ) in [ 'aerodrome', 'heliport' ]:
			return 'Airports'
		if tags.get( 'harbour' ) == 'yes' or tags.get( 'amenity' ) == 'ferry_terminal':
			return 'Ports'
		if tags.get( 'power' ) == 'plant':
			return 'Power Plants'
		if tags.get( 'waterway' ) == 'dam':
			return 'Dams'
		if tags.get( 'telecom' ) == 'data_center' or tags.get( 'building' ) == 'data_center':
			return 'Data Centers'
		if tags.get( 'landuse' ) == 'military' or 'military' in tags:
			return 'Military Installations'
		return ''
"""
    sources = sources.rstrip( ) + provider + '\n'
    sources_path.write_text( sources, encoding='utf-8' )

path = Path( 'live_world.py' )
text = path.read_text( encoding='utf-8' )

old = 'from live_world_sources import AdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive\n'
new = ('from live_world_sources import (\n\tAdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive, OverpassInfrastructure )\n')
if old not in text:
    raise RuntimeError( 'Infrastructure import anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t'measurements': '📏 Measurements & Annotations',
}

LIVE_WORLD_PENDING_LAYERS: Dict[ str, str ] = {
\t'cameras': '📷 CCTV / Web Cameras',
\t'infrastructure': '📡 Infrastructure (Airports, Ports, etc.)',
\t'map_layers': '🗺️ Additional Map Layers',
}
"""
new = """\t'measurements': '📏 Measurements & Annotations',
\t'infrastructure': '📡 Infrastructure (Airports, Ports, etc.)',
}

LIVE_WORLD_PENDING_LAYERS: Dict[ str, str ] = {
\t'cameras': '📷 CCTV / Web Cameras',
\t'map_layers': '🗺️ Additional Map Layers',
}
"""
if old not in text:
    raise RuntimeError( 'Infrastructure layer constants anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t'live_world_firms_area_mode': 'Local Bounding Box',
\t\t'live_world_tracking': False,
"""
new = """\t\t'live_world_firms_area_mode': 'Local Bounding Box',
\t\t'live_world_infrastructure': False,
\t\t'live_world_infrastructure_radius_km': 50,
\t\t'live_world_infrastructure_categories': [
\t\t\t'Airports', 'Ports', 'Power Plants', 'Dams', 'Data Centers' ],
\t\t'live_world_infrastructure_limit': 500,
\t\t'live_world_tracking': False,
"""
if old not in text:
    raise RuntimeError( 'Infrastructure state anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t'live_world_df_fires': pd.DataFrame( ),
\t\t'live_world_aircraft_result': { },
"""
new = """\t\t'live_world_df_fires': pd.DataFrame( ),
\t\t'live_world_df_infrastructure': pd.DataFrame( ),
\t\t'live_world_aircraft_result': { },
"""
if old not in text:
    raise RuntimeError( 'Infrastructure DataFrame state anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\t'live_world_firms_result': { },
\t\t'live_world_map_style': 'Carto Dark Matter',
"""
new = """\t\t'live_world_firms_result': { },
\t\t'live_world_infrastructure_result': { },
\t\t'live_world_map_style': 'Carto Dark Matter',
"""
if old not in text:
    raise RuntimeError( 'Infrastructure result state anchor not found.' )
text = text.replace( old, new, 1 )

old = """\t\twith st.expander( 'Additional Layers', expanded=False ):
\t\t\tst.caption( 'Layers activate as their provider implementations are completed.' )
\t\t\tfor label in LIVE_WORLD_PENDING_LAYERS.values( ):
\t\t\t\tst.checkbox( label, value=False, disabled=True )
"""
new = """\t\twith st.expander( 'Additional Layers', expanded=False ):
\t\t\tst.checkbox( LIVE_WORLD_LAYERS[ 'infrastructure' ], key='live_world_infrastructure' )
\t\t\tif st.session_state[ 'live_world_infrastructure' ]:
\t\t\t\tst.multiselect( 'Infrastructure Categories',
\t\t\t\t\toptions=[ 'Airports', 'Ports', 'Power Plants', 'Dams', 'Data Centers',
\t\t\t\t\t\t'Military Installations' ], key='live_world_infrastructure_categories' )
\t\t\t\tinfra_c1, infra_c2 = st.columns( 2 )
\t\t\t\twith infra_c1:
\t\t\t\t\tst.slider( 'Infrastructure Radius (KM)', min_value=10, max_value=250,
\t\t\t\t\t\tstep=10, key='live_world_infrastructure_radius_km' )
\t\t\t\twith infra_c2:
\t\t\t\t\tst.slider( 'Infrastructure Limit', min_value=50, max_value=2000,
\t\t\t\t\t\tstep=50, key='live_world_infrastructure_limit' )
\t\t\t\tst.caption( 'Infrastructure features are retrieved from OpenStreetMap via Overpass.' )
\t\t\tfor label in LIVE_WORLD_PENDING_LAYERS.values( ):
\t\t\t\tst.checkbox( label, value=False, disabled=True )
"""
if old not in text:
    raise RuntimeError( 'Infrastructure sidebar anchor not found.' )
text = text.replace( old, new, 1 )

# Expand analysis/geofence/history type lists to include Infrastructure.
text = text.replace(
    "'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel', 'Earthquake', 'Fire' ],",
    "'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel', 'Earthquake', 'Fire',\n\t\t\t'Infrastructure' ]," )
text = text.replace(
    "'Earthquake', 'Fire' ],\n\t\t\t\t\tkey='live_world_analysis_entity_types' )",
    "'Earthquake', 'Fire', 'Infrastructure' ],\n\t\t\t\t\tkey='live_world_analysis_entity_types' )" )
text = text.replace(
    "'Earthquake', 'Fire' ],\n\t\t\t\t\tkey='live_world_geofence_entity_types' )",
    "'Earthquake', 'Fire', 'Infrastructure' ],\n\t\t\t\t\tkey='live_world_geofence_entity_types' )" )
text = text.replace(
    "'Earthquake', 'Fire' ], key='live_world_history_entity_types' )",
    "'Earthquake', 'Fire', 'Infrastructure' ], key='live_world_history_entity_types' )" )

anchor = '\ndef get_row_value( row: Dict[ str, Any ], keys: List[ str ] ) -> object:\n'
if anchor not in text:
    raise RuntimeError( 'Infrastructure fetch function anchor not found.' )
function = r"""

def fetch_live_infrastructure( latitude: float, longitude: float ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Retrieve public infrastructure features from OpenStreetMap Overpass and normalize
		them into the Live World GeoEntity contract.

		Parameters:
		-----------
		latitude (float): Current Iyr/global latitude.
		longitude (float): Current Iyr/global longitude.

		Returns:
		--------
		pd.DataFrame: Normalized infrastructure entities.

	'''
	initialize_live_world_state( )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	categories = list( st.session_state.get( 'live_world_infrastructure_categories', [ ] ) or [ ] )
	if not categories:
		return entities_to_dataframe( [ ] )
	radius_km = float( st.session_state[ 'live_world_infrastructure_radius_km' ] )
	limit = int( st.session_state[ 'live_world_infrastructure_limit' ] )
	service = OverpassInfrastructure( timeout=30 )
	result = service.fetch_infrastructure( latitude, longitude, radius_km, categories, limit )
	elements = result.get( 'elements', [ ] ) or [ ]
	entities: List[ GeoEntity ] = [ ]
	observed_at = dt.datetime.now( dt.timezone.utc ).isoformat( )

	for element in elements:
		if not isinstance( element, dict ):
			continue
		center = element.get( 'center', { } ) or { }
		latitude_value = element.get( 'lat', center.get( 'lat', None ) )
		longitude_value = element.get( 'lon', center.get( 'lon', None ) )
		if latitude_value is None or longitude_value is None:
			continue
		try:
			lat = float( latitude_value )
			lon = float( longitude_value )
		except ( TypeError, ValueError ):
			continue
		tags = element.get( 'tags', { } ) or { }
		category = str( element.get( 'InfrastructureCategory', '' ) or 'Infrastructure' )
		osm_type = str( element.get( 'type', '' ) or '' )
		osm_id = str( element.get( 'id', '' ) or '' )
		entity_id = f'OSM-{osm_type}-{osm_id}'
		name = str( tags.get( 'name', '' ) or tags.get( 'operator', '' ) or f'{category} {osm_id}' )
		metadata = {
			'Category': category,
			'OSM Type': osm_type,
			'OSM ID': osm_id,
			'Operator': tags.get( 'operator', '' ),
			'IATA': tags.get( 'iata', '' ),
			'ICAO': tags.get( 'icao', '' ),
			'Website': tags.get( 'website', '' ),
			'Tags': tags,
		}
		entities.append( GeoEntity(
			entity_id=entity_id,
			entity_type='Infrastructure',
			name=name,
			latitude=lat,
			longitude=lon,
			altitude=0.0,
			heading=0.0,
			speed=0.0,
			timestamp=observed_at,
			source='OpenStreetMap Overpass',
			metadata=metadata ) )

	st.session_state[ 'live_world_infrastructure_result' ] = result
	return entities_to_dataframe( entities )

"""
text = text.replace( anchor, function + anchor, 1 )

old = """\t\tif st.session_state[ 'live_world_fires' ]:
\t\t\tdf_fires = fetch_live_fires( latitude, longitude )
\t\t\tst.session_state[ 'live_world_df_fires' ] = df_fires
\t\t\tif not df_fires.empty:
\t\t\t\tframes.append( df_fires )
\t\telse:
\t\t\tst.session_state[ 'live_world_df_fires' ] = pd.DataFrame( )

\t\tdf_entities = pd.concat( frames,
"""
new = """\t\tif st.session_state[ 'live_world_fires' ]:
\t\t\tdf_fires = fetch_live_fires( latitude, longitude )
\t\t\tst.session_state[ 'live_world_df_fires' ] = df_fires
\t\t\tif not df_fires.empty:
\t\t\t\tframes.append( df_fires )
\t\telse:
\t\t\tst.session_state[ 'live_world_df_fires' ] = pd.DataFrame( )

\t\tif st.session_state[ 'live_world_infrastructure' ]:
\t\t\tdf_infrastructure = fetch_live_infrastructure( latitude, longitude )
\t\t\tst.session_state[ 'live_world_df_infrastructure' ] = df_infrastructure
\t\t\tif not df_infrastructure.empty:
\t\t\t\tframes.append( df_infrastructure )
\t\telse:
\t\t\tst.session_state[ 'live_world_df_infrastructure' ] = pd.DataFrame( )

\t\tdf_entities = pd.concat( frames,
"""
if old not in text:
    raise RuntimeError( 'Infrastructure refresh anchor not found.' )
text = text.replace( old, new, 1 )

old = """\tevent_c1, event_c2 = st.columns( 2, border=True )
\tevent_c1.metric( 'Earthquakes',
\t\tf'{int( (df_map[ \"EntityType\" ] == \"Earthquake\").sum( ) ):,}' )
\tevent_c2.metric( 'Fires', f'{int( (df_map[ \"EntityType\" ] == \"Fire\").sum( ) ):,}' )
"""
new = """\tevent_c1, event_c2, event_c3 = st.columns( 3, border=True )
\tevent_c1.metric( 'Earthquakes',
\t\tf'{int( (df_map[ \"EntityType\" ] == \"Earthquake\").sum( ) ):,}' )
\tevent_c2.metric( 'Fires', f'{int( (df_map[ \"EntityType\" ] == \"Fire\").sum( ) ):,}' )
\tevent_c3.metric( 'Infrastructure',
\t\tf'{int( (df_map[ \"EntityType\" ] == \"Infrastructure\").sum( ) ):,}' )
"""
if old not in text:
    raise RuntimeError( 'Infrastructure metrics anchor not found.' )
text = text.replace( old, new, 1 )

old = """\tdf_fires = df_map[ df_map[ 'EntityType' ] == 'Fire' ].copy( )
"""
new = """\tdf_fires = df_map[ df_map[ 'EntityType' ] == 'Fire' ].copy( )
\tdf_infrastructure = df_map[ df_map[ 'EntityType' ] == 'Infrastructure' ].copy( )
"""
if old not in text:
    raise RuntimeError( 'Infrastructure map frame anchor not found.' )
text = text.replace( old, new, 1 )

# Add infrastructure PyDeck layer immediately after Fire layer block by anchoring before tracking frame.
anchor = "\tdf_tracking = get_live_world_tracking_frame( )\n"
if anchor not in text:
    raise RuntimeError( 'Infrastructure map layer insertion anchor not found.' )
layer = """\tif not df_infrastructure.empty:
\t\tdf_infrastructure[ 'Radius' ] = 8500.0 * point_scale
\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_infrastructure,
\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',
\t\t\tget_fill_color=[ 255, 165, 60, 190 ], get_line_color=[ 255, 225, 180, 255 ],
\t\t\tline_width_min_pixels=1, stroked=True, pickable=True ) )

"""
text = text.replace( anchor, layer + anchor, 1 )

old = """\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, tracking_tab, measurements_tab, analysis_tab, geofence_tab, history_tab = st.tabs(
\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
\t\t\t'📈 Earthquakes', '🔥 Fires', '🎯 Tracking', '📏 Measurements', '🧭 Analysis',
\t\t\t'🛡️ Geofence', '🕓 Historical Replay' ] )
"""
new = """\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, infrastructure_tab, tracking_tab, measurements_tab, analysis_tab, geofence_tab, history_tab = st.tabs(
\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
\t\t\t'📈 Earthquakes', '🔥 Fires', '📡 Infrastructure', '🎯 Tracking', '📏 Measurements',
\t\t\t'🧭 Analysis', '🛡️ Geofence', '🕓 Historical Replay' ] )
"""
if old not in text:
    raise RuntimeError( 'Infrastructure tabs anchor not found.' )
text = text.replace( old, new, 1 )

anchor = '\n\twith tracking_tab:\n'
if anchor not in text:
    raise RuntimeError( 'Infrastructure tab insertion anchor not found.' )
tab = r"""

	with infrastructure_tab:
		if df_infrastructure.empty:
			st.info( 'No infrastructure features are loaded.' )
		else:
			categories = df_infrastructure[ 'Metadata' ].map(
				lambda value: value.get( 'Category', '' ) if isinstance( value, dict ) else '' )
			infra_c1, infra_c2 = st.columns( 2, border=True )
			infra_c1.metric( 'Features', f'{len( df_infrastructure.index ):,}' )
			infra_c2.metric( 'Categories', f'{categories.nunique( ):,}' )
			df_display = df_infrastructure.copy( )
			df_display[ 'Category' ] = categories
			st.data_editor( df_display[ [ 'EntityId', 'Category', 'Name', 'Latitude', 'Longitude',
				'Source', 'Metadata' ] ], key='live_world_infrastructure_table',
				use_container_width=True, disabled=True, hide_index=True )
"""
text = text.replace( anchor, tab + anchor, 1 )

path.write_text( text, encoding='utf-8' )
