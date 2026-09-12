from pathlib import Path


def replace_once( text: str, old: str, new: str, label: str ) -> str:
	if old not in text:
		raise RuntimeError( f'Missing implementation anchor: {label}' )
	return text.replace( old, new, 1 )


world_path = Path( 'world.py' )
sources_path = Path( 'sources.py' )
world = world_path.read_text( encoding='utf-8' )
sources = sources_path.read_text( encoding='utf-8' )

world = replace_once(
	world,
	"\tAdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive, OverpassCameras, OverpassInfrastructure )",
	"\tAdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive, OverpassCameras, OverpassInfrastructure,\n\tOverpassMapLayers )",
	'sources import' )

world = replace_once(
	world,
	"\t'cameras': '📷 CCTV / Web Cameras',\n}\n\nLIVE_WORLD_PENDING_LAYERS: Dict[ str, str ] = {\n\t'map_layers': '🗺️ Additional Map Layers',\n}",
	"\t'cameras': '📷 CCTV / Web Cameras',\n\t'map_layers': '🗺️ Additional Map Layers',\n}\n\nLIVE_WORLD_PENDING_LAYERS: Dict[ str, str ] = {\n}",
	'layer registration' )

world = replace_once(
	world,
	"\t\t'live_world_camera_limit': 500,\n\t\t'live_world_tracking': False,",
	"\t\t'live_world_camera_limit': 500,\n\t\t'live_world_map_layers': False,\n\t\t'live_world_map_layer_radius_km': 50,\n\t\t'live_world_map_layer_categories': [\n\t\t\t'Public Transit', 'Bike Share', 'Emergency Services', 'Healthcare',\n\t\t\t'EV Charging', 'Communications', 'Launch Sites' ],\n\t\t'live_world_map_layer_limit': 1000,\n\t\t'live_world_tracking': False,",
	'map layer defaults' )

world = world.replace(
	"\t\t\t'Infrastructure', 'Camera' ],",
	"\t\t\t'Infrastructure', 'Camera', 'Map Feature' ]," )
world = world.replace(
	"\t\t\t'Earthquake', 'Fire', 'Infrastructure' ],",
	"\t\t\t'Earthquake', 'Fire', 'Infrastructure', 'Camera', 'Map Feature' ]," )

world = replace_once(
	world,
	"\t\t'live_world_df_cameras': pd.DataFrame( ),\n\t\t'live_world_aircraft_result': { },",
	"\t\t'live_world_df_cameras': pd.DataFrame( ),\n\t\t'live_world_df_map_layers': pd.DataFrame( ),\n\t\t'live_world_aircraft_result': { },",
	'map layer dataframe state' )
world = replace_once(
	world,
	"\t\t'live_world_camera_result': { },\n\t\t'live_world_map_style': 'Carto Dark Matter',",
	"\t\t'live_world_camera_result': { },\n\t\t'live_world_map_layer_result': { },\n\t\t'live_world_map_style': 'Carto Dark Matter',",
	'map layer raw state' )

sidebar_anchor = "\t\t\t\tst.caption( 'Public camera locations and webcam tags are retrieved from OpenStreetMap via Overpass.' )\n\t\t\tfor label in LIVE_WORLD_PENDING_LAYERS.values( ):\n\t\t\t\tst.checkbox( label, value=False, disabled=True )"
sidebar_replacement = "\t\t\t\tst.caption( 'Public camera locations and webcam tags are retrieved from OpenStreetMap via Overpass.' )\n\n\t\t\tst.checkbox( LIVE_WORLD_LAYERS[ 'map_layers' ], key='live_world_map_layers' )\n\t\t\tif st.session_state[ 'live_world_map_layers' ]:\n\t\t\t\tst.multiselect( 'Map Layer Categories',\n\t\t\t\t\toptions=[ 'Public Transit', 'Bike Share', 'Emergency Services', 'Healthcare',\n\t\t\t\t\t\t'EV Charging', 'Communications', 'Launch Sites' ],\n\t\t\t\t\tkey='live_world_map_layer_categories' )\n\t\t\t\tmap_layer_c1, map_layer_c2 = st.columns( 2 )\n\t\t\t\twith map_layer_c1:\n\t\t\t\t\tst.slider( 'Map Layer Radius (KM)', min_value=5, max_value=250,\n\t\t\t\t\t\tstep=5, key='live_world_map_layer_radius_km' )\n\t\t\t\twith map_layer_c2:\n\t\t\t\t\tst.slider( 'Map Layer Limit', min_value=50, max_value=5000,\n\t\t\t\t\t\tstep=50, key='live_world_map_layer_limit' )\n\t\t\t\tst.caption( 'Contextual public map features are retrieved from OpenStreetMap via Overpass.' )\n\t\t\tfor label in LIVE_WORLD_PENDING_LAYERS.values( ):\n\t\t\t\tst.checkbox( label, value=False, disabled=True )"
world = replace_once( world, sidebar_anchor, sidebar_replacement, 'additional layers sidebar' )

