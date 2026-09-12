from pathlib import Path
import subprocess


ROOT = Path( '.' )


def replace_once( text: str, old: str, new: str, label: str ) -> str:
    if old not in text:
        raise RuntimeError( f'Anchor not found: {label}' )
    return text.replace( old, new, 1 )


def write_text( path: Path, text: str ) -> None:
    path.write_text( text, encoding='utf-8' )


def git_move( source: str, target: str ) -> None:
    if not Path( source ).exists( ):
        raise RuntimeError( f'Rename source does not exist: {source}' )
    if Path( target ).exists( ):
        raise RuntimeError( f'Rename target already exists: {target}' )
    subprocess.run( [ 'git', 'mv', source, target ], check=True )


# ==============================================================================
# MODULE RENAMES
# ==============================================================================
git_move( 'live_world.py', 'world.py' )
git_move( 'live_world_agent_tools.py', 'tools.py' )
git_move( 'live_world_history.py', 'history.py' )
git_move( 'live_world_sources.py', 'sources.py' )

for stale in [
        '.github/scripts/implement_live_world_agent_tools.py',
        '.github/workflows/implement-live-world-agent-tools.yml' ]:
    stale_path = Path( stale )
    if stale_path.exists( ):
        subprocess.run( [ 'git', 'rm', stale ], check=True )

text_files = [
    path for path in ROOT.rglob( '*' )
    if path.is_file( ) and '.git' not in path.parts
    and path.suffix.lower( ) in [ '.py', '.md', '.yml', '.yaml', '.toml', '.txt' ]
]
for path in text_files:
    text = path.read_text( encoding='utf-8' )
    updated = text
    updated = updated.replace( 'from world import ', 'from world import ' )
    updated = updated.replace( 'from history import ', 'from history import ' )
    updated = updated.replace( 'from sources import ', 'from sources import ' )
    updated = updated.replace( 'from tools import ', 'from tools import ' )
    updated = updated.replace( 'Filename:                world.py', 'Filename:                world.py' )
    updated = updated.replace( 'Filename:                history.py', 'Filename:                history.py' )
    updated = updated.replace( 'Filename:                sources.py', 'Filename:                sources.py' )
    updated = updated.replace( 'Filename:                tools.py', 'Filename:                tools.py' )
    if updated != text:
        path.write_text( updated, encoding='utf-8' )


