'''
  ******************************************************************************************
      Assembly:                Iyr
      Filename:                document_processing.py
      Author:                  Terry D. Eppler
      Created:                 09-08-2026
      Last Modified By:        Terry D. Eppler
      Last Modified On:        09-08-2026
  ******************************************************************************************
  <summary>
    Foo-style web, API-result, chunking, embedding, and vector-storage UI.
  </summary>
  ******************************************************************************************
'''
from __future__ import annotations

import json
import math
import os
from typing import Dict, List

import pandas as pd
import streamlit as st
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config as cfg
from embedders import EmbeddingFactory
from fetchers import WebFetcher
from stores.vector import ChromaStore, PineconeStore


EMBEDDING_MODELS: Dict[ str, List[ str ] ] = {
	'OpenAI': [ 'text-embedding-3-small', 'text-embedding-3-large' ],
	'Google Generative AI': [ 'gemini-embedding-2-preview' ],
	'Mistral AI': [ 'mistral-embed' ],
	'Hugging Face': [
		'sentence-transformers/all-MiniLM-L6-v2',
		'sentence-transformers/all-mpnet-base-v2' ],
	'Local GGUF': [ 'Local GGUF' ],
}


def throw_if( name: str, value: object ) -> None:
	"""Validate a required runtime value."""
	if value is None:
		raise ValueError( f'Argument "{name}" cannot be empty!' )
	if isinstance( value, str ) and not value.strip( ):
		raise ValueError( f'Argument "{name}" cannot be empty!' )
	if isinstance( value, ( list, tuple, dict, set ) ) and len( value ) == 0:
		raise ValueError( f'Argument "{name}" cannot be empty!' )


def render_processing_inputs( key_prefix: str, collection_name: str ) -> Dict[ str, object ]:
	"""Render Foo-style chunking, embedding, and vector-storage controls."""
	throw_if( 'key_prefix', key_prefix )
	throw_if( 'collection_name', collection_name )

	chunk_col, overlap_col = st.columns( 2 )
	with chunk_col:
		chunk_size = st.slider( 'Chunk Size', min_value=100, max_value=4000, value=1000,
			step=100, key=f'{key_prefix}_chunk_size' )
	with overlap_col:
		chunk_overlap = st.slider( 'Chunk Overlap', min_value=0,
			max_value=min( 1000, int( chunk_size ) - 1 ),
			value=min( 200, int( chunk_size ) - 1 ), step=50,
			key=f'{key_prefix}_chunk_overlap' )

	provider_col, model_col = st.columns( 2 )
	with provider_col:
		provider = st.selectbox( 'Embedding Provider', options=list( EMBEDDING_MODELS.keys( ) ),
			index=list( EMBEDDING_MODELS.keys( ) ).index( 'Hugging Face' ),
			key=f'{key_prefix}_embedding_provider' )
	with model_col:
		model = st.selectbox( 'Embedding Model', options=EMBEDDING_MODELS[ provider ],
			key=f'{key_prefix}_embedding_model' )

	model_path = ''
	if provider == 'Local GGUF':
		model_path = st.text_input( 'Local GGUF Model Path',
			placeholder=r'C:\models\embedding-model.gguf',
			key=f'{key_prefix}_embedding_model_path' )

	store_col, target_col = st.columns( 2 )
	with store_col:
		vector_backend = st.selectbox( 'Vector Store', options=[ 'Chroma', 'Pinecone' ],
			key=f'{key_prefix}_vector_backend' )
	with target_col:
		if vector_backend == 'Chroma':
			vector_target = st.text_input( 'Collection Name', value=collection_name,
				key=f'{key_prefix}_chroma_collection' )
		else:
			vector_target = st.text_input( 'Index Name', value='',
				key=f'{key_prefix}_pinecone_index' )

	if vector_backend == 'Chroma':
		persist_directory = st.text_input( 'Persistence Directory', value='stores/chroma',
			key=f'{key_prefix}_chroma_directory' )
		namespace = ''
	else:
		persist_directory = ''
		namespace = st.text_input( 'Namespace', value='',
			key=f'{key_prefix}_pinecone_namespace' )

	return {
		'chunk_size': int( chunk_size ),
		'chunk_overlap': int( chunk_overlap ),
		'provider': provider,
		'model': model,
		'model_path': model_path,
		'vector_backend': vector_backend,
		'vector_target': vector_target,
		'persist_directory': persist_directory,
		'namespace': namespace,
	}