world = replace_once(
	world,
	"\tst.session_state[ 'live_world_df_cameras' ] = pd.DataFrame( )\n\tst.session_state[ 'live_world_aircraft_result' ] = { }",
	"\tst.session_state[ 'live_world_df_cameras' ] = pd.DataFrame( )\n\tst.session_state[ 'live_world_df_map_layers' ] = pd.DataFrame( )\n\tst.session_state[ 'live_world_aircraft_result' ] = { }",
	'clear map layer dataframe' )
world = replace_once(
	world,
	"\tst.session_state[ 'live_world_camera_result' ] = { }\n\tst.session_state[ 'live_world_tracking_history' ] = [ ]",
	"\tst.session_state[ 'live_world_camera_result' ] = { }\n\tst.session_state[ 'live_world_map_layer_result' ] = { }\n\tst.session_state[ 'live_world_tracking_history' ] = [ ]",
	'clear map layer result' )

fetch_map_layers = """
def fetch_live_map_layers( latitude: float, longitude: float ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Retrieve selected contextual public map features from OpenStreetMap Overpass and
		normalize them into the Live World GeoEntity contract.

		Parameters:
		-----------
		latitude (float): Current Iyr/global latitude.
		longitude (float): Current Iyr/global longitude.

		Returns:
		--------
		pd.DataFrame: Normalized contextual map features.

	'''
	initialize_live_world_state( )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	categories = list( st.session_state.get( 'live_world_map_layer_categories', [ ] ) or [ ] )
	if not categories:
		return entities_to_dataframe( [ ] )
	radius_km = float( st.session_state[ 'live_world_map_layer_radius_km' ] )
	limit = int( st.session_state[ 'live_world_map_layer_limit' ] )
	service = OverpassMapLayers( timeout=30 )
	result = service.fetch_features( latitude, longitude, radius_km, categories, limit )
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
		category = str( element.get( 'MapLayerCategory', '' ) or 'Map Feature' )
		osm_type = str( element.get( 'type', '' ) or '' )
		osm_id = str( element.get( 'id', '' ) or '' )
		entity_id = f'OSM-MAP-{osm_type}-{osm_id}'
		name = str( tags.get( 'name', '' ) or tags.get( 'operator', '' )
			or tags.get( 'brand', '' ) or f'{category} {osm_id}' )
		metadata = {
			'Category': category,
			'OSM Type': osm_type,
			'OSM ID': osm_id,
			'Operator': tags.get( 'operator', '' ),
			'Network': tags.get( 'network', '' ),
			'Website': tags.get( 'website', '' ),
			'Amenity': tags.get( 'amenity', '' ),
			'Public Transport': tags.get( 'public_transport', '' ),
			'Tags': tags,
		}
		entities.append( GeoEntity(
			entity_id=entity_id,
			entity_type='Map Feature',
			name=name,
			latitude=lat,
			longitude=lon,
			altitude=0.0,
			heading=0.0,
			speed=0.0,
			timestamp=observed_at,
			source='OpenStreetMap Overpass',
			metadata=metadata ) )

	st.session_state[ 'live_world_map_layer_result' ] = result
	return entities_to_dataframe( entities )


"""
world = replace_once( world, "\ndef get_row_value( row: Dict[ str, Any ], keys: List[ str ] ) -> object:",
	fetch_map_layers + "def get_row_value( row: Dict[ str, Any ], keys: List[ str ] ) -> object:",
	'map feature fetch insertion' )