# ==============================================================================
# CAMERA PROVIDER
# ==============================================================================
sources_path = Path( 'sources.py' )
sources = sources_path.read_text( encoding='utf-8' )
provider = r"""

class OverpassCameras:
	'''

		Purpose:
		--------
		Retrieve nearby public CCTV, surveillance-camera, and webcam features from
		OpenStreetMap through the Overpass API.

	'''
	timeout: int
	url: str
	response: Response | None
	category_filters: Dict[ str, List[ str ] ]

	def __init__( self, timeout: int=30 ) -> None:
		'''

			Purpose:
			--------
			Initialize OpenStreetMap Overpass camera access.

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
			'CCTV / Surveillance': [
				'["man_made"="surveillance"]', '["surveillance:type"="camera"]' ],
			'Web Cameras': [ '["webcam"]', '["contact:webcam"]' ],
		}

	def fetch_cameras( self, latitude: float, longitude: float, radius_km: float,
			categories: List[ str ], max_results: int ) -> Dict[ str, Any ]:
		'''

			Purpose:
			--------
			Retrieve tagged public camera features within a circular search radius.

			Parameters:
			-----------
			latitude (float): Search-origin latitude.
			longitude (float): Search-origin longitude.
			radius_km (float): Search radius in kilometers.
			categories (List[str]): Camera categories to retrieve.
			max_results (int): Maximum normalized Overpass elements to return.

			Returns:
			--------
			Dict[str, Any]: Overpass elements with an added CameraCategory field.

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
				raise ValueError( f'Unsupported camera category: {category}' )

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
			raise TypeError( 'Overpass camera response must be a dictionary.' )
		elements = payload.get( 'elements', [ ] ) or [ ]
		if not isinstance( elements, list ):
			raise TypeError( 'Overpass camera elements must be a list.' )

		rows: List[ Dict[ str, Any ] ] = [ ]
		seen: set[ str ] = set( )
		for element in elements:
			if not isinstance( element, dict ):
				continue
			tags = element.get( 'tags', { } ) or { }
			category = self.classify_camera( tags )
			if not category or category not in self.categories:
				continue
			entity_key = f'{element.get( "type", "" )}:{element.get( "id", "" )}'
			if entity_key in seen:
				continue
			seen.add( entity_key )
			row = dict( element )
			row[ 'CameraCategory' ] = category
			rows.append( row )
			if len( rows ) >= self.max_results:
				break
		payload[ 'elements' ] = rows
		return payload

	def classify_camera( self, tags: Dict[ str, Any ] ) -> str:
		'''

			Purpose:
			--------
			Classify one OpenStreetMap camera feature into a supported camera category.

			Parameters:
			-----------
			tags (Dict[str, Any]): OpenStreetMap feature tags.

			Returns:
			--------
			str: Camera category, or an empty string when unsupported.

		'''
		throw_if( 'tags', tags )
		if tags.get( 'webcam' ) or tags.get( 'contact:webcam' ):
			return 'Web Cameras'
		if tags.get( 'man_made' ) == 'surveillance' or tags.get( 'surveillance:type' ) == 'camera':
			return 'CCTV / Surveillance'
		return ''
"""
if 'class OverpassCameras:' in sources:
    raise RuntimeError( 'OverpassCameras already exists.' )
sources = sources.rstrip( ) + provider + '\n'
sources = sources.replace(
    'military aircraft, maritime AIS positions, and current satellite orbital elements.',
    'military aircraft, maritime AIS positions, current satellite orbital elements, public infrastructure, and public camera features.' )
write_text( sources_path, sources )


# ==============================================================================
# WORLD INTEGRATION
# ==============================================================================
world_path = Path( 'world.py' )
world = world_path.read_text( encoding='utf-8' )
world = replace_once(
    world,
    'AdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive, OverpassInfrastructure )',
    'AdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive, OverpassCameras, '
    'OverpassInfrastructure )',
    'camera provider import' )
world = replace_once(
    world,
    "\t'infrastructure': '📡 Infrastructure (Airports, Ports, etc.)',\n}",
    "\t'infrastructure': '📡 Infrastructure (Airports, Ports, etc.)',\n"
    "\t'cameras': '📷 CCTV / Web Cameras',\n}",
    'camera layer registry' )
world = replace_once(
    world,
    "LIVE_WORLD_PENDING_LAYERS: Dict[ str, str ] = {\n\t'cameras': '📷 CCTV / Web Cameras',\n\t'map_layers': '🗺️ Additional Map Layers',\n}",
    "LIVE_WORLD_PENDING_LAYERS: Dict[ str, str ] = {\n\t'map_layers': '🗺️ Additional Map Layers',\n}",
    'pending camera registry' )
world = replace_once(
    world,
    "\t\t'live_world_infrastructure_limit': 500,\n\t\t'live_world_tracking': False,",
    "\t\t'live_world_infrastructure_limit': 500,\n"
    "\t\t'live_world_cameras': False,\n"
    "\t\t'live_world_camera_radius_km': 25,\n"
    "\t\t'live_world_camera_categories': [ 'CCTV / Surveillance', 'Web Cameras' ],\n"
    "\t\t'live_world_camera_limit': 500,\n"
    "\t\t'live_world_tracking': False,",
    'camera state controls' )
world = world.replace(
    "\t\t\t'Infrastructure' ],",
    "\t\t\t'Infrastructure', 'Camera' ]," )
