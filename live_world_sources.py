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
    Provider clients used by Iyr Live World Data for real-time aircraft state vectors and
    current satellite orbital elements. OpenSky access uses the current OAuth2 client
    credentials flow when API-client credentials are available. CelesTrak data is requested
    in OMM JSON format and propagated with SGP4 before conversion to Earth-fixed coordinates.
******************************************************************************************
'''

from __future__ import annotations

import datetime as dt
import math
from typing import Any, Dict, List

import requests
from astropy import units as u
from astropy.coordinates import CartesianRepresentation, EarthLocation, ITRS, TEME
from astropy.time import Time
from requests import Response
from sgp4 import omm
from sgp4.api import Satrec


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