def chunk_documents( documents: List[ Document ], chunk_size: int,
	chunk_overlap: int ) -> List[ Document ]:
	"""Split LangChain documents into retrieval chunks."""
	throw_if( 'documents', documents )
	if chunk_overlap >= chunk_size:
		raise ValueError( 'Chunk Overlap must be smaller than Chunk Size.' )

	splitter = RecursiveCharacterTextSplitter(
		chunk_size=int( chunk_size ), chunk_overlap=int( chunk_overlap ) )
	chunks = splitter.split_documents( documents )
	for index, document in enumerate( chunks, start=1 ):
		document.metadata = dict( document.metadata or { } )
		document.metadata[ 'chunk_id' ] = f'chunk-{index:06d}'
	return chunks


def create_embeddings( chunks: List[ Document ], provider: str, model: str,
	model_path: str ) -> tuple[ object, List[ List[ float ] ] ]:
	"""Create and validate embeddings for document chunks."""
	throw_if( 'chunks', chunks )
	factory = EmbeddingFactory( )
	embedder = factory.create( provider, model, model_path )
	vectors = embedder.embed_documents( [ document.page_content for document in chunks ] )
	if len( vectors ) != len( chunks ):
		raise RuntimeError( 'Embedding count does not match the chunk count.' )
	dimensions = { len( vector ) for vector in vectors }
	if len( dimensions ) != 1:
		raise RuntimeError( 'Embedding vectors do not have a consistent dimension.' )
	if not all( math.isfinite( float( value ) ) for vector in vectors for value in vector ):
		raise RuntimeError( 'Embedding vectors contain non-finite values.' )
	return embedder, vectors


def store_documents( chunks: List[ Document ], embedder: object, vector_backend: str,
	vector_target: str, persist_directory: str, namespace: str ) -> object:
	"""Persist document chunks to Chroma or Pinecone."""
	throw_if( 'chunks', chunks )
	throw_if( 'embedder', embedder )
	throw_if( 'vector_backend', vector_backend )
	throw_if( 'vector_target', vector_target )
	if vector_backend == 'Chroma':
		store = ChromaStore( )
		return store.create( chunks, embedder, vector_target, persist_directory )

	api_key = getattr( cfg, 'PINECONE_API_KEY', '' ) or os.getenv( 'PINECONE_API_KEY', '' )
	store = PineconeStore( )
	return store.create( chunks, embedder, vector_target, namespace, api_key )


def initialize_mode_document_state( prefix: str ) -> None:
	"""Initialize isolated document state for one API mode."""
	throw_if( 'prefix', prefix )
	defaults = {
		f'{prefix}_documents': [ ],
		f'{prefix}_chunks': [ ],
		f'{prefix}_embeddings': [ ],
		f'{prefix}_embedder': None,
		f'{prefix}_vector_store': None,
		f'{prefix}_document_signature': '',
		f'{prefix}_chunk_size_used': 0,
		f'{prefix}_chunk_overlap_used': 0,
		f'{prefix}_embedding_provider_used': '',
		f'{prefix}_embedding_model_used': '',
		f'{prefix}_embedding_model_path_used': '',
	}
	for key, value in defaults.items( ):
		if key not in st.session_state:
			st.session_state[ key ] = value


def serialize_mode_result( result: object ) -> str:
	"""Serialize a structured API result as LangChain document text."""
	if isinstance( result, pd.DataFrame ):
		return result.to_json( orient='records', indent=2, default_handler=str )
	if isinstance( result, str ):
		return result
	return json.dumps( result, indent=2, sort_keys=True, default=str )