world = replace_once(
    world,
    "\t\t'live_world_df_infrastructure': pd.DataFrame( ),\n\t\t'live_world_aircraft_result': { },",
    "\t\t'live_world_df_infrastructure': pd.DataFrame( ),\n"
    "\t\t'live_world_df_cameras': pd.DataFrame( ),\n"
    "\t\t'live_world_aircraft_result': { },",
    'camera dataframe state' )
world = replace_once(
    world,
    "\t\t'live_world_infrastructure_result': { },\n\t\t'live_world_map_style': 'Carto Dark Matter',",
    "\t\t'live_world_infrastructure_result': { },\n"
    "\t\t'live_world_camera_result': { },\n"
    "\t\t'live_world_map_style': 'Carto Dark Matter',",
    'camera result state' )

old_additional = """\t\twith st.expander( 'Additional Layers', expanded=False ):
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
new_additional = """\t\twith st.expander( 'Additional Layers', expanded=False ):
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

\t\t\tst.checkbox( LIVE_WORLD_LAYERS[ 'cameras' ], key='live_world_cameras' )
\t\t\tif st.session_state[ 'live_world_cameras' ]:
\t\t\t\tst.multiselect( 'Camera Categories',
\t\t\t\t\toptions=[ 'CCTV / Surveillance', 'Web Cameras' ],
\t\t\t\t\tkey='live_world_camera_categories' )
\t\t\t\tcamera_c1, camera_c2 = st.columns( 2 )
\t\t\t\twith camera_c1:
\t\t\t\t\tst.slider( 'Camera Radius (KM)', min_value=1, max_value=100,
\t\t\t\t\t\tstep=1, key='live_world_camera_radius_km' )
\t\t\t\twith camera_c2:
\t\t\t\t\tst.slider( 'Camera Limit', min_value=50, max_value=2000,
\t\t\t\t\t\tstep=50, key='live_world_camera_limit' )
\t\t\t\tst.caption( 'Public camera locations and webcam tags are retrieved from OpenStreetMap via Overpass.' )
\t\t\tfor label in LIVE_WORLD_PENDING_LAYERS.values( ):
\t\t\t\tst.checkbox( label, value=False, disabled=True )
"""
world = replace_once( world, old_additional, new_additional, 'camera sidebar controls' )

camera_function = r"""

