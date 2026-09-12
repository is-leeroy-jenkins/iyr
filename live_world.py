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
    live aircraft, military aircraft, satellite, vessel, earthquake, and active-fire retrieval,
    normalized geospatial entities, operational PyDeck rendering, entity tracking and trails,
    refresh controls,
    filtering, and source-data inspection.
******************************************************************************************
'''

from __future__ import annotations

import datetime as dt
import json
import math
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

import pandas as pd
import pydeck as pdk
import streamlit as st

from fetchers import Firms, USGSEarthquakes
from live_world_sources import AdsbLolMilitary, AisStreamLive, CelesTrakLive, OpenSkyLive


LIVE_WORLD_LAYERS: Dict[ str, str ] = {
	'aircraft': '✈️ Aircraft (Live)',
	'military_aircraft': '🛩️ Military Aircraft',
	'satellites': '🛰️ Satellites',
	'vessels': '🚢 Vessels & Ships',
	'earthquakes': '📈 Earthquakes',
	'fires': '🔥 Fires (Wildfires)',
	'tracking': '🎯 Tracking & Trails',
	'measurements': '📏 Measurements & Annotations',
}

LIVE_WORLD_PENDING_LAYERS: Dict[ str, str ] = {
	'cameras': '📷 CCTV / Web Cameras',
	'infrastructure': '📡 Infrastructure (Airports, Ports, etc.)',
	'map_layers': '🗺️ Additional Map Layers',
}

AI_ADVANCED_TOOLS: Dict[ str, str ] = {
	'cross_layer_analysis': '🧭 Cross-Layer Analysis',
}

AI_ADVANCED_PENDING_TOOLS: Dict[ str, str ] = {
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
		'live_world_military_aircraft': False,
		'live_world_military_radius_nm': 250,
		'live_world_satellites': False,
		'live_world_satellite_group': 'stations',
		'live_world_satellite_limit': 100,
		'live_world_vessels': False,
		'live_world_aisstream_api_key': os.getenv( 'AISSTREAM_API_KEY', '' ) or '',
		'live_world_vessel_radius': 2.0,
		'live_world_vessel_limit': 100,
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
		'live_world_measurements': False,
		'live_world_measurement_start': 'Current Location',
		'live_world_measurement_end': 'Current Location',
		'live_world_measurement_custom_start_latitude': 0.0,
		'live_world_measurement_custom_start_longitude': 0.0,
		'live_world_measurement_custom_end_latitude': 0.0,
		'live_world_measurement_custom_end_longitude': 0.0,
		'live_world_annotation_label': '',
		'live_world_annotation_latitude': 0.0,
		'live_world_annotation_longitude': 0.0,
		'live_world_annotations': [ ],
		'live_world_cross_layer_analysis': False,
		'live_world_analysis_origin': 'Current Location',
		'live_world_analysis_custom_latitude': 0.0,
		'live_world_analysis_custom_longitude': 0.0,
		'live_world_analysis_radius_nm': 250,
		'live_world_analysis_entity_types': [
			'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel', 'Earthquake', 'Fire' ],
		'live_world_analysis_limit': 100,
		'live_world_refresh_requested': False,
		'live_world_last_refresh': '',
		'live_world_last_error': '',
		'live_world_df_entities': pd.DataFrame( ),
		'live_world_df_aircraft': pd.DataFrame( ),
		'live_world_df_military_aircraft': pd.DataFrame( ),
		'live_world_df_satellites': pd.DataFrame( ),
		'live_world_df_vessels': pd.DataFrame( ),
		'live_world_df_earthquakes': pd.DataFrame( ),
		'live_world_df_fires': pd.DataFrame( ),
		'live_world_aircraft_result': { },
		'live_world_military_aircraft_result': { },
		'live_world_satellite_result': [ ],
		'live_world_vessel_result': [ ],
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

		st.checkbox( LIVE_WORLD_LAYERS[ 'military_aircraft' ],
			key='live_world_military_aircraft' )
		if st.session_state[ 'live_world_military_aircraft' ]:
			st.slider( 'Military Aircraft Radius (NM)', min_value=25, max_value=250,
				step=25, key='live_world_military_radius_nm' )
			st.caption( 'Military-tagged aircraft are retrieved from ADSB.lol.' )

		st.checkbox( LIVE_WORLD_LAYERS[ 'satellites' ], key='live_world_satellites' )
		if st.session_state[ 'live_world_satellites' ]:
			st.selectbox( 'Satellite Group',
				options=[ 'stations', 'visual', 'weather', 'gps-ops', 'active' ],
				key='live_world_satellite_group' )
			st.slider( 'Satellite Limit', min_value=10, max_value=500, step=10,
				key='live_world_satellite_limit' )

		st.checkbox( LIVE_WORLD_LAYERS[ 'vessels' ], key='live_world_vessels' )
		if st.session_state[ 'live_world_vessels' ]:
			st.text_input( 'AIS Stream API Key', type='password',
				key='live_world_aisstream_api_key',
				help='Uses AISSTREAM_API_KEY when configured in the environment.' )
			st.slider( 'Vessel Radius (Degrees)', min_value=0.25, max_value=10.0,
				step=0.25, key='live_world_vessel_radius' )
			st.slider( 'Vessel Message Limit', min_value=10, max_value=250, step=10,
				key='live_world_vessel_limit' )

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

		st.checkbox( LIVE_WORLD_LAYERS[ 'measurements' ], key='live_world_measurements' )
		if st.session_state[ 'live_world_measurements' ]:
			measurement_options = get_live_world_measurement_options( )
			measurement_keys = list( measurement_options.keys( ) )
			if st.session_state[ 'live_world_measurement_start' ] not in measurement_keys:
				st.session_state[ 'live_world_measurement_start' ] = 'Current Location'
			if st.session_state[ 'live_world_measurement_end' ] not in measurement_keys:
				st.session_state[ 'live_world_measurement_end' ] = 'Current Location'
			measure_c1, measure_c2 = st.columns( 2 )
			with measure_c1:
				st.selectbox( 'Measure From', options=measurement_keys,
					format_func=lambda value: measurement_options[ value ],
					key='live_world_measurement_start' )
			with measure_c2:
				st.selectbox( 'Measure To', options=measurement_keys,
					format_func=lambda value: measurement_options[ value ],
					key='live_world_measurement_end' )
			if st.session_state[ 'live_world_measurement_start' ] == 'Custom Point':
				custom_start_c1, custom_start_c2 = st.columns( 2 )
				with custom_start_c1:
					st.number_input( 'Start Latitude', min_value=-90.0, max_value=90.0,
						format='%.6f', key='live_world_measurement_custom_start_latitude' )
				with custom_start_c2:
					st.number_input( 'Start Longitude', min_value=-180.0, max_value=180.0,
						format='%.6f', key='live_world_measurement_custom_start_longitude' )
			if st.session_state[ 'live_world_measurement_end' ] == 'Custom Point':
				custom_end_c1, custom_end_c2 = st.columns( 2 )
				with custom_end_c1:
					st.number_input( 'End Latitude', min_value=-90.0, max_value=90.0,
						format='%.6f', key='live_world_measurement_custom_end_latitude' )
				with custom_end_c2:
					st.number_input( 'End Longitude', min_value=-180.0, max_value=180.0,
						format='%.6f', key='live_world_measurement_custom_end_longitude' )

			st.caption( 'Annotations' )
			st.text_input( 'Annotation Label', key='live_world_annotation_label' )
			annotation_c1, annotation_c2 = st.columns( 2 )
			with annotation_c1:
				st.number_input( 'Annotation Latitude', min_value=-90.0, max_value=90.0,
					format='%.6f', key='live_world_annotation_latitude' )
			with annotation_c2:
				st.number_input( 'Annotation Longitude', min_value=-180.0, max_value=180.0,
					format='%.6f', key='live_world_annotation_longitude' )
			annotation_button_c1, annotation_button_c2 = st.columns( 2 )
			with annotation_button_c1:
				if st.button( 'Add Annotation', icon='📍', key='live_world_annotation_add',
						width='stretch' ):
					add_live_world_annotation( )
			with annotation_button_c2:
				if st.button( 'Clear Annotations', icon='🧹', key='live_world_annotation_clear',
						width='stretch' ):
					clear_live_world_annotations( )

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
				st.info( 'Refresh a moving Live World layer before selecting a tracked entity.' )
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
			st.caption( 'Advanced tools operate on the currently loaded Live World entity frame.' )
			st.checkbox( AI_ADVANCED_TOOLS[ 'cross_layer_analysis' ],
				key='live_world_cross_layer_analysis' )
			if st.session_state[ 'live_world_cross_layer_analysis' ]:
				analysis_options = get_live_world_analysis_origin_options( )
				analysis_keys = list( analysis_options.keys( ) )
				if st.session_state[ 'live_world_analysis_origin' ] not in analysis_keys:
					st.session_state[ 'live_world_analysis_origin' ] = 'Current Location'
				st.selectbox( 'Analysis Origin', options=analysis_keys,
					format_func=lambda value: analysis_options[ value ],
					key='live_world_analysis_origin' )
				if st.session_state[ 'live_world_analysis_origin' ] == 'Custom Point':
					analysis_c1, analysis_c2 = st.columns( 2 )
					with analysis_c1:
						st.number_input( 'Analysis Latitude', min_value=-90.0, max_value=90.0,
							format='%.6f', key='live_world_analysis_custom_latitude' )
					with analysis_c2:
						st.number_input( 'Analysis Longitude', min_value=-180.0, max_value=180.0,
							format='%.6f', key='live_world_analysis_custom_longitude' )
				st.slider( 'Analysis Radius (NM)', min_value=10, max_value=2500,
					step=10, key='live_world_analysis_radius_nm' )
				st.multiselect( 'Entity Types',
					options=[ 'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel',
						'Earthquake', 'Fire' ],
					key='live_world_analysis_entity_types' )
				st.slider( 'Analysis Result Limit', min_value=10, max_value=500,
					step=10, key='live_world_analysis_limit' )
			for label in AI_ADVANCED_PENDING_TOOLS.values( ):
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
	st.session_state[ 'live_world_df_military_aircraft' ] = pd.DataFrame( )
	st.session_state[ 'live_world_df_satellites' ] = pd.DataFrame( )
	st.session_state[ 'live_world_df_vessels' ] = pd.DataFrame( )
	st.session_state[ 'live_world_df_earthquakes' ] = pd.DataFrame( )
	st.session_state[ 'live_world_df_fires' ] = pd.DataFrame( )
	st.session_state[ 'live_world_aircraft_result' ] = { }
	st.session_state[ 'live_world_military_aircraft_result' ] = { }
	st.session_state[ 'live_world_satellite_result' ] = [ ]
	st.session_state[ 'live_world_vessel_result' ] = [ ]
	st.session_state[ 'live_world_earthquake_result' ] = { }
	st.session_state[ 'live_world_firms_result' ] = { }
	st.session_state[ 'live_world_tracking_history' ] = [ ]
	st.session_state[ 'live_world_tracking_active_entity' ] = ''
	st.session_state[ 'live_world_annotations' ] = [ ]
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



def calculate_live_world_distance_nm( latitude_a: float, longitude_a: float,
		latitude_b: float, longitude_b: float ) -> float:
	'''

		Purpose:
		--------
		Calculate great-circle distance between two geospatial points in nautical miles.

		Parameters:
		-----------
		latitude_a (float): First latitude.
		longitude_a (float): First longitude.
		latitude_b (float): Second latitude.
		longitude_b (float): Second longitude.

		Returns:
		--------
		float: Great-circle distance in nautical miles.

	'''
	throw_if( 'latitude_a', latitude_a )
	throw_if( 'longitude_a', longitude_a )
	throw_if( 'latitude_b', latitude_b )
	throw_if( 'longitude_b', longitude_b )
	lat_a = math.radians( float( latitude_a ) )
	lat_b = math.radians( float( latitude_b ) )
	delta_lat = math.radians( float( latitude_b ) - float( latitude_a ) )
	delta_lon = math.radians( float( longitude_b ) - float( longitude_a ) )
	value = (math.sin( delta_lat / 2.0 ) ** 2
		+ math.cos( lat_a ) * math.cos( lat_b ) * math.sin( delta_lon / 2.0 ) ** 2)
	central_angle = 2.0 * math.atan2( math.sqrt( value ), math.sqrt( 1.0 - value ) )
	return 3440.065 * central_angle


def fetch_live_military_aircraft( latitude: float, longitude: float ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Retrieve ADSB.lol military-tagged aircraft and normalize aircraft within the
		configured nautical-mile radius around the current Iyr location.

		Parameters:
		-----------
		latitude (float): Geographic center latitude.
		longitude (float): Geographic center longitude.

		Returns:
		--------
		pd.DataFrame: Normalized military-aircraft entities.

	'''
	initialize_live_world_state( )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	radius_nm = float( st.session_state[ 'live_world_military_radius_nm' ] )
	service = AdsbLolMilitary( timeout=20 )
	result = service.fetch_military( latitude=latitude, longitude=longitude,
		radius_nm=radius_nm ) or { }
	rows = result.get( 'ac', [ ] ) or [ ]
	entities: List[ GeoEntity ] = [ ]

	for index, row in enumerate( rows ):
		if not isinstance( row, dict ):
			continue
		latitude_value = row.get( 'lat', None )
		longitude_value = row.get( 'lon', None )
		if latitude_value is None or longitude_value is None:
			continue

		try:
			lat = float( latitude_value )
			lon = float( longitude_value )
		except ( TypeError, ValueError ):
			continue

		distance_nm = calculate_live_world_distance_nm( latitude, longitude, lat, lon )
		if distance_nm > radius_nm:
			continue

		altitude = row.get( 'alt_geom', row.get( 'alt_baro', 0.0 ) )
		ground_speed = row.get( 'gs', 0.0 )
		heading = row.get( 'track', row.get( 'true_heading', 0.0 ) )
		try:
			altitude_meters = float( altitude ) * 0.3048 if altitude not in [ None, 'ground' ] else 0.0
		except ( TypeError, ValueError ):
			altitude_meters = 0.0
		try:
			speed_mps = float( ground_speed ) * 0.514444 if ground_speed is not None else 0.0
		except ( TypeError, ValueError ):
			speed_mps = 0.0
		try:
			heading_value = float( heading ) if heading is not None else 0.0
		except ( TypeError, ValueError ):
			heading_value = 0.0

		hex_id = str( row.get( 'hex', '' ) or '' ).strip( )
		flight = str( row.get( 'flight', '' ) or '' ).strip( )
		registration = str( row.get( 'r', '' ) or '' ).strip( )
		metadata = {
			'ICAO Hex': hex_id,
			'Callsign': flight,
			'Registration': registration,
			'Aircraft Type': row.get( 't', '' ),
			'Description': row.get( 'desc', '' ),
			'Category': row.get( 'category', '' ),
			'Squawk': row.get( 'squawk', '' ),
			'Emergency': row.get( 'emergency', '' ),
			'DB Flags': row.get( 'dbFlags', 1 ),
			'Altitude (ft)': altitude,
			'Ground Speed (kt)': ground_speed,
			'Vertical Rate': row.get( 'baro_rate', row.get( 'geom_rate', None ) ),
			'Distance (NM)': round( distance_nm, 2 ),
		}
		entities.append( GeoEntity(
			entity_id=hex_id or f'ADSBLOL-MIL-{index + 1}',
			entity_type='Military Aircraft',
			name=flight or registration or hex_id,
			latitude=lat,
			longitude=lon,
			altitude=altitude_meters,
			heading=heading_value,
			speed=speed_mps,
			timestamp=dt.datetime.now( dt.timezone.utc ).isoformat( ),
			source='ADSB.lol',
			metadata=metadata ) )

	st.session_state[ 'live_world_military_aircraft_result' ] = result
	return entities_to_dataframe( entities )


