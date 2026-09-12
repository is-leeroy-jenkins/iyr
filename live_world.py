'''
******************************************************************************************
 Assembly:                iyr
 Filename:                live_world.py
 Author:                  Terry D. Eppler / Assistant
 Created:                 09-12-2026

 Last Modified By:        Terry D. Eppler / Assistant
 Last Modified On:        09-12-2026
******************************************************************************************

Purpose:
    Live World Data functionality inspired by God's Eye View while preserving Iyr's
    existing GIS modes and execution paths. The module provides isolated sidebar state,
    live aircraft, satellite, earthquake, and active-fire retrieval, normalized geospatial
    entities, operational PyDeck rendering, entity tracking and trails, refresh controls,
    filtering, and source-data inspection.
******************************************************************************************
'''

from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import pandas as pd
import pydeck as pdk
import streamlit as st

from fetchers import Firms, USGSEarthquakes
from live_world_sources import CelesTrakLive, OpenSkyLive


LIVE_WORLD_LAYERS: Dict[ str, str ] = {
	'aircraft': '✈️ Aircraft (Live)',
	'satellites': '🛰️ Satellites',
	'earthquakes': '📈 Earthquakes',
	'fires': '🔥 Fires (Wildfires)',
	'tracking': '🎯 Tracking & Trails',
}

LIVE_WORLD_PENDING_LAYERS: Dict[ str, str ] = {
	'military_aircraft': '🛩️ Military Aircraft',
	'vessels': '🚢 Vessels & Ships',
	'cameras': '📷 CCTV / Web Cameras',
	'infrastructure': '📡 Infrastructure (Airports, Ports, etc.)',
	'measurements': '📏 Measurements & Annotations',
	'map_layers': '🗺️ Additional Map Layers',
}

AI_ADVANCED_TOOLS: Dict[ str, str ] = {
	'cross_layer_analysis': '🧭 Cross-Layer Analysis',
	'geofencing': '🛡️ Geofencing',
	'agent_tools': '🤖 Agent Tools',
	'historical_replay': '🕓 Historical Replay',
}


@dataclass
class GeoEntity:
	'''

		Purpose:
		--------
		Represent one normalized geospatial object or event displayed by Live World Data.

		Attributes:
		-----------
		entity_id (str): Stable source identifier.
		entity_type (str): Logical entity category.
		name (str): Human-readable label.
		latitude (float): Latitude in decimal degrees.
		longitude (float): Longitude in decimal degrees.
		altitude (float): Altitude or depth value when available.
		heading (float): Heading in degrees when available.
		speed (float): Speed when available.
		timestamp (str): Source timestamp.
		source (str): Source system name.
		metadata (Dict[str, Any]): Source-specific attributes.

	'''
	entity_id: str
	entity_type: str
	name: str
	latitude: float
	longitude: float
	altitude: float
	heading: float
	speed: float
	timestamp: str
	source: str
	metadata: Dict[ str, Any ]


def throw_if( name: str, value: object ) -> None:
	'''

		Purpose:
		--------
		Validate that a required value is not empty.

		Parameters:
		-----------
		name (str): Name of the argument being validated.
		value (object): Value to validate.

		Returns:
		--------
		None

	'''
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be None.' )

	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty.' )


def initialize_live_world_state( ) -> None:
	'''

		Purpose:
		--------
		Initialize isolated Live World Data state without modifying Iyr's existing mode state.

		Returns:
		--------
		None

	'''
	defaults: Dict[ str, object ] = {
		'live_world_enabled': False,
		'live_world_aircraft': False,
		'live_world_aircraft_radius': 2.0,
		'live_world_aircraft_airborne_only': True,
		'live_world_satellites': False,
		'live_world_satellite_group': 'stations',
		'live_world_satellite_limit': 100,
		'live_world_earthquakes': False,
		'live_world_earthquake_feed': 'all_day.geojson',
		'live_world_earthquake_min_magnitude': 1.0,
		'live_world_fires': False,
		'live_world_firms_source': 'VIIRS_SNPP_NRT',
		'live_world_firms_day_range': 1,
		'live_world_firms_area_mode': 'Local Bounding Box',
		'live_world_tracking': False,
		'live_world_tracking_entity': '',
		'live_world_tracking_active_entity': '',
		'live_world_tracking_follow': True,
		'live_world_tracking_max_points': 100,
		'live_world_tracking_history': [ ],
		'live_world_refresh_requested': False,
		'live_world_last_refresh': '',
		'live_world_last_error': '',
		'live_world_df_entities': pd.DataFrame( ),
		'live_world_df_aircraft': pd.DataFrame( ),
		'live_world_df_satellites': pd.DataFrame( ),
		'live_world_df_earthquakes': pd.DataFrame( ),
		'live_world_df_fires': pd.DataFrame( ),
		'live_world_aircraft_result': { },
		'live_world_satellite_result': [ ],
		'live_world_earthquake_result': { },
		'live_world_firms_result': { },
		'live_world_map_style': 'Carto Dark Matter',
		'live_world_zoom': 4,
		'live_world_point_scale': 1.0,
	}

	for key, value in defaults.items( ):
		if key not in st.session_state:
			st.session_state[ key ] = value


def get_live_world_layers( ) -> Dict[ str, bool ]:
	'''

		Purpose:
		--------
		Return the enabled state of every implemented Live World Data layer.

		Returns:
		--------
		Dict[str, bool]: Enabled state keyed by layer identifier.

	'''
	initialize_live_world_state( )
	return {
		key: bool( st.session_state.get( f'live_world_{key}', False ) )
		for key in LIVE_WORLD_LAYERS
	}