def sync_mode_document( prefix: str, result_key: str, source_key: str ) -> None:
	"""Synchronize the latest API result into a LangChain Document."""
	initialize_mode_document_state( prefix )
	result = st.session_state.get( result_key )
	if result is None or result == { } or result == [ ] or result == '':
		return

	text = serialize_mode_result( result )
	source = str( st.session_state.get( source_key, '' ) or prefix.title( ) )
	signature = f'{source}\n{text}'
	if signature == st.session_state[ f'{prefix}_document_signature' ]:
		return

	st.session_state[ f'{prefix}_documents' ] = [
		Document( page_content=text, metadata={ 'source': source, 'mode': prefix } ) ]
	st.session_state[ f'{prefix}_chunks' ] = [ ]
	st.session_state[ f'{prefix}_embeddings' ] = [ ]
	st.session_state[ f'{prefix}_embedder' ] = None
	st.session_state[ f'{prefix}_vector_store' ] = None
	st.session_state[ f'{prefix}_document_signature' ] = signature


def render_source_processing_controls( prefix: str, result_key: str, source_key: str,
	source_name: str, key_prefix: str ) -> None:
	"""Render Foo-style processing controls inside one source/API expander."""
	throw_if( 'prefix', prefix )
	throw_if( 'result_key', result_key )
	throw_if( 'source_key', source_key )
	throw_if( 'source_name', source_name )
	throw_if( 'key_prefix', key_prefix )
	initialize_mode_document_state( prefix )

	active_source = str( st.session_state.get( source_key, '' ) or '' )
	if active_source == source_name:
		sync_mode_document( prefix, result_key, source_key )

	settings = render_processing_inputs( key_prefix, f'iyr-{prefix}-documents' )
	chunk_col, embed_col, store_col = st.columns( 3 )
	chunk_run = chunk_col.button( 'Chunk', icon='✂️', key=f'{key_prefix}_chunk_run',
		use_container_width=True )
	embed_run = embed_col.button( 'Embed', icon='🧬', key=f'{key_prefix}_embed_run',
		use_container_width=True )
	store_run = store_col.button( 'Store', icon='🗄️', key=f'{key_prefix}_store_run',
		use_container_width=True )

	if chunk_run:
		if active_source != source_name:
			st.warning( f'Run {source_name} before chunking.' )
		else:
			try:
				documents = st.session_state[ f'{prefix}_documents' ]
				chunks = chunk_documents( documents, settings[ 'chunk_size' ],
					settings[ 'chunk_overlap' ] )
				st.session_state[ f'{prefix}_chunks' ] = chunks
				st.session_state[ f'{prefix}_chunk_size_used' ] = settings[ 'chunk_size' ]
				st.session_state[ f'{prefix}_chunk_overlap_used' ] = settings[ 'chunk_overlap' ]
				st.session_state[ f'{prefix}_embeddings' ] = [ ]
				st.session_state[ f'{prefix}_embedder' ] = None
				st.session_state[ f'{prefix}_vector_store' ] = None
				st.success( f'Created {len( chunks ):,} chunk(s).' )
			except Exception as exc:
				st.error( str( exc ) )

	if embed_run:
		chunks = st.session_state[ f'{prefix}_chunks' ]
		if active_source != source_name:
			st.warning( f'Run and chunk {source_name} before embedding.' )
		elif not chunks:
			st.warning( 'Chunk the loaded result before embedding.' )
		elif settings[ 'chunk_size' ] != st.session_state[ f'{prefix}_chunk_size_used' ] or \
				settings[ 'chunk_overlap' ] != st.session_state[ f'{prefix}_chunk_overlap_used' ]:
			st.warning( 'Chunk settings changed. Run Chunk again before embedding.' )
		else:
			try:
				embedder, vectors = create_embeddings( chunks, settings[ 'provider' ],
					settings[ 'model' ], settings[ 'model_path' ] )
				st.session_state[ f'{prefix}_embedder' ] = embedder
				st.session_state[ f'{prefix}_embeddings' ] = vectors
				st.session_state[ f'{prefix}_embedding_provider_used' ] = settings[ 'provider' ]
				st.session_state[ f'{prefix}_embedding_model_used' ] = settings[ 'model' ]
				st.session_state[ f'{prefix}_embedding_model_path_used' ] = settings[ 'model_path' ]
				st.session_state[ f'{prefix}_vector_store' ] = None
				st.success( f'Created {len( vectors ):,} embedding vector(s).' )
			except Exception as exc:
				st.error( str( exc ) )

	if store_run:
		chunks = st.session_state[ f'{prefix}_chunks' ]
		embedder = st.session_state[ f'{prefix}_embedder' ]
		if active_source != source_name:
			st.warning( f'Run, chunk, and embed {source_name} before storing.' )
		elif not chunks or embedder is None:
			st.warning( 'Create embeddings before storing vectors.' )
		elif settings[ 'provider' ] != st.session_state[ f'{prefix}_embedding_provider_used' ] or \
				settings[ 'model' ] != st.session_state[ f'{prefix}_embedding_model_used' ] or \
				settings[ 'model_path' ] != st.session_state[ f'{prefix}_embedding_model_path_used' ]:
			st.warning( 'Embedding settings changed. Run Embed again before storing.' )
		else:
			try:
				st.session_state[ f'{prefix}_vector_store' ] = store_documents(
					chunks, embedder, settings[ 'vector_backend' ], settings[ 'vector_target' ],
					settings[ 'persist_directory' ], settings[ 'namespace' ] )
				st.success( f"Stored {len( chunks ):,} chunk(s) in {settings[ 'vector_backend' ]}." )
			except Exception as exc:
				st.error( str( exc ) )


