'''
******************************************************************************************
 Assembly:                iyr
 Filename:                history.py
 Author:                  Terry D. Eppler / Assistant
 Created:                 09-12-2026

 Last Modified By:        Terry D. Eppler / Assistant
 Last Modified On:        09-12-2026
******************************************************************************************

Purpose:
    SQLite-backed persistence and retrieval for normalized Live World observations. The
    module stores explicit Live World refresh snapshots in Iyr's existing SQLite database
    and provides bounded historical queries used by Historical Replay.
******************************************************************************************
'''

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path
from typing import Dict, List

import pandas as pd

import config as cfg


HISTORY_TABLE = 'LiveWorldHistory'
HISTORY_COLUMNS: List[ str ] = [
    'RefreshId', 'ObservedAt', 'EntityId', 'EntityType', 'Name', 'Latitude', 'Longitude',
    'Altitude', 'Heading', 'Speed', 'Timestamp', 'Source', 'Metadata' ]


def throw_if( name: str, value: object ) -> None:
    '''

        Purpose:
        --------
        Validate that a required argument is not empty.

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


def initialize_live_world_history( ) -> None:
    '''

        Purpose:
        --------
        Create the Live World history table and supporting indexes when they do not exist.

        Returns:
        --------
        None

    '''
    database_path = Path( cfg.DB_PATH )
    database_path.parent.mkdir( parents=True, exist_ok=True )
    with sqlite3.connect( database_path ) as conn:
        conn.execute( f'''
            CREATE TABLE IF NOT EXISTS {HISTORY_TABLE} (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                RefreshId TEXT NOT NULL,
                ObservedAt TEXT NOT NULL,
                EntityId TEXT NOT NULL,
                EntityType TEXT NOT NULL,
                Name TEXT NOT NULL,
                Latitude REAL NOT NULL,
                Longitude REAL NOT NULL,
                Altitude REAL,
                Heading REAL,
                Speed REAL,
                Timestamp TEXT,
                Source TEXT NOT NULL,
                Metadata TEXT,
                UNIQUE (RefreshId, EntityType, EntityId)
            )
        ''' )
        conn.execute( f'''
            CREATE INDEX IF NOT EXISTS IX_{HISTORY_TABLE}_ObservedAt
            ON {HISTORY_TABLE} (ObservedAt)
        ''' )
        conn.execute( f'''
            CREATE INDEX IF NOT EXISTS IX_{HISTORY_TABLE}_Entity
            ON {HISTORY_TABLE} (EntityType, EntityId, ObservedAt)
        ''' )


def persist_live_world_history( df_entities: pd.DataFrame, refresh_id: str,
        observed_at: str ) -> int:
    '''

        Purpose:
        --------
        Persist one normalized Live World refresh snapshot without duplicate observations.

        Parameters:
        -----------
        df_entities (pd.DataFrame): Normalized Live World entity frame.
        refresh_id (str): Stable identifier for the refresh snapshot.
        observed_at (str): UTC ISO timestamp for the refresh.

        Returns:
        --------
        int: Number of newly inserted observations.

    '''
    throw_if( 'df_entities', df_entities )
    throw_if( 'refresh_id', refresh_id )
    throw_if( 'observed_at', observed_at )
    initialize_live_world_history( )
    if df_entities.empty:
        return 0

    records: List[ tuple ] = [ ]
    for _, row in df_entities.iterrows( ):
        metadata = row.get( 'Metadata', { } )
        metadata_text = json.dumps( metadata if isinstance( metadata, dict ) else { },
            ensure_ascii=False, default=str )
        records.append( (
            refresh_id,
            observed_at,
            str( row.get( 'EntityId', '' ) ),
            str( row.get( 'EntityType', '' ) ),
            str( row.get( 'Name', '' ) ),
            float( row.get( 'Latitude', 0.0 ) ),
            float( row.get( 'Longitude', 0.0 ) ),
            float( row.get( 'Altitude', 0.0 ) ) if pd.notna( row.get( 'Altitude', 0.0 ) ) else None,
            float( row.get( 'Heading', 0.0 ) ) if pd.notna( row.get( 'Heading', 0.0 ) ) else None,
            float( row.get( 'Speed', 0.0 ) ) if pd.notna( row.get( 'Speed', 0.0 ) ) else None,
            str( row.get( 'Timestamp', '' ) ),
            str( row.get( 'Source', '' ) ),
            metadata_text,
        ) )

    with sqlite3.connect( cfg.DB_PATH ) as conn:
        before = conn.total_changes
        conn.executemany( f'''
            INSERT OR IGNORE INTO {HISTORY_TABLE} (
                RefreshId, ObservedAt, EntityId, EntityType, Name, Latitude, Longitude,
                Altitude, Heading, Speed, Timestamp, Source, Metadata )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', records )
        return conn.total_changes - before


