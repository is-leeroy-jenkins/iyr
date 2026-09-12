'''
******************************************************************************************
 Assembly:                iyr
 Filename:                live_world.py
 Author:                  Terry D. Eppler / Assistant
 Created:                 09-12-2026
******************************************************************************************

Purpose:
    Live World Data state and sidebar controls inspired by God's Eye View while preserving
    Iyr's existing GIS modes and execution paths.
******************************************************************************************
'''

from __future__ import annotations

from typing import Dict

import streamlit as st


LIVE_WORLD_LAYERS: Dict[ str, str ] = {
	'aircraft': '✈️ Aircraft (Live)',
	'military_aircraft': '🛩️ Military Aircraft',
	'vessels': '🚢 Vessels & Ships',
	'satellites': '🛰️ Satellites',
	'earthquakes': '📈 Earthquakes',
	'fires': '🔥 Fires (Wildfires)',
	'cameras': '📷 CCTV / Web Cameras',
	'infrastructure': '📡 Infrastructure (Airports, Ports, etc.)',
	'tracking': '🎯 Tracking & Trails',
	'measurements': '📏 Measurements & Annotations',
	'map_layers': '🗺️ Additional Map Layers',
}

AI_ADVANCED_TOOLS: Dict[ str, str ] = {
	'cross_layer_analysis': '🧭 Cross-Layer Analysis',
	'geofencing': '🛡️ Geofencing',
	'agent_tools': '🤖 Agent Tools',
	'historical_replay': '🕓 Historical Replay',
}


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
		Initialize isolated Live World Data session-state values without modifying Iyr mode state.

		Parameters:
		-----------
		None

		Returns:
		--------
		None

	'''
	defaults = {
		'live_world_enabled': False,
		'live_world_layer': '',
		'live_world_tool': '',
	}

	for key in LIVE_WORLD_LAYERS:
		defaults[ f'live_world_{key}' ] = False

	for key in AI_ADVANCED_TOOLS:
		defaults[ f'live_world_{key}' ] = False

	for key, value in defaults.items( ):
		if key not in st.session_state:
			st.session_state[ key ] = value


def get_live_world_layers( ) -> Dict[ str, bool ]:
	'''

		Purpose:
		--------
		Return the current enabled state for every Live World Data layer.

		Parameters:
		-----------
		None

		Returns:
		--------
		Dict[str, bool]: Live World Data layer states keyed by layer identifier.

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
		Render Live World Data controls in an isolated sidebar expander directly below Iyr's
		existing Mode expander.

		Parameters:
		-----------
		None

		Returns:
		--------
		None

	'''
	initialize_live_world_state( )

	with st.expander( '🌐 Live World Data (God\'s Eye View)', expanded=False ):
		st.caption( 'Live Layers & Tools' )

		for key, label in LIVE_WORLD_LAYERS.items( ):
			st.checkbox( label, key=f'live_world_{key}' )

		st.divider( )

		with st.expander( 'AI & Advanced Tools', expanded=False ):
			for key, label in AI_ADVANCED_TOOLS.items( ):
				st.checkbox( label, key=f'live_world_{key}' )