def render_live_world_sidebar( ) -> None:
	'''

		Purpose:
		--------
		Render operational Live World Data controls in an isolated sidebar expander below
		Iyr's existing Mode expander.

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )

	with st.expander( '🌐 Live World Data (God\'s Eye View)', expanded=False ):
		st.checkbox( 'Enable Live World Map', key='live_world_enabled' )
		st.divider( )
		st.caption( 'Live Layers' )

		st.checkbox( LIVE_WORLD_LAYERS[ 'aircraft' ], key='live_world_aircraft' )
		if st.session_state[ 'live_world_aircraft' ]:
			st.slider( 'Aircraft Radius (Degrees)', min_value=0.25, max_value=10.0,
				step=0.25, key='live_world_aircraft_radius' )
			st.checkbox( 'Airborne Only', key='live_world_aircraft_airborne_only' )
			st.caption( 'OpenSky API Client credentials are used when configured.' )

		st.checkbox( LIVE_WORLD_LAYERS[ 'satellites' ], key='live_world_satellites' )
		if st.session_state[ 'live_world_satellites' ]:
			st.selectbox( 'Satellite Group',
				options=[ 'stations', 'visual', 'weather', 'gps-ops', 'active' ],
				key='live_world_satellite_group' )
			st.slider( 'Satellite Limit', min_value=10, max_value=500, step=10,
				key='live_world_satellite_limit' )

		st.checkbox( LIVE_WORLD_LAYERS[ 'earthquakes' ], key='live_world_earthquakes' )
		if st.session_state[ 'live_world_earthquakes' ]:
			st.selectbox(
				'Earthquake Feed',
				options=[
					'all_hour.geojson', 'all_day.geojson', 'all_week.geojson',
					'2.5_day.geojson', '2.5_week.geojson', '4.5_day.geojson',
					'4.5_week.geojson', 'significant_day.geojson',
					'significant_week.geojson' ],
				key='live_world_earthquake_feed' )
			st.slider( 'Minimum Magnitude', min_value=0.0, max_value=10.0,
				step=0.1, key='live_world_earthquake_min_magnitude' )

		st.checkbox( LIVE_WORLD_LAYERS[ 'fires' ], key='live_world_fires' )
		if st.session_state[ 'live_world_fires' ]:
			st.selectbox( 'FIRMS Source',
				options=[ 'VIIRS_SNPP_NRT', 'VIIRS_NOAA20_NRT', 'VIIRS_NOAA21_NRT',
					'MODIS_NRT', 'LANDSAT_NRT' ],
				key='live_world_firms_source' )
			st.slider( 'Fire Day Range', min_value=1, max_value=5, step=1,
				key='live_world_firms_day_range' )
			st.selectbox( 'Fire Area', options=[ 'Local Bounding Box', 'World' ],
				key='live_world_firms_area_mode' )

		st.checkbox( LIVE_WORLD_LAYERS[ 'tracking' ], key='live_world_tracking' )
		if st.session_state[ 'live_world_tracking' ]:
			tracking_options = get_live_world_tracking_options( )
			if tracking_options:
				tracking_keys = list( tracking_options.keys( ) )
				if st.session_state[ 'live_world_tracking_entity' ] not in tracking_keys:
					st.session_state[ 'live_world_tracking_entity' ] = tracking_keys[ 0 ]
				st.selectbox( 'Tracked Entity', options=tracking_keys,
					format_func=lambda value: tracking_options[ value ],
					key='live_world_tracking_entity' )
			else:
				st.info( 'Refresh Aircraft or Satellites before selecting a tracked entity.' )
			st.checkbox( 'Follow Tracked Entity', key='live_world_tracking_follow' )
			st.slider( 'Trail Points', min_value=10, max_value=500, step=10,
				key='live_world_tracking_max_points' )
			if st.button( 'Clear Trail', icon='🧹', key='live_world_tracking_clear',
					width='stretch' ):
				clear_live_world_tracking( )

		st.divider( )
		refresh_c1, clear_c2 = st.columns( 2 )
		with refresh_c1:
			if st.button( 'Refresh', icon='🔄', key='live_world_refresh', width='stretch' ):
				st.session_state[ 'live_world_refresh_requested' ] = True

		with clear_c2:
			if st.button( 'Clear', icon='🧹', key='live_world_clear', width='stretch' ):
				clear_live_world_data( )

		with st.expander( 'Additional Layers', expanded=False ):
			st.caption( 'Layers activate as their provider implementations are completed.' )
			for label in LIVE_WORLD_PENDING_LAYERS.values( ):
				st.checkbox( label, value=False, disabled=True )

		with st.expander( 'AI & Advanced Tools', expanded=False ):
			st.caption( 'Advanced tools activate after their dependent live layers are operational.' )
			for label in AI_ADVANCED_TOOLS.values( ):
				st.checkbox( label, value=False, disabled=True )


def clear_live_world_data( ) -> None:
	'''

		Purpose:
		--------
		Clear retrieved Live World Data while preserving layer selections and map controls.

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )
	st.session_state[ 'live_world_df_entities' ] = pd.DataFrame( )
	st.session_state[ 'live_world_df_aircraft' ] = pd.DataFrame( )
	st.session_state[ 'live_world_df_satellites' ] = pd.DataFrame( )
	st.session_state[ 'live_world_df_earthquakes' ] = pd.DataFrame( )
	st.session_state[ 'live_world_df_fires' ] = pd.DataFrame( )
	st.session_state[ 'live_world_aircraft_result' ] = { }
	st.session_state[ 'live_world_satellite_result' ] = [ ]
	st.session_state[ 'live_world_earthquake_result' ] = { }
	st.session_state[ 'live_world_firms_result' ] = { }
	st.session_state[ 'live_world_tracking_history' ] = [ ]
	st.session_state[ 'live_world_tracking_active_entity' ] = ''
	st.session_state[ 'live_world_last_refresh' ] = ''
	st.session_state[ 'live_world_last_error' ] = ''
	st.session_state[ 'live_world_refresh_requested' ] = False