def purge_live_world_history( retention_days: int ) -> int:
    '''

        Purpose:
        --------
        Delete persisted Live World observations older than the configured retention period.

        Parameters:
        -----------
        retention_days (int): Number of days of history to retain.

        Returns:
        --------
        int: Number of deleted observations.

    '''
    throw_if( 'retention_days', retention_days )
    if retention_days < 1:
        raise ValueError( 'Argument "retention_days" must be greater than zero.' )
    initialize_live_world_history( )
    cutoff = dt.datetime.now( dt.timezone.utc ) - dt.timedelta( days=retention_days )
    with sqlite3.connect( cfg.DB_PATH ) as conn:
        cursor = conn.execute( f'DELETE FROM {HISTORY_TABLE} WHERE ObservedAt < ?',
            (cutoff.isoformat( ),) )
        return int( cursor.rowcount if cursor.rowcount is not None else 0 )


def clear_live_world_history( ) -> int:
    '''

        Purpose:
        --------
        Delete all persisted Live World historical observations.

        Returns:
        --------
        int: Number of deleted observations.

    '''
    initialize_live_world_history( )
    with sqlite3.connect( cfg.DB_PATH ) as conn:
        cursor = conn.execute( f'DELETE FROM {HISTORY_TABLE}' )
        return int( cursor.rowcount if cursor.rowcount is not None else 0 )


def get_live_world_history_snapshots( hours: int=24 ) -> List[ str ]:
    '''

        Purpose:
        --------
        Return persisted refresh timestamps within a replay window, newest first.

        Parameters:
        -----------
        hours (int): Replay lookback window in hours; zero returns all persisted snapshots.

        Returns:
        --------
        List[str]: Persisted refresh timestamps.

    '''
    throw_if( 'hours', hours )
    if hours < 0:
        raise ValueError( 'Argument "hours" cannot be negative.' )
    initialize_live_world_history( )
    query = f'SELECT DISTINCT ObservedAt FROM {HISTORY_TABLE}'
    parameters: tuple = ( )
    if hours > 0:
        cutoff = dt.datetime.now( dt.timezone.utc ) - dt.timedelta( hours=hours )
        query += ' WHERE ObservedAt >= ?'
        parameters = (cutoff.isoformat( ),)
    query += ' ORDER BY ObservedAt DESC'
    with sqlite3.connect( cfg.DB_PATH ) as conn:
        return [ str( row[ 0 ] ) for row in conn.execute( query, parameters ).fetchall( ) ]


def load_live_world_history( hours: int, entity_types: List[ str ], snapshot: str,
        limit: int=5000 ) -> pd.DataFrame:
    '''

        Purpose:
        --------
        Load persisted observations through a selected replay snapshot.

        Parameters:
        -----------
        hours (int): Replay lookback window in hours; zero loads all retained history.
        entity_types (List[str]): Entity types to include.
        snapshot (str): Maximum replay timestamp to include.
        limit (int): Maximum number of historical observations returned.

        Returns:
        --------
        pd.DataFrame: Historical observations ordered chronologically.

    '''
    throw_if( 'hours', hours )
    throw_if( 'entity_types', entity_types )
    throw_if( 'snapshot', snapshot )
    throw_if( 'limit', limit )
    if hours < 0:
        raise ValueError( 'Argument "hours" cannot be negative.' )
    if limit < 1:
        raise ValueError( 'Argument "limit" must be greater than zero.' )
    if not entity_types:
        return pd.DataFrame( columns=HISTORY_COLUMNS )
    initialize_live_world_history( )

    placeholders = ','.join( '?' for _ in entity_types )
    clauses = [ f'EntityType IN ({placeholders})', 'ObservedAt <= ?' ]
    parameters: List[ object ] = list( entity_types ) + [ snapshot ]
    if hours > 0:
        cutoff = dt.datetime.now( dt.timezone.utc ) - dt.timedelta( hours=hours )
        clauses.append( 'ObservedAt >= ?' )
        parameters.append( cutoff.isoformat( ) )
    parameters.append( limit )
    query = f'''
        SELECT RefreshId, ObservedAt, EntityId, EntityType, Name, Latitude, Longitude,
            Altitude, Heading, Speed, Timestamp, Source, Metadata
        FROM {HISTORY_TABLE}
        WHERE {' AND '.join( clauses )}
        ORDER BY ObservedAt ASC, EntityType ASC, EntityId ASC
        LIMIT ?
    '''
    with sqlite3.connect( cfg.DB_PATH ) as conn:
        df_history = pd.read_sql_query( query, conn, params=parameters )
    if not df_history.empty:
        df_history[ 'Metadata' ] = df_history[ 'Metadata' ].apply(
            lambda value: json.loads( value ) if value else { } )
    return df_history


def get_live_world_history_summary( ) -> Dict[ str, object ]:
    '''

        Purpose:
        --------
        Return aggregate persistence statistics for the Historical Replay interface.

        Returns:
        --------
        Dict[str, object]: Observation count, snapshot count, and retained time bounds.

    '''
    initialize_live_world_history( )
    with sqlite3.connect( cfg.DB_PATH ) as conn:
        row = conn.execute( f'''
            SELECT COUNT(*), COUNT(DISTINCT RefreshId), MIN(ObservedAt), MAX(ObservedAt)
            FROM {HISTORY_TABLE}
        ''' ).fetchone( )
    return {
        'ObservationCount': int( row[ 0 ] or 0 ),
        'SnapshotCount': int( row[ 1 ] or 0 ),
        'FirstObservedAt': str( row[ 2 ] or '' ),
        'LastObservedAt': str( row[ 3 ] or '' ),
    }