def fetch_live_cameras( latitude: float, longitude: float ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Retrieve public CCTV, surveillance-camera, and webcam features from OpenStreetMap
		Overpass and normalize them into the Live World GeoEntity contract.

		Parameters:
		-----------
		latitude (float): Current Iyr/global latitude.
		longitude (float): Current Iyr/global longitude.

		Returns:
		--------
		pd.DataFrame: Normalized camera entities.

	'''
	initialize_live_world_state( )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	categories = list( st.session_state.get( 'live_world_camera_categories', [ ] ) or [ ] )
	if not categories:
		return entities_to_dataframe( [ ] )
	radius_km = float( st.session_state[ 'live_world_camera_radius_km' ] )
	limit = int( st.session_state[ 'live_world_camera_limit' ] )
	service = OverpassCameras( timeout=30 )
	result = service.fetch_cameras( latitude, longitude, radius_km, categories, limit )
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
		category = str( element.get( 'CameraCategory', '' ) or 'Camera' )
		osm_type = str( element.get( 'type', '' ) or '' )
		osm_id = str( element.get( 'id', '' ) or '' )
		entity_id = f'OSM-CAMERA-{osm_type}-{osm_id}'
		web_url = str( tags.get( 'webcam', '' ) or tags.get( 'contact:webcam', '' )
			or tags.get( 'website', '' ) or tags.get( 'url', '' ) or '' )
		name = str( tags.get( 'name', '' ) or tags.get( 'operator', '' )
			or f'{category} {osm_id}' )
		metadata = {
			'Category': category,
			'OSM Type': osm_type,
			'OSM ID': osm_id,
			'Operator': tags.get( 'operator', '' ),
			'Surveillance Type': tags.get( 'surveillance:type', '' ),
			'Surveillance Zone': tags.get( 'surveillance:zone', '' ),
			'Direction': tags.get( 'camera:direction', tags.get( 'direction', '' ) ),
			'Web URL': web_url,
			'Tags': tags,
		}
		entities.append( GeoEntity(
			entity_id=entity_id,
			entity_type='Camera',
			name=name,
			latitude=lat,
			longitude=lon,
			altitude=0.0,
			heading=0.0,
			speed=0.0,
			timestamp=observed_at,
			source='OpenStreetMap Overpass',
			metadata=metadata ) )

	st.session_state[ 'live_world_camera_result' ] = result
	return entities_to_dataframe( entities )
"""
world = replace_once(
    world,
    "\tst.session_state[ 'live_world_infrastructure_result' ] = result\n\treturn entities_to_dataframe( entities )\n\n\ndef get_row_value",
    "\tst.session_state[ 'live_world_infrastructure_result' ] = result\n"
    "\treturn entities_to_dataframe( entities )\n" + camera_function + "\n\ndef get_row_value",
    'camera fetch function' )

world = replace_once(
    world,
    "\tst.session_state[ 'live_world_df_infrastructure' ] = pd.DataFrame( )\n"
    "\tst.session_state[ 'live_world_aircraft_result' ] = { }",
    "\tst.session_state[ 'live_world_df_infrastructure' ] = pd.DataFrame( )\n"
    "\tst.session_state[ 'live_world_df_cameras' ] = pd.DataFrame( )\n"
    "\tst.session_state[ 'live_world_aircraft_result' ] = { }",
    'camera clear dataframe' )
world = replace_once(
    world,
    "\tst.session_state[ 'live_world_infrastructure_result' ] = { }\n"
    "\tst.session_state[ 'live_world_tracking_history' ] = [ ]",
    "\tst.session_state[ 'live_world_infrastructure_result' ] = { }\n"
    "\tst.session_state[ 'live_world_camera_result' ] = { }\n"
    "\tst.session_state[ 'live_world_tracking_history' ] = [ ]",
    'camera clear result' )

world = replace_once(
    world,
    "\t\tif st.session_state[ 'live_world_infrastructure' ]:\n"
    "\t\t\tdf_infrastructure = fetch_live_infrastructure( latitude, longitude )\n"
    "\t\t\tst.session_state[ 'live_world_df_infrastructure' ] = df_infrastructure\n"
    "\t\t\tif not df_infrastructure.empty:\n"
    "\t\t\t\tframes.append( df_infrastructure )\n"
    "\t\telse:\n"
    "\t\t\tst.session_state[ 'live_world_df_infrastructure' ] = pd.DataFrame( )\n\n"
    "\t\tdf_entities = pd.concat( frames,",
    "\t\tif st.session_state[ 'live_world_infrastructure' ]:\n"
    "\t\t\tdf_infrastructure = fetch_live_infrastructure( latitude, longitude )\n"
    "\t\t\tst.session_state[ 'live_world_df_infrastructure' ] = df_infrastructure\n"
    "\t\t\tif not df_infrastructure.empty:\n"
    "\t\t\t\tframes.append( df_infrastructure )\n"
    "\t\telse:\n"
    "\t\t\tst.session_state[ 'live_world_df_infrastructure' ] = pd.DataFrame( )\n\n"
    "\t\tif st.session_state[ 'live_world_cameras' ]:\n"
    "\t\t\tdf_cameras = fetch_live_cameras( latitude, longitude )\n"
    "\t\t\tst.session_state[ 'live_world_df_cameras' ] = df_cameras\n"
    "\t\t\tif not df_cameras.empty:\n"
    "\t\t\t\tframes.append( df_cameras )\n"
    "\t\telse:\n"
    "\t\t\tst.session_state[ 'live_world_df_cameras' ] = pd.DataFrame( )\n\n"
    "\t\tdf_entities = pd.concat( frames,",
    'camera refresh path' )

world = replace_once(
    world,
    "\tevent_c1, event_c2, event_c3 = st.columns( 3, border=True )\n"
    "\tevent_c1.metric( 'Earthquakes',\n"
    "\t\tf'{int( (df_map[ \"EntityType\" ] == \"Earthquake\").sum( ) ):,}' )\n"
    "\tevent_c2.metric( 'Fires', f'{int( (df_map[ \"EntityType\" ] == \"Fire\").sum( ) ):,}' )\n"
    "\tevent_c3.metric( 'Infrastructure',\n"
    "\t\tf'{int( (df_map[ \"EntityType\" ] == \"Infrastructure\").sum( ) ):,}' )",
    "\tevent_c1, event_c2, event_c3, event_c4 = st.columns( 4, border=True )\n"
    "\tevent_c1.metric( 'Earthquakes',\n"
    "\t\tf'{int( (df_map[ \"EntityType\" ] == \"Earthquake\").sum( ) ):,}' )\n"
    "\tevent_c2.metric( 'Fires', f'{int( (df_map[ \"EntityType\" ] == \"Fire\").sum( ) ):,}' )\n"
    "\tevent_c3.metric( 'Infrastructure',\n"
    "\t\tf'{int( (df_map[ \"EntityType\" ] == \"Infrastructure\").sum( ) ):,}' )\n"
    "\tevent_c4.metric( 'Cameras', f'{int( (df_map[ \"EntityType\" ] == \"Camera\").sum( ) ):,}' )",
    'camera metric' )
world = replace_once(
    world,
    "\tdf_infrastructure = df_map[ df_map[ 'EntityType' ] == 'Infrastructure' ].copy( )\n\n",
    "\tdf_infrastructure = df_map[ df_map[ 'EntityType' ] == 'Infrastructure' ].copy( )\n"
    "\tdf_cameras = df_map[ df_map[ 'EntityType' ] == 'Camera' ].copy( )\n\n",
    'camera map dataframe' )
world = replace_once(
    world,
    "\tif not df_infrastructure.empty:\n"
    "\t\tdf_infrastructure[ 'Radius' ] = 8500.0 * point_scale\n"
    "\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_infrastructure,\n"
    "\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',\n"
    "\t\t\tget_fill_color=[ 255, 165, 60, 190 ], get_line_color=[ 255, 225, 180, 255 ],\n"
    "\t\t\tline_width_min_pixels=1, stroked=True, pickable=True ) )\n\n"
    "\tdf_tracking = get_live_world_tracking_frame( )",
    "\tif not df_infrastructure.empty:\n"
    "\t\tdf_infrastructure[ 'Radius' ] = 8500.0 * point_scale\n"
    "\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_infrastructure,\n"
    "\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',\n"
    "\t\t\tget_fill_color=[ 255, 165, 60, 190 ], get_line_color=[ 255, 225, 180, 255 ],\n"
    "\t\t\tline_width_min_pixels=1, stroked=True, pickable=True ) )\n\n"
    "\tif not df_cameras.empty:\n"
    "\t\tdf_cameras[ 'Radius' ] = 7500.0 * point_scale\n"
    "\t\tlayers.append( pdk.Layer( 'ScatterplotLayer', data=df_cameras,\n"
    "\t\t\tget_position='[Longitude, Latitude]', get_radius='Radius',\n"
    "\t\t\tget_fill_color=[ 70, 210, 255, 205 ], get_line_color=[ 220, 250, 255, 255 ],\n"
    "\t\t\tline_width_min_pixels=1, radius_min_pixels=5, radius_max_pixels=28,\n"
    "\t\t\tstroked=True, pickable=True ) )\n\n"
    "\tdf_tracking = get_live_world_tracking_frame( )",
    'camera map layer' )

world = replace_once(
    world,
    "\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, infrastructure_tab, tracking_tab, measurements_tab, analysis_tab, geofence_tab, history_tab = st.tabs(\n"
    "\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',\n"
    "\t\t\t'📈 Earthquakes', '🔥 Fires', '📡 Infrastructure', '🎯 Tracking', '📏 Measurements',\n"
    "\t\t\t'🧭 Analysis', '🛡️ Geofence', '🕓 Historical Replay' ] )",
    "\tentities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, infrastructure_tab, cameras_tab, tracking_tab, measurements_tab, analysis_tab, geofence_tab, history_tab = st.tabs(\n"
    "\t\t[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',\n"
    "\t\t\t'📈 Earthquakes', '🔥 Fires', '📡 Infrastructure', '📷 Cameras', '🎯 Tracking',\n"
    "\t\t\t'📏 Measurements', '🧭 Analysis', '🛡️ Geofence', '🕓 Historical Replay' ] )",
    'camera tab registry' )

camera_tab = """
\twith cameras_tab:
\t\tif df_cameras.empty:
\t\t\tst.info( 'No public CCTV or webcam features are loaded.' )
\t\telse:
\t\t\tcategories = df_cameras[ 'Metadata' ].map(
\t\t\t\tlambda value: value.get( 'Category', '' ) if isinstance( value, dict ) else '' )
\t\t\tweb_urls = df_cameras[ 'Metadata' ].map(
\t\t\t\tlambda value: value.get( 'Web URL', '' ) if isinstance( value, dict ) else '' )
\t\t\tcamera_c1, camera_c2, camera_c3 = st.columns( 3, border=True )
\t\t\tcamera_c1.metric( 'Cameras', f'{len( df_cameras.index ):,}' )
\t\t\tcamera_c2.metric( 'Categories', f'{categories.nunique( ):,}' )
\t\t\tcamera_c3.metric( 'Web URLs', f'{int( web_urls.astype( bool ).sum( ) ):,}' )
\t\t\tdf_display = df_cameras.copy( )
\t\t\tdf_display[ 'Category' ] = categories
\t\t\tdf_display[ 'WebURL' ] = web_urls
\t\t\tst.data_editor( df_display[ [ 'EntityId', 'Category', 'Name', 'Latitude', 'Longitude',
\t\t\t\t'WebURL', 'Source', 'Metadata' ] ], key='live_world_camera_table',
\t\t\t\tuse_container_width=True, disabled=True, hide_index=True )

"""
world = replace_once(
    world,
    "\twith tracking_tab:\n",
    camera_tab + "\twith tracking_tab:\n",
    'camera tab content' )

world = world.replace(
    'live aircraft, military aircraft, satellite, vessel, earthquake, and active-fire retrieval,',
    'live aircraft, military aircraft, satellite, vessel, earthquake, active-fire, infrastructure, and public-camera retrieval,' )
write_text( world_path, world )


# ==============================================================================
# FINAL MODULE-REFERENCE CHECKS
# ==============================================================================
for path in [ Path( 'world.py' ), Path( 'history.py' ), Path( 'sources.py' ), Path( 'tools.py' ) ]:
    if not path.exists( ):
        raise RuntimeError( f'Renamed module is missing: {path}' )

for path in [ Path( 'app.py' ), Path( 'world.py' ), Path( 'history.py' ), Path( 'sources.py' ), Path( 'tools.py' ) ]:
    text = path.read_text( encoding='utf-8' )
    for old_name in [ 'from world import ', 'from history import ',
            'from sources import ', 'from tools import ' ]:
        if old_name in text:
            raise RuntimeError( f'Stale module import in {path}: {old_name}' )

print( 'CCTV/Web Cameras and module renames implemented.' )