def create_live_world_bounding_box( latitude: float, longitude: float,
		delta: float=2.0 ) -> str:
	'''

		Purpose:
		--------
		Create a NASA FIRMS area-coordinate string centered on the supplied location.

		Parameters:
		-----------
		latitude (float): Center latitude.
		longitude (float): Center longitude.
		delta (float): Decimal-degree offset used to create the bounding box.

		Returns:
		--------
		str: FIRMS west,south,east,north area-coordinate string.

	'''
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	west = max( -180.0, float( longitude ) - float( delta ) )
	south = max( -90.0, float( latitude ) - float( delta ) )
	east = min( 180.0, float( longitude ) + float( delta ) )
	north = min( 90.0, float( latitude ) + float( delta ) )
	return f'{west:.6f},{south:.6f},{east:.6f},{north:.6f}'


def fetch_live_aircraft( latitude: float, longitude: float ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Retrieve current OpenSky aircraft state vectors around the Iyr/global location and
		normalize positioned aircraft for Live World rendering.

		Parameters:
		-----------
		latitude (float): Geographic center latitude.
		longitude (float): Geographic center longitude.

		Returns:
		--------
		pd.DataFrame: Normalized aircraft entities.

	'''
	initialize_live_world_state( )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	client_id = str( st.session_state.get( 'opensky_api_client_id', '' ) or '' )
	client_secret = str( st.session_state.get( 'opensky_api_credentials', '' ) or '' )
	radius = float( st.session_state[ 'live_world_aircraft_radius' ] )
	airborne_only = bool( st.session_state[ 'live_world_aircraft_airborne_only' ] )
	service = OpenSkyLive( client_id=client_id, client_secret=client_secret, timeout=20 )
	result = service.fetch_states( latitude=latitude, longitude=longitude,
		radius_degrees=radius ) or { }
	states = result.get( 'states', [ ] ) or [ ]
	entities: List[ GeoEntity ] = [ ]

	for state in states:
		if not isinstance( state, list ) or len( state ) < 17:
			continue

		icao24 = str( state[ 0 ] or '' ).strip( )
		callsign = str( state[ 1 ] or '' ).strip( )
		longitude_value = state[ 5 ]
		latitude_value = state[ 6 ]
		if latitude_value is None or longitude_value is None:
			continue

		on_ground = bool( state[ 8 ] )
		if airborne_only and on_ground:
			continue

		try:
			lat = float( latitude_value )
			lon = float( longitude_value )
		except ( TypeError, ValueError ):
			continue

		geo_altitude = state[ 13 ] if len( state ) > 13 else None
		baro_altitude = state[ 7 ] if len( state ) > 7 else None
		altitude = geo_altitude if geo_altitude is not None else baro_altitude
		try:
			altitude_value = float( altitude ) if altitude is not None else 0.0
		except ( TypeError, ValueError ):
			altitude_value = 0.0

		velocity = state[ 9 ] if len( state ) > 9 else None
		heading = state[ 10 ] if len( state ) > 10 else None
		try:
			velocity_value = float( velocity ) if velocity is not None else 0.0
		except ( TypeError, ValueError ):
			velocity_value = 0.0
		try:
			heading_value = float( heading ) if heading is not None else 0.0
		except ( TypeError, ValueError ):
			heading_value = 0.0

		metadata = {
			'ICAO24': icao24,
			'Callsign': callsign,
			'Origin Country': state[ 2 ],
			'Time Position': state[ 3 ],
			'Last Contact': state[ 4 ],
			'Barometric Altitude': baro_altitude,
			'Geometric Altitude': geo_altitude,
			'Vertical Rate': state[ 11 ] if len( state ) > 11 else None,
			'On Ground': on_ground,
			'Squawk': state[ 14 ] if len( state ) > 14 else None,
			'SPI': state[ 15 ] if len( state ) > 15 else None,
			'Position Source': state[ 16 ] if len( state ) > 16 else None,
			'Category': state[ 17 ] if len( state ) > 17 else None,
		}
		entities.append( GeoEntity(
			entity_id=icao24 or f'OPENSKY-{len( entities ) + 1}',
			entity_type='Aircraft',
			name=callsign or icao24,
			latitude=lat,
			longitude=lon,
			altitude=altitude_value,
			heading=heading_value,
			speed=velocity_value,
			timestamp=str( state[ 4 ] or '' ),
			source='OpenSky Network',
			metadata=metadata ) )

	st.session_state[ 'live_world_aircraft_result' ] = result
	return entities_to_dataframe( entities )


def fetch_live_satellites( ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Retrieve current CelesTrak OMM records, propagate each orbit to the current UTC time,
		and normalize successfully propagated satellites for Live World rendering.

		Returns:
		--------
		pd.DataFrame: Normalized satellite entities.

	'''
	initialize_live_world_state( )
	group = str( st.session_state[ 'live_world_satellite_group' ] )
	limit = int( st.session_state[ 'live_world_satellite_limit' ] )
	service = CelesTrakLive( timeout=20 )
	records = service.fetch_group( group=group, limit=limit )
	when = dt.datetime.now( dt.timezone.utc )
	entities: List[ GeoEntity ] = [ ]

	for record in records:
		try:
			position = service.propagate( record=record, when=when )
		except Exception:
			continue

		catalog_number = str( position.get( 'CatalogNumber', '' ) or '' )
		name = str( position.get( 'Name', '' ) or catalog_number )
		metadata = {
			'Catalog Number': catalog_number,
			'Object ID': position.get( 'ObjectId', '' ),
			'Epoch': position.get( 'Epoch', '' ),
			'Classification': position.get( 'Classification', '' ),
			'Group': group,
		}
		entities.append( GeoEntity(
			entity_id=catalog_number or name,
			entity_type='Satellite',
			name=name,
			latitude=float( position[ 'Latitude' ] ),
			longitude=float( position[ 'Longitude' ] ),
			altitude=float( position[ 'Altitude' ] ),
			heading=0.0,
			speed=float( position[ 'Velocity' ] ),
			timestamp=when.isoformat( ),
			source='CelesTrak',
			metadata=metadata ) )

	st.session_state[ 'live_world_satellite_result' ] = records
	return entities_to_dataframe( entities )


def fetch_live_earthquakes( ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Retrieve the selected USGS earthquake feed through Iyr's existing provider and
		normalize matching events for Live World rendering.

		Returns:
		--------
		pd.DataFrame: Normalized earthquake entities.

	'''
	initialize_live_world_state( )
	feed = str( st.session_state[ 'live_world_earthquake_feed' ] )
	min_magnitude = float( st.session_state[ 'live_world_earthquake_min_magnitude' ] )
	service = USGSEarthquakes( )
	result = service.fetch( mode='feed', feed=feed, time=20 ) or { }
	rows = result.get( 'rows', [ ] ) or [ ]
	entities: List[ GeoEntity ] = [ ]

	for index, row in enumerate( rows ):
		latitude = row.get( 'Latitude', None )
		longitude = row.get( 'Longitude', None )
		magnitude = row.get( 'Magnitude', None )
		if latitude is None or longitude is None:
			continue

		try:
			magnitude_value = float( magnitude ) if magnitude is not None else 0.0
			latitude_value = float( latitude )
			longitude_value = float( longitude )
		except ( TypeError, ValueError ):
			continue

		if magnitude_value < min_magnitude:
			continue

		depth = row.get( 'Depth (km)', 0.0 )
		try:
			depth_value = float( depth ) if depth is not None else 0.0
		except ( TypeError, ValueError ):
			depth_value = 0.0

		entity_id = str( row.get( 'Id', '' ) or f'USGS-{index + 1}' )
		metadata = {
			'Magnitude': magnitude_value,
			'Depth (km)': depth_value,
			'Alert': row.get( 'Alert', '' ),
			'Status': row.get( 'Status', '' ),
			'Tsunami': row.get( 'Tsunami', None ),
			'Felt Reports': row.get( 'Felt Reports', None ),
			'Event Type': row.get( 'Event Type', '' ),
			'URL': row.get( 'URL', '' ),
		}
		entities.append( GeoEntity(
			entity_id=entity_id,
			entity_type='Earthquake',
			name=str( row.get( 'Place', '' ) or entity_id ),
			latitude=latitude_value,
			longitude=longitude_value,
			altitude=-depth_value,
			heading=0.0,
			speed=0.0,
			timestamp=str( row.get( 'Time', '' ) or '' ),
			source='USGS Earthquakes',
			metadata=metadata ) )

	st.session_state[ 'live_world_earthquake_result' ] = result
	return entities_to_dataframe( entities )


def fetch_live_fires( latitude: float, longitude: float ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Retrieve NASA FIRMS active-fire detections through Iyr's existing Firms provider
		and normalize the response for Live World rendering.

		Parameters:
		-----------
		latitude (float): Current Iyr/global latitude used for local bounding-box mode.
		longitude (float): Current Iyr/global longitude used for local bounding-box mode.

		Returns:
		--------
		pd.DataFrame: Normalized FIRMS fire entities.

	'''
	initialize_live_world_state( )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	source = str( st.session_state[ 'live_world_firms_source' ] )
	day_range = int( st.session_state[ 'live_world_firms_day_range' ] )
	area_mode = str( st.session_state[ 'live_world_firms_area_mode' ] )
	area_coordinates = 'world' if area_mode == 'World' else create_live_world_bounding_box(
		latitude, longitude )

	service = Firms( )
	result = service.fetch_area(
		source=source,
		area_coordinates=area_coordinates,
		day_range=day_range,
		date='',
		time=20 ) or { }
	rows = result.get( 'rows', [ ] ) or [ ]
	entities: List[ GeoEntity ] = [ ]

	for index, row in enumerate( rows ):
		latitude_value = get_row_value( row, [ 'latitude', 'Latitude' ] )
		longitude_value = get_row_value( row, [ 'longitude', 'Longitude' ] )
		if latitude_value is None or longitude_value is None:
			continue

		try:
			lat = float( latitude_value )
			lon = float( longitude_value )
		except ( TypeError, ValueError ):
			continue

		acq_date = str( get_row_value( row,
			[ 'acq_date', 'Acq Date', 'Acquisition Date' ] ) or '' )
		acq_time = str( get_row_value( row,
			[ 'acq_time', 'Acq Time', 'Acquisition Time' ] ) or '' )
		satellite = str( get_row_value( row, [ 'satellite', 'Satellite' ] ) or source )
		metadata = {
			'Satellite': satellite,
			'Instrument': get_row_value( row, [ 'instrument', 'Instrument' ] ),
			'Confidence': get_row_value( row, [ 'confidence', 'Confidence' ] ),
			'FRP': get_row_value( row, [ 'frp', 'FRP' ] ),
			'Brightness': get_row_value( row,
				[ 'bright_ti4', 'brightness', 'Brightness', 'bright_t31' ] ),
			'Day/Night': get_row_value( row, [ 'daynight', 'Day/Night' ] ),
			'Version': get_row_value( row, [ 'version', 'Version' ] ),
		}
		entity_id = f'FIRMS-{source}-{acq_date}-{acq_time}-{index + 1}'
		entities.append( GeoEntity(
			entity_id=entity_id,
			entity_type='Fire',
			name=f'Active Fire - {satellite}',
			latitude=lat,
			longitude=lon,
			altitude=0.0,
			heading=0.0,
			speed=0.0,
			timestamp=f'{acq_date} {acq_time}'.strip( ),
			source='NASA FIRMS',
			metadata=metadata ) )

	st.session_state[ 'live_world_firms_result' ] = result
	return entities_to_dataframe( entities )


def get_row_value( row: Dict[ str, Any ], keys: List[ str ] ) -> object:
	'''

		Purpose:
		--------
		Read the first available value from an explicit list of known provider keys.

		Parameters:
		-----------
		row (Dict[str, Any]): Provider row.
		keys (List[str]): Ordered known keys for the same source field.

		Returns:
		--------
		object: Matching value or None.

	'''
	throw_if( 'row', row )
	throw_if( 'keys', keys )
	for key in keys:
		if key in row:
			return row[ key ]
	return None


def entities_to_dataframe( entities: List[ GeoEntity ] ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Convert normalized GeoEntity objects into the Live World DataFrame contract.

		Parameters:
		-----------
		entities (List[GeoEntity]): Normalized geospatial entities.

		Returns:
		--------
		pd.DataFrame: Live World entity records.

	'''
	columns = [ 'EntityId', 'EntityType', 'Name', 'Latitude', 'Longitude', 'Altitude',
		'Heading', 'Speed', 'Timestamp', 'Source', 'Metadata' ]
	if not entities:
		return pd.DataFrame( columns=columns )

	rows: List[ Dict[ str, object ] ] = [ ]
	for entity in entities:
		row = asdict( entity )
		rows.append( {
			'EntityId': row[ 'entity_id' ],
			'EntityType': row[ 'entity_type' ],
			'Name': row[ 'name' ],
			'Latitude': row[ 'latitude' ],
			'Longitude': row[ 'longitude' ],
			'Altitude': row[ 'altitude' ],
			'Heading': row[ 'heading' ],
			'Speed': row[ 'speed' ],
			'Timestamp': row[ 'timestamp' ],
			'Source': row[ 'source' ],
			'Metadata': row[ 'metadata' ],
		} )
	return pd.DataFrame( rows, columns=columns )



def get_live_world_tracking_options( ) -> Dict[ str, str ]:
	'''

		Purpose:
		--------
		Return selectable moving entities from the current Live World entity frame.

		Returns:
		--------
		Dict[str, str]: Tracking keys mapped to human-readable labels.

	'''
	initialize_live_world_state( )
	df_entities = st.session_state.get( 'live_world_df_entities', pd.DataFrame( ) )
	if df_entities is None or df_entities.empty:
		return { }

	required = [ 'EntityId', 'EntityType', 'Name' ]
	if any( column not in df_entities.columns for column in required ):
		return { }

	df_tracking = df_entities[ df_entities[ 'EntityType' ].isin(
		[ 'Aircraft', 'Satellite' ] ) ].copy( )
	options: Dict[ str, str ] = { }
	for _, row in df_tracking.iterrows( ):
		entity_id = str( row[ 'EntityId' ] )
		entity_type = str( row[ 'EntityType' ] )
		name = str( row[ 'Name' ] )
		tracking_key = f'{entity_type}::{entity_id}'
		options[ tracking_key ] = f'{entity_type} | {name} | {entity_id}'
	return options


def clear_live_world_tracking( ) -> None:
	'''

		Purpose:
		--------
		Clear the current tracking trail without changing the selected tracked entity.

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )
	st.session_state[ 'live_world_tracking_history' ] = [ ]
	st.session_state[ 'live_world_tracking_active_entity' ] = ''


def update_live_world_tracking( df_entities: pd.DataFrame ) -> None:
	'''

		Purpose:
		--------
		Append the selected moving entity's newest position to its in-session trail.

		Parameters:
		-----------
		df_entities (pd.DataFrame): Current normalized Live World entity records.

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )
	throw_if( 'df_entities', df_entities )
	if not st.session_state[ 'live_world_tracking' ]:
		return

	tracking_key = str( st.session_state.get( 'live_world_tracking_entity', '' ) or '' )
	if not tracking_key or '::' not in tracking_key or df_entities.empty:
		return

	entity_type, entity_id = tracking_key.split( '::', 1 )
	df_match = df_entities[
		(df_entities[ 'EntityType' ].astype( str ) == entity_type)
		& (df_entities[ 'EntityId' ].astype( str ) == entity_id) ].copy( )
	if df_match.empty:
		return

	active_entity = str( st.session_state.get(
		'live_world_tracking_active_entity', '' ) or '' )
	if active_entity != tracking_key:
		st.session_state[ 'live_world_tracking_history' ] = [ ]
		st.session_state[ 'live_world_tracking_active_entity' ] = tracking_key

	row = df_match.iloc[ 0 ]
	point = {
		'EntityKey': tracking_key,
		'EntityId': str( row[ 'EntityId' ] ),
		'EntityType': str( row[ 'EntityType' ] ),
		'Name': str( row[ 'Name' ] ),
		'Latitude': float( row[ 'Latitude' ] ),
		'Longitude': float( row[ 'Longitude' ] ),
		'Altitude': float( row[ 'Altitude' ] ),
		'Heading': float( row[ 'Heading' ] ),
		'Speed': float( row[ 'Speed' ] ),
		'Timestamp': str( row[ 'Timestamp' ] ),
		'ObservedAt': dt.datetime.now( dt.timezone.utc ).isoformat( ),
	}

	history = list( st.session_state.get( 'live_world_tracking_history', [ ] ) or [ ] )
	if history:
		previous = history[ -1 ]
		if (float( previous[ 'Latitude' ] ) == point[ 'Latitude' ]
				and float( previous[ 'Longitude' ] ) == point[ 'Longitude' ]):
			return

	history.append( point )
	max_points = int( st.session_state[ 'live_world_tracking_max_points' ] )
	st.session_state[ 'live_world_tracking_history' ] = history[ -max_points: ]


def get_live_world_tracking_frame( ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Return the current tracking trail as a DataFrame for rendering and inspection.

		Returns:
		--------
		pd.DataFrame: Ordered tracking trail points.

	'''
	initialize_live_world_state( )
	history = list( st.session_state.get( 'live_world_tracking_history', [ ] ) or [ ] )
	columns = [ 'EntityKey', 'EntityId', 'EntityType', 'Name', 'Latitude', 'Longitude',
		'Altitude', 'Heading', 'Speed', 'Timestamp', 'ObservedAt' ]
	return pd.DataFrame( history, columns=columns )

def refresh_live_world_data( latitude: float, longitude: float ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Refresh every enabled implemented Live World layer and persist the combined frame.

		Parameters:
		-----------
		latitude (float): Current Iyr/global latitude.
		longitude (float): Current Iyr/global longitude.

		Returns:
		--------
		pd.DataFrame: Combined normalized entity data.

	'''
	initialize_live_world_state( )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	frames: List[ pd.DataFrame ] = [ ]
	st.session_state[ 'live_world_last_error' ] = ''

	try:
		if st.session_state[ 'live_world_aircraft' ]:
			df_aircraft = fetch_live_aircraft( latitude, longitude )
			st.session_state[ 'live_world_df_aircraft' ] = df_aircraft
			if not df_aircraft.empty:
				frames.append( df_aircraft )
		else:
			st.session_state[ 'live_world_df_aircraft' ] = pd.DataFrame( )

		if st.session_state[ 'live_world_satellites' ]:
			df_satellites = fetch_live_satellites( )
			st.session_state[ 'live_world_df_satellites' ] = df_satellites
			if not df_satellites.empty:
				frames.append( df_satellites )
		else:
			st.session_state[ 'live_world_df_satellites' ] = pd.DataFrame( )

		if st.session_state[ 'live_world_earthquakes' ]:
			df_earthquakes = fetch_live_earthquakes( )
			st.session_state[ 'live_world_df_earthquakes' ] = df_earthquakes
			if not df_earthquakes.empty:
				frames.append( df_earthquakes )
		else:
			st.session_state[ 'live_world_df_earthquakes' ] = pd.DataFrame( )

		if st.session_state[ 'live_world_fires' ]:
			df_fires = fetch_live_fires( latitude, longitude )
			st.session_state[ 'live_world_df_fires' ] = df_fires
			if not df_fires.empty:
				frames.append( df_fires )
		else:
			st.session_state[ 'live_world_df_fires' ] = pd.DataFrame( )

		df_entities = pd.concat( frames,
			ignore_index=True ) if frames else entities_to_dataframe( [ ] )
		st.session_state[ 'live_world_df_entities' ] = df_entities
		update_live_world_tracking( df_entities )
		st.session_state[ 'live_world_last_refresh' ] = dt.datetime.now( ).strftime(
			'%Y-%m-%d %H:%M:%S' )
		st.session_state[ 'live_world_refresh_requested' ] = False
		return df_entities

	except Exception as ex:
		st.session_state[ 'live_world_last_error' ] = str( ex )
		st.session_state[ 'live_world_refresh_requested' ] = False
		raise


def render_live_world_map( latitude: float, longitude: float ) -> None:
	'''

		Purpose:
		--------
		Render normalized Live World entities on an operational PyDeck map with metrics,
		map controls, source tooltips, and source-data tabs.

		Parameters:
		-----------
		latitude (float): Current Iyr/global latitude used for initial map centering.
		longitude (float): Current Iyr/global longitude used for initial map centering.

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	if not st.session_state[ 'live_world_enabled' ]:
		return

	st.divider( )
	st.subheader( '🌐 Live World Data' )
	if not any( get_live_world_layers( ).values( ) ):
		st.info( 'Select at least one implemented Live World layer in the sidebar.' )
		return

	if st.session_state[ 'live_world_refresh_requested' ]:
		try:
			with st.spinner( 'Refreshing Live World Data...' ):
				refresh_live_world_data( latitude, longitude )
		except Exception as ex:
			st.error( f'Live World refresh failed: {ex}' )

	df_entities = st.session_state.get( 'live_world_df_entities', pd.DataFrame( ) )
	if df_entities is None or df_entities.empty:
		st.info( 'No Live World data has been loaded. Select Refresh in the sidebar.' )
		return

	df_map = df_entities.copy( )
	df_map[ 'MetadataText' ] = df_map[ 'Metadata' ].map(
		lambda value: json.dumps( value, default=str ) if isinstance( value, dict ) else str( value ) )
	df_map[ 'Latitude' ] = pd.to_numeric( df_map[ 'Latitude' ], errors='coerce' )
	df_map[ 'Longitude' ] = pd.to_numeric( df_map[ 'Longitude' ], errors='coerce' )
	df_map = df_map.dropna( subset=[ 'Latitude', 'Longitude' ] )
	if df_map.empty:
		st.info( 'Live World data does not contain usable map coordinates.' )
		return

	last_refresh = str( st.session_state.get( 'live_world_last_refresh', '' ) or 'Not refreshed' )
	metric_c1, metric_c2, metric_c3, metric_c4, metric_c5 = st.columns( 5, border=True )
	metric_c1.metric( 'Entities', f'{len( df_map ):,}' )
	metric_c2.metric( 'Aircraft',
		f'{int( (df_map[ "EntityType" ] == "Aircraft").sum( ) ):,}' )
	metric_c3.metric( 'Satellites',
		f'{int( (df_map[ "EntityType" ] == "Satellite").sum( ) ):,}' )
	metric_c4.metric( 'Earthquakes',
		f'{int( (df_map[ "EntityType" ] == "Earthquake").sum( ) ):,}' )
	metric_c5.metric( 'Fires', f'{int( (df_map[ "EntityType" ] == "Fire").sum( ) ):,}' )
	st.caption( f'Last refresh: {last_refresh}' )

	map_style_options = {
		'Carto Dark Matter': 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
		'Carto Positron': 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
		'Carto Voyager': 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
		'Dark': 'dark',
		'Light': 'light',
		'Road': 'road',
		'Satellite': 'satellite',
	}
	control_c1, control_c2, control_c3 = st.columns( 3, border=True )
	with control_c1:
		st.selectbox( 'Map Style', options=list( map_style_options.keys( ) ),
			key='live_world_map_style' )
	with control_c2:
		st.slider( 'Zoom', min_value=0, max_value=18, key='live_world_zoom' )
	with control_c3:
		st.slider( 'Point Scale', min_value=0.5, max_value=3.0, step=0.25,
			key='live_world_point_scale' )

	layers: List[ pdk.Layer ] = [ ]
	point_scale = float( st.session_state[ 'live_world_point_scale' ] )
	df_aircraft = df_map[ df_map[ 'EntityType' ] == 'Aircraft' ].copy( )
	df_satellites = df_map[ df_map[ 'EntityType' ] == 'Satellite' ].copy( )
	df_earthquakes = df_map[ df_map[ 'EntityType' ] == 'Earthquake' ].copy( )
	df_fires = df_map[ df_map[ 'EntityType' ] == 'Fire' ].copy( )

	if not df_aircraft.empty:
		df_aircraft[ 'Radius' ] = 7000.0 * point_scale
		layers.append( pdk.Layer(
			'ScatterplotLayer', data=df_aircraft,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 0, 170, 255, 220 ], get_line_color=[ 220, 245, 255, 240 ],
			line_width_min_pixels=1, radius_min_pixels=5, radius_max_pixels=26,
			filled=True, stroked=True, pickable=True ) )

	if not df_satellites.empty:
		df_satellites[ 'Radius' ] = 8500.0 * point_scale
		layers.append( pdk.Layer(
			'ScatterplotLayer', data=df_satellites,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 180, 120, 255, 220 ], get_line_color=[ 245, 235, 255, 240 ],
			line_width_min_pixels=1, radius_min_pixels=5, radius_max_pixels=28,
			filled=True, stroked=True, pickable=True ) )

	if not df_earthquakes.empty:
		df_earthquakes[ 'Magnitude' ] = df_earthquakes[ 'Metadata' ].map(
			lambda value: get_metadata_number( value, 'Magnitude', 0.0 ) )
		df_earthquakes[ 'Radius' ] = df_earthquakes[ 'Magnitude' ].map(
			lambda value: max( 4000.0, (float( value ) + 1.0) * 9000.0 * point_scale ) )
		layers.append( pdk.Layer(
			'ScatterplotLayer', data=df_earthquakes,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 255, 196, 0, 185 ], get_line_color=[ 255, 255, 255, 210 ],
			line_width_min_pixels=1, radius_min_pixels=4, radius_max_pixels=40,
			filled=True, stroked=True, pickable=True ) )

	if not df_fires.empty:
		df_fires[ 'Radius' ] = 9000.0 * point_scale
		layers.append( pdk.Layer(
			'ScatterplotLayer', data=df_fires,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 255, 70, 0, 210 ], get_line_color=[ 255, 225, 180, 230 ],
			line_width_min_pixels=1, radius_min_pixels=4, radius_max_pixels=28,
			filled=True, stroked=True, pickable=True ) )

	df_tracking = get_live_world_tracking_frame( )
	if st.session_state[ 'live_world_tracking' ] and not df_tracking.empty:
		if len( df_tracking ) > 1:
			path_data = [ {
				'Path': df_tracking[ [ 'Longitude', 'Latitude' ] ].values.tolist( ) } ]
			layers.append( pdk.Layer(
				'PathLayer', data=path_data, get_path='Path',
				get_color=[ 0, 255, 170, 235 ], get_width=5,
				width_min_pixels=2, width_max_pixels=8, pickable=False ) )

		df_tracked_point = df_tracking.tail( 1 ).copy( )
		df_tracked_point[ 'Radius' ] = 15000.0 * point_scale
		layers.append( pdk.Layer(
			'ScatterplotLayer', data=df_tracked_point,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 0, 255, 170, 80 ], get_line_color=[ 0, 255, 170, 255 ],
			line_width_min_pixels=3, radius_min_pixels=10, radius_max_pixels=40,
			filled=True, stroked=True, pickable=False ) )

	center_latitude = float( latitude )
	center_longitude = float( longitude )
	if not (-90.0 <= center_latitude <= 90.0 and -180.0 <= center_longitude <= 180.0):
		center_latitude = float( df_map[ 'Latitude' ].median( ) )
		center_longitude = float( df_map[ 'Longitude' ].median( ) )
	if (st.session_state[ 'live_world_tracking' ]
			and st.session_state[ 'live_world_tracking_follow' ]
			and not df_tracking.empty):
		center_latitude = float( df_tracking.iloc[ -1 ][ 'Latitude' ] )
		center_longitude = float( df_tracking.iloc[ -1 ][ 'Longitude' ] )

	view_state = pdk.ViewState( latitude=center_latitude, longitude=center_longitude,
		zoom=int( st.session_state[ 'live_world_zoom' ] ), pitch=0 )
	tooltip = {
		'html': (
			'<b>{EntityType}</b><br/><b>{Name}</b><br/>'
			'<b>Source:</b> {Source}<br/><b>Time:</b> {Timestamp}<br/>'
			'<b>Coordinates:</b> {Latitude}, {Longitude}<br/>'
			'<b>Altitude / Depth:</b> {Altitude}<br/>'
			'<b>Speed:</b> {Speed}<br/><b>Heading:</b> {Heading}<br/>'
			'<b>Metadata:</b> {MetadataText}' ),
		'style': {
			'backgroundColor': 'rgba(0, 0, 0, 0.88)',
			'color': 'white',
			'fontSize': '12px',
		},
	}
	deck = pdk.Deck( layers=layers, initial_view_state=view_state,
		map_style=map_style_options[ st.session_state[ 'live_world_map_style' ] ], tooltip=tooltip )
	st.pydeck_chart( deck, use_container_width=True )

	entities_tab, aircraft_tab, satellites_tab, earthquakes_tab, fires_tab, tracking_tab = st.tabs(
		[ '🌐 Entities', '✈️ Aircraft', '🛰️ Satellites', '📈 Earthquakes', '🔥 Fires',
			'🎯 Tracking' ] )

	with entities_tab:
		st.data_editor( make_live_world_display_frame( df_map ), key='live_world_entities_table',
			use_container_width=True, disabled=True, hide_index=True )

	with aircraft_tab:
		df_aircraft_records = st.session_state.get( 'live_world_df_aircraft', pd.DataFrame( ) )
		if df_aircraft_records is None or df_aircraft_records.empty:
			st.info( 'No aircraft records loaded.' )
		else:
			st.data_editor( make_live_world_display_frame( df_aircraft_records ),
				key='live_world_aircraft_table', use_container_width=True,
				disabled=True, hide_index=True )

	with satellites_tab:
		df_satellite_records = st.session_state.get( 'live_world_df_satellites', pd.DataFrame( ) )
		if df_satellite_records is None or df_satellite_records.empty:
			st.info( 'No satellite records loaded.' )
		else:
			st.data_editor( make_live_world_display_frame( df_satellite_records ),
				key='live_world_satellite_table', use_container_width=True,
				disabled=True, hide_index=True )

	with earthquakes_tab:
		df_quakes = st.session_state.get( 'live_world_df_earthquakes', pd.DataFrame( ) )
		if df_quakes is None or df_quakes.empty:
			st.info( 'No earthquake records loaded.' )
		else:
			st.data_editor( make_live_world_display_frame( df_quakes ),
				key='live_world_earthquake_table', use_container_width=True,
				disabled=True, hide_index=True )

	with fires_tab:
		df_fire_records = st.session_state.get( 'live_world_df_fires', pd.DataFrame( ) )
		if df_fire_records is None or df_fire_records.empty:
			st.info( 'No fire records loaded.' )
		else:
			st.data_editor( make_live_world_display_frame( df_fire_records ),
				key='live_world_fire_table', use_container_width=True,
				disabled=True, hide_index=True )

	with tracking_tab:
		if df_tracking.empty:
			st.info( 'No tracking trail has been recorded. Select an aircraft or satellite and Refresh.' )
		else:
			tracking_c1, tracking_c2, tracking_c3 = st.columns( 3, border=True )
			tracking_c1.metric( 'Trail Points', f'{len( df_tracking ):,}' )
			tracking_c2.metric( 'Entity', str( df_tracking.iloc[ -1 ][ 'Name' ] ) )
			tracking_c3.metric( 'Type', str( df_tracking.iloc[ -1 ][ 'EntityType' ] ) )
			st.data_editor( df_tracking, key='live_world_tracking_table',
				use_container_width=True, disabled=True, hide_index=True )


