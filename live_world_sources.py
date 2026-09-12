'''
******************************************************************************************
 Assembly:                iyr
 Filename:                live_world_sources.py
 Author:                  Terry D. Eppler / Assistant
 Created:                 09-12-2026

 Last Modified By:        Terry D. Eppler / Assistant
 Last Modified On:        09-12-2026
******************************************************************************************

Purpose:
    Provider clients used by Iyr Live World Data for real-time aircraft state vectors,
    military aircraft, maritime AIS positions, and current satellite orbital elements.
    OpenSky access uses the current OAuth2 client-credentials flow when API-client
    credentials are available. ADSB.lol provides public military-tagged aircraft data.
    AIS Stream provides server-side WebSocket maritime position events. CelesTrak data is
    requested in OMM JSON format and propagated with SGP4 before conversion to Earth-fixed
    coordinates.
******************************************************************************************
'''

from __future__ import annotations

import datetime as dt
import json
import math
import time
from typing import Any, Dict, List

import requests
from astropy import units as u
from astropy.coordinates import CartesianRepresentation, EarthLocation, ITRS, TEME
from astropy.time import Time
from requests import Response
from sgp4 import omm
from sgp4.api import Satrec
from websocket import WebSocket, WebSocketTimeoutException, create_connection


def throw_if( name: str, value: object ) -> None:
	'''

		Purpose:
		--------
		Validate a required runtime argument.

		Parameters:
		-----------
		name (str): Argument name.
		value (object): Argument value.

		Returns:
		--------
		None

	'''
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be None.' )

	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty.' )


class OpenSkyLive:
	'''

		Purpose:
		--------
		Retrieve current OpenSky state vectors for a geographic bounding box.

	'''
	client_id: str
	client_secret: str
	timeout: int
	token_url: str
	states_url: str
	access_token: str
	response: Response | None

	def __init__( self, client_id: str='', client_secret: str='', timeout: int=20 ) -> None:
		'''

			Purpose:
			--------
			Initialize OpenSky REST API access. Credentials are optional because OpenSky can
			serve anonymous requests subject to the provider's current access limits.

			Parameters:
			-----------
			client_id (str): OpenSky API Client identifier.
			client_secret (str): OpenSky API Client secret.
			timeout (int): HTTP timeout in seconds.

			Returns:
			--------
			None

		'''
		self.client_id = client_id
		self.client_secret = client_secret
		self.timeout = timeout
		self.token_url = (
			'https://auth.opensky-network.org/auth/realms/opensky-network/'
			'protocol/openid-connect/token' )
		self.states_url = 'https://opensky-network.org/api/states/all'
		self.access_token = ''
		self.response = None

	def get_access_token( self ) -> str:
		'''

			Purpose:
			--------
			Obtain an OpenSky OAuth2 access token using the configured API Client.

			Returns:
			--------
			str: Bearer access token, or an empty string when credentials were not supplied.

		'''
		if not self.client_id or not self.client_secret:
			return ''

		data = {
			'grant_type': 'client_credentials',
			'client_id': self.client_id,
			'client_secret': self.client_secret,
		}
		self.response = requests.post( self.token_url, data=data, timeout=self.timeout )
		self.response.raise_for_status( )
		payload = self.response.json( ) or { }
		self.access_token = str( payload.get( 'access_token', '' ) or '' )
		throw_if( 'access_token', self.access_token )
		return self.access_token

	def fetch_states( self, latitude: float, longitude: float,
			radius_degrees: float=2.0 ) -> Dict[ str, Any ]:
		'''

			Purpose:
			--------
			Retrieve live aircraft state vectors within a geographic bounding box centered
			on the supplied latitude and longitude.

			Parameters:
			-----------
			latitude (float): Bounding-box center latitude.
			longitude (float): Bounding-box center longitude.
			radius_degrees (float): Decimal-degree half-width of the bounding box.

			Returns:
			--------
			Dict[str, Any]: OpenSky state-vector payload.

		'''
		throw_if( 'latitude', latitude )
		throw_if( 'longitude', longitude )
		throw_if( 'radius_degrees', radius_degrees )
		self.latitude = float( latitude )
		self.longitude = float( longitude )
		self.radius_degrees = float( radius_degrees )
		self.lamin = max( -90.0, self.latitude - self.radius_degrees )
		self.lamax = min( 90.0, self.latitude + self.radius_degrees )
		self.lomin = max( -180.0, self.longitude - self.radius_degrees )
		self.lomax = min( 180.0, self.longitude + self.radius_degrees )
		self.params = {
			'lamin': self.lamin,
			'lomin': self.lomin,
			'lamax': self.lamax,
			'lomax': self.lomax,
		}
		self.headers: Dict[ str, str ] = { }
		self.access_token = self.get_access_token( )
		if self.access_token:
			self.headers[ 'Authorization' ] = f'Bearer {self.access_token}'

		self.response = requests.get( self.states_url, params=self.params,
			headers=self.headers, timeout=self.timeout )
		self.response.raise_for_status( )
		return self.response.json( ) or { }