refresh_anchor = "\t\tdf_entities = pd.concat( frames,\n\t\t\tignore_index=True ) if frames else entities_to_dataframe( [ ] )"
refresh_block = "\t\tif st.session_state[ 'live_world_map_layers' ]:\n\t\t\tdf_map_layers = fetch_live_map_layers( latitude, longitude )\n\t\t\tst.session_state[ 'live_world_df_map_layers' ] = df_map_layers\n\t\t\tif not df_map_layers.empty:\n\t\t\t\tframes.append( df_map_layers )\n\t\telse:\n\t\t\tst.session_state[ 'live_world_df_map_layers' ] = pd.DataFrame( )\n\n" + refresh_anchor
world = replace_once( world, refresh_anchor, refresh_block, 'refresh map feature block' )

world = replace_once(
	world,
	"\tdf_cameras = df_map[ df_map[ 'EntityType' ] == 'Camera' ].copy( )",
	"\tdf_cameras = df_map[ df_map[ 'EntityType' ] == 'Camera' ].copy( )\n\tdf_map_layers = df_map[ df_map[ 'EntityType' ] == 'Map Feature' ].copy( )",
	'map feature frame' )

map_layer_render = """
	if not df_map_layers.empty:
		df_map_layers[ 'Radius' ] = 7000.0 * point_scale
		layers.append( pdk.Layer( 'ScatterplotLayer', data=df_map_layers,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 85, 220, 140, 190 ], get_line_color=[ 220, 255, 235, 255 ],
			line_width_min_pixels=1, radius_min_pixels=4, radius_max_pixels=26,
			filled=True, stroked=True, pickable=True ) )

"""
world = replace_once( world, "\tdf_tracking = get_live_world_tracking_frame( )",
	map_layer_render + "\tdf_tracking = get_live_world_tracking_frame( )", 'map feature rendering' )

world = replace_once(
	world,
	"\tevent_c1, event_c2, event_c3, event_c4 = st.columns( 4, border=True )",
	"\tevent_c1, event_c2, event_c3, event_c4, event_c5 = st.columns( 5, border=True )",
	'metric columns' )
world = replace_once(
	world,
	"\tevent_c4.metric( 'Cameras', f'{int( (df_map[ \"EntityType\" ] == \"Camera\").sum( ) ):,}' )",
	"\tevent_c4.metric( 'Cameras', f'{int( (df_map[ \"EntityType\" ] == \"Camera\").sum( ) ):,}' )\n\tevent_c5.metric( 'Map Features', f'{int( (df_map[ \"EntityType\" ] == \"Map Feature\").sum( ) ):,}' )",
	'map feature metric' )

world = replace_once(
	world,
	"entities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, infrastructure_tab, cameras_tab, tracking_tab, measurements_tab, analysis_tab, geofence_tab, history_tab = st.tabs(",
	"entities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, infrastructure_tab, cameras_tab, map_layers_tab, tracking_tab, measurements_tab, analysis_tab, geofence_tab, history_tab = st.tabs(",
	'tab variables' )
world = replace_once(
	world,
	"\t\t\t'📈 Earthquakes', '🔥 Fires', '📡 Infrastructure', '📷 Cameras', '🎯 Tracking', '📏 Measurements',",
	"\t\t\t'📈 Earthquakes', '🔥 Fires', '📡 Infrastructure', '📷 Cameras', '🗺️ Map Layers', '🎯 Tracking', '📏 Measurements',",
	'tab labels' )

map_tab = """
	with map_layers_tab:
		if df_map_layers.empty:
			st.info( 'No additional map features are loaded.' )
		else:
			categories = df_map_layers[ 'Metadata' ].map(
				lambda value: value.get( 'Category', '' ) if isinstance( value, dict ) else '' )
			map_c1, map_c2 = st.columns( 2, border=True )
			map_c1.metric( 'Features', f'{len( df_map_layers.index ):,}' )
			map_c2.metric( 'Categories', f'{categories.nunique( ):,}' )
			df_display = df_map_layers.copy( )
			df_display[ 'Category' ] = categories
			st.data_editor( make_live_world_display_frame( df_display[ [
				'EntityId', 'Category', 'Name', 'Latitude', 'Longitude', 'Source', 'Metadata' ] ] ),
				key='live_world_map_layers_table', use_container_width=True,
				disabled=True, hide_index=True )

"""
world = replace_once( world, "\twith tracking_tab:", map_tab + "\twith tracking_tab:", 'map layers tab' )