def get_metadata_number( metadata: object, key: str, default: float=0.0 ) -> float:
	'''

		Purpose:
		--------
		Read a numeric value from a GeoEntity metadata dictionary for map sizing.

		Parameters:
		-----------
		metadata (object): Metadata dictionary.
		key (str): Metadata key.
		default (float): Fallback value.

		Returns:
		--------
		float: Numeric metadata value.

	'''
	throw_if( 'key', key )
	if not isinstance( metadata, dict ):
		return float( default )
	try:
		return float( metadata.get( key, default ) )
	except ( TypeError, ValueError ):
		return float( default )


def make_live_world_display_frame( df_frame: pd.DataFrame ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Create a Streamlit-safe display copy of Live World entity data.

		Parameters:
		-----------
		df_frame (pd.DataFrame): Live World entity data.

		Returns:
		--------
		pd.DataFrame: Display-safe entity data.

	'''
	throw_if( 'df_frame', df_frame )
	df_display = df_frame.copy( )
	if 'Metadata' in df_display.columns:
		df_display[ 'Metadata' ] = df_display[ 'Metadata' ].map(
			lambda value: json.dumps( value, default=str ) if isinstance( value, dict ) else str( value ) )
	for column in [ 'Radius', 'Magnitude', 'MetadataText' ]:
		if column in df_display.columns:
			df_display = df_display.drop( columns=[ column ] )
	return df_display