class AdsbLolMilitary:
	'''

		Purpose:
		--------
		Retrieve aircraft currently tagged as military by ADSB.lol.

	'''
	timeout: int
	url: str
	response: Response | None

	def __init__( self, timeout: int=20 ) -> None:
		'''

			Purpose:
			--------
			Initialize ADSB.lol military-aircraft access.

			Parameters:
			-----------
			timeout (int): HTTP timeout in seconds.

			Returns:
			--------
			None

		'''
		self.timeout = timeout
		self.url = 'https://api.adsb.lol/v2/point'
		self.response = None

	def fetch_military( self, latitude: float, longitude: float,
			radius_nm: float=250.0 ) -> Dict[ str, Any ]:
		'''

			Purpose:
			--------
			Retrieve ADSB.lol aircraft around a geographic point and retain records
			whose database flags identify them as military aircraft.

			Parameters:
			-----------
			latitude (float): Geographic center latitude.
			longitude (float): Geographic center longitude.
			radius_nm (float): Search radius in nautical miles.

			Returns:
			--------
			Dict[str, Any]: ADSB.lol payload containing only military-tagged aircraft.

		'''
		throw_if( 'latitude', latitude )
		throw_if( 'longitude', longitude )
		throw_if( 'radius_nm', radius_nm )
		self.latitude = float( latitude )
		self.longitude = float( longitude )
		self.radius_nm = float( radius_nm )
		self.request_url = (
			f'{self.url}/{self.latitude:.6f}/{self.longitude:.6f}/{self.radius_nm:.1f}' )
		self.response = requests.get( self.request_url, timeout=self.timeout )
		self.response.raise_for_status( )
		payload = self.response.json( ) or { }
		if not isinstance( payload, dict ):
			raise TypeError( 'ADSB.lol point response must be a dictionary.' )
		aircraft = payload.get( 'ac', [ ] ) or [ ]
		payload[ 'ac' ] = [
			row for row in aircraft
			if isinstance( row, dict ) and int( row.get( 'dbFlags', 0 ) or 0 ) & 1
		]
		return payload


class AisStreamLive:
	'''

		Purpose:
		--------
		Retrieve live maritime AIS position reports through the AIS Stream WebSocket API.

	'''
	api_key: str
	timeout: int
	url: str
	socket: WebSocket | None

	def __init__( self, api_key: str, timeout: int=5 ) -> None:
		'''

			Purpose:
			--------
			Initialize AIS Stream server-side WebSocket access.

			Parameters:
			-----------
			api_key (str): AIS Stream API key.
			timeout (int): WebSocket connection and receive timeout in seconds.

			Returns:
			--------
			None

		'''
		throw_if( 'api_key', api_key )
		self.api_key = api_key
		self.timeout = timeout
		self.url = 'wss://stream.aisstream.io/v0/stream'
		self.socket = None

	def fetch_positions( self, latitude: float, longitude: float,
			radius_degrees: float=2.0, max_messages: int=100,
			duration_seconds: float=3.0 ) -> List[ Dict[ str, Any ] ]:
		'''

			Purpose:
			--------
			Collect a bounded sample of live AIS vessel position messages around a geographic
			center point.

			Parameters:
			-----------
			latitude (float): Bounding-box center latitude.
			longitude (float): Bounding-box center longitude.
			radius_degrees (float): Decimal-degree half-width of the bounding box.
			max_messages (int): Maximum matching AIS messages returned.
			duration_seconds (float): Maximum receive window in seconds.

			Returns:
			--------
			List[Dict[str, Any]]: AIS Stream message envelopes containing vessel positions.

		'''
		throw_if( 'latitude', latitude )
		throw_if( 'longitude', longitude )
		throw_if( 'radius_degrees', radius_degrees )
		throw_if( 'max_messages', max_messages )
		throw_if( 'duration_seconds', duration_seconds )
		self.latitude = float( latitude )
		self.longitude = float( longitude )
		self.radius_degrees = float( radius_degrees )
		self.max_messages = int( max_messages )
		self.duration_seconds = float( duration_seconds )
		self.north = min( 90.0, self.latitude + self.radius_degrees )
		self.south = max( -90.0, self.latitude - self.radius_degrees )
		self.west = max( -180.0, self.longitude - self.radius_degrees )
		self.east = min( 180.0, self.longitude + self.radius_degrees )
		self.subscription = {
			'APIKey': self.api_key,
			'BoundingBoxes': [ [ [ self.north, self.west ], [ self.south, self.east ] ] ],
			'FilterMessageTypes': [
				'PositionReport',
				'StandardClassBPositionReport',
				'ExtendedClassBPositionReport',
				'LongRangeAisBroadcastMessage',
			],
		}
		messages: List[ Dict[ str, Any ] ] = [ ]
		self.socket = create_connection( self.url, timeout=self.timeout )
		self.socket.send( json.dumps( self.subscription ) )
		started = time.monotonic( )

		try:
			while len( messages ) < self.max_messages:
				elapsed = time.monotonic( ) - started
				remaining = self.duration_seconds - elapsed
				if remaining <= 0.0:
					break

				self.socket.settimeout( min( 1.0, max( 0.1, remaining ) ) )
				try:
					frame = self.socket.recv( )
				except WebSocketTimeoutException:
					continue

				if isinstance( frame, bytes ):
					frame = frame.decode( 'utf-8' )
				payload = json.loads( frame )
				if not isinstance( payload, dict ):
					continue
				if payload.get( 'MessageType' ) == 'SubscriptionConfirmation':
					continue
				metadata = payload.get( 'MetaData', { } ) or { }
				if metadata.get( 'Latitude' ) is None or metadata.get( 'Longitude' ) is None:
					continue
				messages.append( payload )

		finally:
			if self.socket is not None:
				self.socket.close( )
				self.socket = None

		return messages