def render_mode_document_tabs( prefix: str, loaded_label: str = '📄 Loaded' ) -> None:
	"""Render Loaded, Chunks, and Embeddings tabs for one API mode."""
	initialize_mode_document_state( prefix )
	loaded_tab, chunks_tab, embeddings_tab = st.tabs(
		[ loaded_label, '✂️ Chunks', '🧠 Embeddings' ] )

	with loaded_tab:
		documents = st.session_state[ f'{prefix}_documents' ]
		if not documents:
			st.info( 'Run a source request to load a document.' )
		else:
			rows = [ {
				'Document': index,
				'Source': ( document.metadata or { } ).get( 'source', '' ),
				'Characters': len( document.page_content ),
				'Metadata': document.metadata or { },
				'Text': document.page_content,
			} for index, document in enumerate( documents, start=1 ) ]
			st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )

	with chunks_tab:
		chunks = st.session_state[ f'{prefix}_chunks' ]
		if not chunks:
			st.info( 'Run Chunk to display document chunks.' )
		else:
			rows = [ {
				'Chunk': index,
				'Chunk ID': ( document.metadata or { } ).get( 'chunk_id', '' ),
				'Source': ( document.metadata or { } ).get( 'source', '' ),
				'Characters': len( document.page_content ),
				'Text': document.page_content,
			} for index, document in enumerate( chunks, start=1 ) ]
			st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )

	with embeddings_tab:
		vectors = st.session_state[ f'{prefix}_embeddings' ]
		chunks = st.session_state[ f'{prefix}_chunks' ]
		if not vectors:
			st.info( 'Run Embed to display embedding vectors.' )
		else:
			rows = [ ]
			for index, vector in enumerate( vectors ):
				document = chunks[ index ]
				rows.append( {
					'Chunk': index + 1,
					'Provider': st.session_state[ f'{prefix}_embedding_provider_used' ],
					'Model': st.session_state[ f'{prefix}_embedding_model_path_used' ] or
						st.session_state[ f'{prefix}_embedding_model_used' ],
					'Dimensions': len( vector ),
					'Source': ( document.metadata or { } ).get( 'source', '' ),
					'Text': document.page_content,
					'Vector': vector,
				} )
			st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )


def initialize_web_state( ) -> None:
	"""Initialize isolated web-document state."""
	defaults = {
		'web_documents': [ ],
		'web_document_url': '',
		'web_chunks': [ ],
		'web_embeddings': [ ],
		'web_embedder': None,
		'web_vector_store': None,
		'web_chunk_size_used': 0,
		'web_chunk_overlap_used': 0,
		'web_embedding_provider_used': '',
		'web_embedding_model_used': '',
		'web_embedding_model_path_used': '',
	}
	for key, value in defaults.items( ):
		if key not in st.session_state:
			st.session_state[ key ] = value