source_class = """

class OverpassMapLayers:
	'''

		Purpose:
		--------
		Retrieve contextual public map features from OpenStreetMap through the Overpass API.

	'''
	timeout: int
	url: str
	response: Response | None
	category_filters: Dict[ str, List[ str ] ]

	def __init__( self, timeout: int=30 ) -> None:
		'''

			Purpose:
			--------
			Initialize OpenStreetMap Overpass contextual map-layer access.

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
			'Public Transit': [ '["public_transport"="station"]', '["railway"="station"]' ],
			'Bike Share': [ '["amenity"="bicycle_rental"]' ],
			'Emergency Services': [ '["amenity"="police"]', '["amenity"="fire_station"]' ],
			'Healthcare': [ '["amenity"="hospital"]', '["amenity"="clinic"]' ],
			'EV Charging': [ '["amenity"="charging_station"]' ],
			'Communications': [
				'["man_made"="tower"]["tower:type"="communication"]',
				'["man_made"="mast"]["tower:type"="communication"]' ],
			'Launch Sites': [ '["aeroway"="spaceport"]', '["man_made"="launch_pad"]' ],
		}

	def fetch_features( self, latitude: float, longitude: float, radius_km: float,
			categories: List[ str ], max_results: int ) -> Dict[ str, Any ]:
		'''

			Purpose:
			--------
			Retrieve selected contextual map features within a circular search radius.

			Parameters:
			-----------
			latitude (float): Search-origin latitude.
			longitude (float): Search-origin longitude.
			radius_km (float): Search radius in kilometers.
			categories (List[str]): Contextual map categories to retrieve.
			max_results (int): Maximum normalized Overpass elements to return.

			Returns:
			--------
			Dict[str, Any]: Overpass elements with an added MapLayerCategory field.

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
				raise ValueError( f'Unsupported map layer category: {category}' )

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
			raise TypeError( 'Overpass map-layer response must be a dictionary.' )
		elements = payload.get( 'elements', [ ] ) or [ ]
		if not isinstance( elements, list ):
			raise TypeError( 'Overpass map-layer elements must be a list.' )

		rows: List[ Dict[ str, Any ] ] = [ ]
		seen: set[ str ] = set( )
		for element in elements:
			if not isinstance( element, dict ):
				continue
			tags = element.get( 'tags', { } ) or { }
			category = self.classify_feature( tags )
			if not category or category not in self.categories:
				continue
			entity_key = f'{element.get( "type", "" )}:{element.get( "id", "" )}'
			if entity_key in seen:
				continue
			seen.add( entity_key )
			row = dict( element )
			row[ 'MapLayerCategory' ] = category
			rows.append( row )
			if len( rows ) >= self.max_results:
				break
		payload[ 'elements' ] = rows
		return payload

	def classify_feature( self, tags: Dict[ str, Any ] ) -> str:
		'''

			Purpose:
			--------
			Classify one OpenStreetMap feature into a supported contextual map category.

			Parameters:
			-----------
			tags (Dict[str, Any]): OpenStreetMap feature tags.

			Returns:
			--------
			str: Contextual map category, or an empty string when unsupported.

		'''
		throw_if( 'tags', tags )
		if tags.get( 'aeroway' ) == 'spaceport' or tags.get( 'man_made' ) == 'launch_pad':
			return 'Launch Sites'
		if tags.get( 'amenity' ) == 'bicycle_rental':
			return 'Bike Share'
		if tags.get( 'amenity' ) in [ 'police', 'fire_station' ]:
			return 'Emergency Services'
		if tags.get( 'amenity' ) in [ 'hospital', 'clinic' ]:
			return 'Healthcare'
		if tags.get( 'amenity' ) == 'charging_station':
			return 'EV Charging'
		if tags.get( 'public_transport' ) == 'station' or tags.get( 'railway' ) == 'station':
			return 'Public Transit'
		if (tags.get( 'man_made' ) in [ 'tower', 'mast' ]
				and tags.get( 'tower:type' ) == 'communication'):
			return 'Communications'
		return ''
"""
if 'class OverpassMapLayers:' not in sources:
	sources = sources.rstrip( ) + source_class + '\n'

world_path.write_text( world, encoding='utf-8' )
sources_path.write_text( sources, encoding='utf-8' )