class CelesTrakLive:
	'''

		Purpose:
		--------
		Retrieve current CelesTrak OMM records and propagate them to current Earth-fixed
		latitude, longitude, and altitude values using SGP4.

	'''
	timeout: int
	url: str
	response: Response | None

	def __init__( self, timeout: int=20 ) -> None:
		'''

			Purpose:
			--------
			Initialize current CelesTrak GP-data access.

			Parameters:
			-----------
			timeout (int): HTTP timeout in seconds.

			Returns:
			--------
			None

		'''
		self.timeout = timeout
		self.url = 'https://celestrak.org/NORAD/elements/gp.php'
		self.response = None

	def fetch_group( self, group: str, limit: int=250 ) -> List[ Dict[ str, Any ] ]:
		'''

			Purpose:
			--------
			Retrieve current general-perturbation records for one CelesTrak satellite group
			in OMM JSON format.

			Parameters:
			-----------
			group (str): CelesTrak group identifier such as stations, visual, weather,
				gps-ops, or active.
			limit (int): Maximum records returned to the caller.

			Returns:
			--------
			List[Dict[str, Any]]: OMM records.

		'''
		throw_if( 'group', group )
		throw_if( 'limit', limit )
		self.group = group
		self.limit = int( limit )
		self.params = { 'GROUP': self.group, 'FORMAT': 'JSON' }
		self.response = requests.get( self.url, params=self.params, timeout=self.timeout )
		self.response.raise_for_status( )
		payload = self.response.json( ) or [ ]
		if not isinstance( payload, list ):
			raise TypeError( 'CelesTrak GP JSON response must be a list.' )
		return payload[ :self.limit ]

	def propagate( self, record: Dict[ str, Any ],
			when: dt.datetime ) -> Dict[ str, Any ]:
		'''

			Purpose:
			--------
			Propagate one OMM record to the requested UTC time and transform its TEME
			position into Earth-fixed geodetic coordinates.

			Parameters:
			-----------
			record (Dict[str, Any]): CelesTrak OMM record.
			when (datetime): UTC propagation time.

			Returns:
			--------
			Dict[str, Any]: Propagated latitude, longitude, altitude, velocity, and identity.

		'''
		throw_if( 'record', record )
		throw_if( 'when', when )
		self.record = record
		self.when = when
		self.satellite = Satrec( )
		omm.initialize( self.satellite, self.record )
		self.obstime = Time( self.when )
		error, position, velocity = self.satellite.sgp4(
			self.obstime.jd1, self.obstime.jd2 )
		if error != 0:
			raise RuntimeError( f'SGP4 propagation failed with error code {error}.' )

		self.teme = TEME(
			CartesianRepresentation( position[ 0 ] * u.km, position[ 1 ] * u.km,
				position[ 2 ] * u.km ),
			obstime=self.obstime )
		self.itrs = self.teme.transform_to( ITRS( obstime=self.obstime ) )
		self.location = EarthLocation.from_geocentric(
			self.itrs.cartesian.x, self.itrs.cartesian.y, self.itrs.cartesian.z )
		self.speed = math.sqrt(
			float( velocity[ 0 ] ) ** 2
			+ float( velocity[ 1 ] ) ** 2
			+ float( velocity[ 2 ] ) ** 2 )

		return {
			'Name': str( self.record.get( 'OBJECT_NAME', '' ) or '' ),
			'CatalogNumber': str( self.record.get( 'NORAD_CAT_ID', '' ) or '' ),
			'ObjectId': str( self.record.get( 'OBJECT_ID', '' ) or '' ),
			'Latitude': float( self.location.lat.deg ),
			'Longitude': float( self.location.lon.deg ),
			'Altitude': float( self.location.height.to( u.km ).value ),
			'Velocity': float( self.speed ),
			'Epoch': str( self.record.get( 'EPOCH', '' ) or '' ),
			'Classification': str( self.record.get( 'CLASSIFICATION_TYPE', '' ) or '' ),
		}


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