def fetch_live_vessels( latitude: float, longitude: float ) -> pd.DataFrame:
	'''

		Purpose:
		--------
		Retrieve a bounded live AIS Stream vessel sample around the current Iyr location
		and normalize the messages for Live World rendering and tracking.

		Parameters:
		-----------
		latitude (float): Geographic center latitude.
		longitude (float): Geographic center longitude.

		Returns:
		--------
		pd.DataFrame: Normalized vessel entities.

	'''
	initialize_live_world_state( )
	throw_if( 'latitude', latitude )
	throw_if( 'longitude', longitude )
	api_key = str( st.session_state.get( 'live_world_aisstream_api_key', '' ) or '' )
	throw_if( 'live_world_aisstream_api_key', api_key )
	radius = float( st.session_state[ 'live_world_vessel_radius' ] )
	limit = int( st.session_state[ 'live_world_vessel_limit' ] )
	service = AisStreamLive( api_key=api_key, timeout=5 )
	result = service.fetch_positions( latitude=latitude, longitude=longitude,
		radius_degrees=radius, max_messages=limit, duration_seconds=3.0 )
	entities_by_mmsi: Dict[ str, GeoEntity ] = { }

	for index, envelope in enumerate( result ):
		metadata_source = envelope.get( 'MetaData', { } ) or { }
		message_type = str( envelope.get( 'MessageType', '' ) or '' )
		message = envelope.get( 'Message', { } ) or { }
		body = message.get( message_type, { } ) or { }
		latitude_value = metadata_source.get( 'Latitude', body.get( 'Latitude', None ) )
		longitude_value = metadata_source.get( 'Longitude', body.get( 'Longitude', None ) )
		if latitude_value is None or longitude_value is None:
			continue

		try:
			lat = float( latitude_value )
			lon = float( longitude_value )
		except ( TypeError, ValueError ):
			continue

		mmsi = str( metadata_source.get( 'MMSI', body.get( 'UserID', '' ) ) or '' )
		ship_name = str( metadata_source.get( 'ShipName', '' ) or '' ).strip( )
		speed_knots = body.get( 'Sog', 0.0 )
		heading = body.get( 'TrueHeading', body.get( 'Cog', 0.0 ) )
		try:
			speed_mps = float( speed_knots ) * 0.514444 if speed_knots is not None else 0.0
		except ( TypeError, ValueError ):
			speed_mps = 0.0
		try:
			heading_value = float( heading ) if heading is not None else 0.0
		except ( TypeError, ValueError ):
			heading_value = 0.0

		metadata = {
			'MMSI': mmsi,
			'Message Type': message_type,
			'Speed Over Ground (kt)': speed_knots,
			'Course Over Ground': body.get( 'Cog', None ),
			'True Heading': body.get( 'TrueHeading', None ),
			'Navigational Status': body.get( 'NavigationalStatus', None ),
			'Position Accuracy': body.get( 'PositionAccuracy', None ),
			'RAIM': body.get( 'Raim', None ),
		}
		entity_id = mmsi or f'AIS-{index + 1}'
		entities_by_mmsi[ entity_id ] = GeoEntity(
			entity_id=entity_id,
			entity_type='Vessel',
			name=ship_name or entity_id,
			latitude=lat,
			longitude=lon,
			altitude=0.0,
			heading=heading_value,
			speed=speed_mps,
			timestamp=dt.datetime.now( dt.timezone.utc ).isoformat( ),
			source='AIS Stream',
			metadata=metadata )

	st.session_state[ 'live_world_vessel_result' ] = result
	return entities_to_dataframe( list( entities_by_mmsi.values( ) ) )

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
		[ 'Aircraft', 'Military Aircraft', 'Satellite', 'Vessel' ] ) ].copy( )
	options: Dict[ str, str ] = { }
	for _, row in df_tracking.iterrows( ):
		entity_id = str( row[ 'EntityId' ] )
		entity_type = str( row[ 'EntityType' ] )
		name = str( row[ 'Name' ] )
		tracking_key = f'{entity_type}::{entity_id}'
		options[ tracking_key ] = f'{entity_type} | {name} | {entity_id}'
	return options




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

		if st.session_state[ 'live_world_military_aircraft' ]:
			df_military = fetch_live_military_aircraft( latitude, longitude )
			st.session_state[ 'live_world_df_military_aircraft' ] = df_military
			if not df_military.empty:
				frames.append( df_military )
		else:
			st.session_state[ 'live_world_df_military_aircraft' ] = pd.DataFrame( )

		if st.session_state[ 'live_world_satellites' ]:
			df_satellites = fetch_live_satellites( )
			st.session_state[ 'live_world_df_satellites' ] = df_satellites
			if not df_satellites.empty:
				frames.append( df_satellites )
		else:
			st.session_state[ 'live_world_df_satellites' ] = pd.DataFrame( )

		if st.session_state[ 'live_world_vessels' ]:
			df_vessels = fetch_live_vessels( latitude, longitude )
			st.session_state[ 'live_world_df_vessels' ] = df_vessels
			if not df_vessels.empty:
				frames.append( df_vessels )
		else:
			st.session_state[ 'live_world_df_vessels' ] = pd.DataFrame( )

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
		if not st.session_state[ 'live_world_measurements' ]:
			st.info( 'No Live World data has been loaded. Select Refresh in the sidebar.' )
			return
		df_entities = entities_to_dataframe( [ ] )

	df_map = df_entities.copy( )
	df_map[ 'MetadataText' ] = df_map[ 'Metadata' ].map(
		lambda value: json.dumps( value, default=str ) if isinstance( value, dict ) else str( value ) )
	df_map[ 'Latitude' ] = pd.to_numeric( df_map[ 'Latitude' ], errors='coerce' )
	df_map[ 'Longitude' ] = pd.to_numeric( df_map[ 'Longitude' ], errors='coerce' )
	df_map = df_map.dropna( subset=[ 'Latitude', 'Longitude' ] )
	if df_map.empty and not st.session_state[ 'live_world_measurements' ]:
		st.info( 'Live World data does not contain usable map coordinates.' )
		return

	last_refresh = str( st.session_state.get( 'live_world_last_refresh', '' ) or 'Not refreshed' )
	metric_c1, metric_c2, metric_c3, metric_c4, metric_c5 = st.columns( 5, border=True )
	metric_c1.metric( 'Entities', f'{len( df_map ):,}' )
	metric_c2.metric( 'Aircraft',
		f'{int( (df_map[ "EntityType" ] == "Aircraft").sum( ) ):,}' )
	metric_c3.metric( 'Military',
		f'{int( (df_map[ "EntityType" ] == "Military Aircraft").sum( ) ):,}' )
	metric_c4.metric( 'Satellites',
		f'{int( (df_map[ "EntityType" ] == "Satellite").sum( ) ):,}' )
	metric_c5.metric( 'Vessels',
		f'{int( (df_map[ "EntityType" ] == "Vessel").sum( ) ):,}' )
	event_c1, event_c2 = st.columns( 2, border=True )
	event_c1.metric( 'Earthquakes',
		f'{int( (df_map[ "EntityType" ] == "Earthquake").sum( ) ):,}' )
	event_c2.metric( 'Fires', f'{int( (df_map[ "EntityType" ] == "Fire").sum( ) ):,}' )
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
	df_military = df_map[ df_map[ 'EntityType' ] == 'Military Aircraft' ].copy( )
	df_satellites = df_map[ df_map[ 'EntityType' ] == 'Satellite' ].copy( )
	df_vessels = df_map[ df_map[ 'EntityType' ] == 'Vessel' ].copy( )
	df_earthquakes = df_map[ df_map[ 'EntityType' ] == 'Earthquake' ].copy( )
	df_fires = df_map[ df_map[ 'EntityType' ] == 'Fire' ].copy( )

	df_analysis = pd.DataFrame( )
	analysis_origin: Dict[ str, object ] = { }
	analysis_error = ''
	if st.session_state[ 'live_world_cross_layer_analysis' ]:
		try:
			analysis_origin = resolve_live_world_analysis_origin(
				str( st.session_state[ 'live_world_analysis_origin' ] ), latitude, longitude )
			df_analysis = calculate_live_world_cross_layer_analysis( latitude, longitude )
			df_analysis_origin = pd.DataFrame( [ analysis_origin ] )
			df_analysis_origin[ 'Radius' ] = float(
				st.session_state[ 'live_world_analysis_radius_nm' ] ) * 1852.0
			layers.append( pdk.Layer( 'ScatterplotLayer', data=df_analysis_origin,
				get_position='[Longitude, Latitude]', get_radius='Radius',
				get_fill_color=[ 80, 180, 255, 20 ], get_line_color=[ 80, 180, 255, 180 ],
				line_width_min_pixels=2, radius_min_pixels=1,
				filled=True, stroked=True, pickable=False ) )
			df_analysis_origin[ 'Radius' ] = 12000.0 * point_scale
			layers.append( pdk.Layer( 'ScatterplotLayer', data=df_analysis_origin,
				get_position='[Longitude, Latitude]', get_radius='Radius',
				get_fill_color=[ 80, 180, 255, 180 ], get_line_color=[ 255, 255, 255, 255 ],
				line_width_min_pixels=2, radius_min_pixels=8, radius_max_pixels=30,
				filled=True, stroked=True, pickable=False ) )
			if not df_analysis.empty:
				df_analysis_points = df_analysis.copy( )
				df_analysis_points[ 'Radius' ] = 11000.0 * point_scale
				layers.append( pdk.Layer( 'ScatterplotLayer', data=df_analysis_points,
					get_position='[Longitude, Latitude]', get_radius='Radius',
					get_fill_color=[ 255, 255, 255, 35 ], get_line_color=[ 80, 180, 255, 255 ],
					line_width_min_pixels=2, radius_min_pixels=7, radius_max_pixels=28,
					filled=True, stroked=True, pickable=True ) )
		except Exception as ex:
			analysis_error = str( ex )

	if not df_aircraft.empty:
		df_aircraft[ 'Radius' ] = 7000.0 * point_scale
		layers.append( pdk.Layer(
			'ScatterplotLayer', data=df_aircraft,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 0, 170, 255, 220 ], get_line_color=[ 220, 245, 255, 240 ],
			line_width_min_pixels=1, radius_min_pixels=5, radius_max_pixels=26,
			filled=True, stroked=True, pickable=True ) )

	if not df_military.empty:
		df_military[ 'Radius' ] = 8500.0 * point_scale
		layers.append( pdk.Layer(
			'ScatterplotLayer', data=df_military,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 255, 45, 85, 225 ], get_line_color=[ 255, 220, 225, 245 ],
			line_width_min_pixels=2, radius_min_pixels=6, radius_max_pixels=30,
			filled=True, stroked=True, pickable=True ) )

	if not df_satellites.empty:
		df_satellites[ 'Radius' ] = 8500.0 * point_scale
		layers.append( pdk.Layer(
			'ScatterplotLayer', data=df_satellites,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 180, 120, 255, 220 ], get_line_color=[ 245, 235, 255, 240 ],
			line_width_min_pixels=1, radius_min_pixels=5, radius_max_pixels=28,
			filled=True, stroked=True, pickable=True ) )

	if not df_vessels.empty:
		df_vessels[ 'Radius' ] = 7500.0 * point_scale
		layers.append( pdk.Layer(
			'ScatterplotLayer', data=df_vessels,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 0, 210, 190, 220 ], get_line_color=[ 210, 255, 250, 240 ],
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

	df_measurement = pd.DataFrame( )
	measurement_result: Dict[ str, object ] = { }
	if st.session_state[ 'live_world_measurements' ]:
		try:
			measurement_result = calculate_live_world_measurement( latitude, longitude )
			start = measurement_result[ 'Start' ]
			end = measurement_result[ 'End' ]
			df_measurement = pd.DataFrame( [ start, end ] )
			path_data = [ { 'Path': [
				[ float( start[ 'Longitude' ] ), float( start[ 'Latitude' ] ) ],
				[ float( end[ 'Longitude' ] ), float( end[ 'Latitude' ] ) ] ] } ]
			layers.append( pdk.Layer( 'PathLayer', data=path_data, get_path='Path',
				get_color=[ 255, 255, 255, 230 ], get_width=4,
				width_min_pixels=2, width_max_pixels=7, pickable=False ) )
			df_measurement[ 'Radius' ] = 10000.0 * point_scale
			layers.append( pdk.Layer( 'ScatterplotLayer', data=df_measurement,
				get_position='[Longitude, Latitude]', get_radius='Radius',
				get_fill_color=[ 255, 255, 255, 80 ], get_line_color=[ 255, 255, 255, 255 ],
				line_width_min_pixels=2, radius_min_pixels=7, radius_max_pixels=28,
				filled=True, stroked=True, pickable=False ) )
		except Exception as ex:
			measurement_result = { 'Error': str( ex ) }

	df_annotations = get_live_world_annotation_frame( )
	if st.session_state[ 'live_world_measurements' ] and not df_annotations.empty:
		df_annotation_points = df_annotations.copy( )
		df_annotation_points[ 'Radius' ] = 9000.0 * point_scale
		layers.append( pdk.Layer( 'ScatterplotLayer', data=df_annotation_points,
			get_position='[Longitude, Latitude]', get_radius='Radius',
			get_fill_color=[ 255, 210, 0, 180 ], get_line_color=[ 255, 255, 255, 255 ],
			line_width_min_pixels=2, radius_min_pixels=7, radius_max_pixels=28,
			filled=True, stroked=True, pickable=True ) )
		layers.append( pdk.Layer( 'TextLayer', data=df_annotations,
			get_position='[Longitude, Latitude]', get_text='Label', get_size=14,
			get_color=[ 255, 255, 255, 255 ], get_angle=0,
			get_text_anchor='middle', get_alignment_baseline='bottom', pickable=False ) )

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
	if (st.session_state[ 'live_world_cross_layer_analysis' ] and analysis_origin):
		center_latitude = float( analysis_origin[ 'Latitude' ] )
		center_longitude = float( analysis_origin[ 'Longitude' ] )
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

	entities_tab, aircraft_tab, military_tab, satellites_tab, vessels_tab, earthquakes_tab, fires_tab, tracking_tab, measurements_tab, analysis_tab = st.tabs(
		[ '🌐 Entities', '✈️ Aircraft', '🛩️ Military', '🛰️ Satellites', '🚢 Vessels',
			'📈 Earthquakes', '🔥 Fires', '🎯 Tracking', '📏 Measurements', '🧭 Analysis' ] )

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

	with military_tab:
		df_military_records = st.session_state.get(
			'live_world_df_military_aircraft', pd.DataFrame( ) )
		if df_military_records is None or df_military_records.empty:
			st.info( 'No military aircraft records loaded.' )
		else:
			st.data_editor( make_live_world_display_frame( df_military_records ),
				key='live_world_military_aircraft_table', use_container_width=True,
				disabled=True, hide_index=True )

	with satellites_tab:
		df_satellite_records = st.session_state.get( 'live_world_df_satellites', pd.DataFrame( ) )
		if df_satellite_records is None or df_satellite_records.empty:
			st.info( 'No satellite records loaded.' )
		else:
			st.data_editor( make_live_world_display_frame( df_satellite_records ),
				key='live_world_satellite_table', use_container_width=True,
				disabled=True, hide_index=True )

	with vessels_tab:
		df_vessel_records = st.session_state.get( 'live_world_df_vessels', pd.DataFrame( ) )
		if df_vessel_records is None or df_vessel_records.empty:
			st.info( 'No vessel records loaded.' )
		else:
			st.data_editor( make_live_world_display_frame( df_vessel_records ),
				key='live_world_vessel_table', use_container_width=True,
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
			st.info( 'No tracking trail has been recorded. Select a moving entity and Refresh.' )
		else:
			tracking_c1, tracking_c2, tracking_c3 = st.columns( 3, border=True )
			tracking_c1.metric( 'Trail Points', f'{len( df_tracking ):,}' )
			tracking_c2.metric( 'Entity', str( df_tracking.iloc[ -1 ][ 'Name' ] ) )
			tracking_c3.metric( 'Type', str( df_tracking.iloc[ -1 ][ 'EntityType' ] ) )
			st.data_editor( df_tracking, key='live_world_tracking_table',
				use_container_width=True, disabled=True, hide_index=True )


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