def clear_web_state( ) -> None:
	"""Clear scraped documents and all derived web state."""
	initialize_web_state( )
	st.session_state[ 'web_documents' ] = [ ]
	st.session_state[ 'web_document_url' ] = ''
	st.session_state[ 'web_chunks' ] = [ ]
	st.session_state[ 'web_embeddings' ] = [ ]
	st.session_state[ 'web_embedder' ] = None
	st.session_state[ 'web_vector_store' ] = None
	st.session_state[ 'web_chunk_size_used' ] = 0
	st.session_state[ 'web_chunk_overlap_used' ] = 0
	st.session_state[ 'web_embedding_provider_used' ] = ''
	st.session_state[ 'web_embedding_model_used' ] = ''
	st.session_state[ 'web_embedding_model_path_used' ] = ''


def render_web_document_processing( ) -> None:
	"""Render Foo-style Site Crawler document processing."""
	initialize_web_state( )
	st.subheader( '🕷️ Site Crawler' )
	st.divider( )
	left, right = st.columns( [ 0.4, 0.6 ], gap='xxsmall', border=True )

	with left:
		with st.expander( label='Web Processing', icon='🌐', expanded=True ):
			target_url = st.text_input( 'Target URL', placeholder='https://example.com',
				key='web_document_url_input' )
			request_timeout = st.slider( 'Request Timeout', min_value=1, max_value=120,
				value=10, step=1, key='web_document_timeout' )
			fetch_col, clear_col = st.columns( 2 )
			fetch_run = fetch_col.button( 'Fetch', icon='🌐', key='web_document_fetch',
				use_container_width=True )
			clear_run = clear_col.button( 'Clear', icon='🧹', key='web_document_clear',
				use_container_width=True )

			if clear_run:
				clear_web_state( )
				st.rerun( )

			if fetch_run:
				try:
					throw_if( 'target_url', target_url )
					fetcher = WebFetcher( )
					documents = fetcher.fetch( target_url.strip( ), time=int( request_timeout ) )
					throw_if( 'documents', documents )
					st.session_state[ 'web_documents' ] = documents
					st.session_state[ 'web_document_url' ] = target_url.strip( )
					st.session_state[ 'web_chunks' ] = [ ]
					st.session_state[ 'web_embeddings' ] = [ ]
					st.session_state[ 'web_embedder' ] = None
					st.session_state[ 'web_vector_store' ] = None
					st.success( f'Scraped {len( documents ):,} LangChain document(s).' )
				except Exception as exc:
					st.error( str( exc ) )

			settings = render_processing_inputs( 'web', 'iyr-web-documents' )
			chunk_col, embed_col, store_col = st.columns( 3 )
			chunk_run = chunk_col.button( 'Chunk', icon='✂️', key='web_chunk_run',
				use_container_width=True )
			embed_run = embed_col.button( 'Embed', icon='🧬', key='web_embed_run',
				use_container_width=True )
			store_run = store_col.button( 'Store', icon='🗄️', key='web_store_run',
				use_container_width=True )

			if chunk_run:
				if not st.session_state[ 'web_documents' ]:
					st.warning( 'Fetch a URL before chunking.' )
				else:
					try:
						chunks = chunk_documents( st.session_state[ 'web_documents' ],
							settings[ 'chunk_size' ], settings[ 'chunk_overlap' ] )
						st.session_state[ 'web_chunks' ] = chunks
						st.session_state[ 'web_chunk_size_used' ] = settings[ 'chunk_size' ]
						st.session_state[ 'web_chunk_overlap_used' ] = settings[ 'chunk_overlap' ]
						st.session_state[ 'web_embeddings' ] = [ ]
						st.session_state[ 'web_embedder' ] = None
						st.session_state[ 'web_vector_store' ] = None
						st.success( f'Created {len( chunks ):,} chunk(s).' )
					except Exception as exc:
						st.error( str( exc ) )

			if embed_run:
				chunks = st.session_state[ 'web_chunks' ]
				if not chunks:
					st.warning( 'Chunk the scraped document before embedding.' )
				elif settings[ 'chunk_size' ] != st.session_state[ 'web_chunk_size_used' ] or \
						settings[ 'chunk_overlap' ] != st.session_state[ 'web_chunk_overlap_used' ]:
					st.warning( 'Chunk settings changed. Run Chunk again before embedding.' )
				else:
					try:
						embedder, vectors = create_embeddings( chunks, settings[ 'provider' ],
							settings[ 'model' ], settings[ 'model_path' ] )
						st.session_state[ 'web_embedder' ] = embedder
						st.session_state[ 'web_embeddings' ] = vectors
						st.session_state[ 'web_embedding_provider_used' ] = settings[ 'provider' ]
						st.session_state[ 'web_embedding_model_used' ] = settings[ 'model' ]
						st.session_state[ 'web_embedding_model_path_used' ] = settings[ 'model_path' ]
						st.session_state[ 'web_vector_store' ] = None
						st.success( f'Created {len( vectors ):,} embedding vector(s).' )
					except Exception as exc:
						st.error( str( exc ) )

			if store_run:
				embedder = st.session_state[ 'web_embedder' ]
				chunks = st.session_state[ 'web_chunks' ]
				if not chunks or embedder is None:
					st.warning( 'Create embeddings before storing vectors.' )
				elif settings[ 'provider' ] != st.session_state[ 'web_embedding_provider_used' ] or \
						settings[ 'model' ] != st.session_state[ 'web_embedding_model_used' ] or \
						settings[ 'model_path' ] != st.session_state[ 'web_embedding_model_path_used' ]:
					st.warning( 'Embedding settings changed. Run Embed again before storing.' )
				else:
					try:
						st.session_state[ 'web_vector_store' ] = store_documents(
							chunks, embedder, settings[ 'vector_backend' ], settings[ 'vector_target' ],
							settings[ 'persist_directory' ], settings[ 'namespace' ] )
						st.success( f"Stored {len( chunks ):,} chunk(s) in {settings[ 'vector_backend' ]}." )
					except Exception as exc:
						st.error( str( exc ) )

	with right:
		loaded_tab, chunks_tab, embeddings_tab = st.tabs(
			[ '🌐 Scraped', '✂️ Chunks', '🧠 Embeddings' ] )
		with loaded_tab:
			documents = st.session_state[ 'web_documents' ]
			if not documents:
				st.info( 'Fetch a URL to load a LangChain document.' )
			else:
				rows = [ {
					'Document': index,
					'Source': ( document.metadata or { } ).get( 'source', '' ),
					'Characters': len( document.page_content ),
					'Metadata': document.metadata or { },
					'Text': document.page_content,
				} for index, document in enumerate( documents, start=1 ) ]
				st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
		with chunks_tab:
			chunks = st.session_state[ 'web_chunks' ]
			if not chunks:
				st.info( 'Run Chunk to display scraped document chunks.' )
			else:
				rows = [ {
					'Chunk': index,
					'Chunk ID': ( document.metadata or { } ).get( 'chunk_id', '' ),
					'Source': ( document.metadata or { } ).get( 'source', '' ),
					'Characters': len( document.page_content ),
					'Text': document.page_content,
				} for index, document in enumerate( chunks, start=1 ) ]
				st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )
		with embeddings_tab:
			vectors = st.session_state[ 'web_embeddings' ]
			chunks = st.session_state[ 'web_chunks' ]
			if not vectors:
				st.info( 'Run Embed to display embedding vectors.' )
			else:
				rows = [ ]
				for index, vector in enumerate( vectors ):
					document = chunks[ index ]
					rows.append( {
						'Chunk': index + 1,
						'Provider': st.session_state[ 'web_embedding_provider_used' ],
						'Model': st.session_state[ 'web_embedding_model_path_used' ] or
							st.session_state[ 'web_embedding_model_used' ],
						'Dimensions': len( vector ),
						'Source': ( document.metadata or { } ).get( 'source', '' ),
						'Text': document.page_content,
						'Vector': vector,
					} )
				st.dataframe( pd.DataFrame( rows ), use_container_width=True, hide_index=True )