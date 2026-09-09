from __future__ import annotations

import re
from pathlib import Path


APP_PATH = Path( 'app.py' )
FETCHERS_PATH = Path( 'fetchers.py' )
REQUIREMENTS_PATH = Path( 'requirements.txt' )


def find_mode_block( text: str, mode_name: str ) -> tuple[ int, int ]:
	anchor = f"elif mode == '{mode_name}':"
	start = text.index( anchor )
	next_mode = text.find( '\nelif mode == ', start + len( anchor ) )
	end = len( text ) if next_mode < 0 else next_mode + 1
	return start, end


def slugify( value: str ) -> str:
	return re.sub( r'[^a-z0-9]+', '_', value.lower( ) ).strip( '_' )


def add_source_controls( block: str, prefix: str, result_key: str,
	source_key: str ) -> tuple[ str, int ]:
	lines = block.splitlines( keepends=True )
	insertions: list[ tuple[ int, list[ str ] ] ] = [ ]
	count = 0
	i = 0
	while i < len( lines ):
		match = re.match( r'^(\t+)with st\.expander\(', lines[ i ] )
		if not match:
			i += 1
			continue

		indent = match.group( 1 )
		indent_level = len( indent )
		end = i + 1
		while end < len( lines ):
			line = lines[ end ]
			if not line.strip( ):
				end += 1
				continue
			line_indent = len( line ) - len( line.lstrip( '\t' ) )
			if line_indent <= indent_level:
				break
			end += 1

		body = ''.join( lines[ i + 1:end ] ).replace( '\n', ' ' )
		matches = re.findall(
			rf"\[\s*'{re.escape( source_key )}'\s*\]\s*=\s*'([^']*)'",
			body )
		source_names = [ value for value in matches if value.strip( ) ]
		if source_names:
			source_name = source_names[ 0 ]
			key_prefix = f'{prefix}_{slugify( source_name )}'
			body_indent = indent + '\t'
			insertion = [
				f'{body_indent}st.divider( )\n',
				f"{body_indent}render_source_processing_controls( '{prefix}', '{result_key}', "
				f"'{source_key}', '{source_name}', '{key_prefix}' )\n",
			]
			insertions.append( ( end, insertion ) )
			count += 1
		i = end

	for index, insertion in reversed( insertions ):
		lines[ index:index ] = insertion
	return ''.join( lines ), count


def replace_right_pane( block: str, variable: str, prefix: str ) -> str:
	anchor = f'\t\twith {variable}:'
	start = block.index( anchor )
	return block[ :start ] + (
		f"\t\twith {variable}:\n"
		f"\t\t\trender_mode_document_tabs( '{prefix}', '📄 Loaded' )\n" )


def patch_app( ) -> dict[ str, int ]:
	text = APP_PATH.read_text( encoding='utf-8' )
	import_block = (
		'from document_processing import (\n'
		'\trender_web_document_processing,\n'
		'\trender_source_processing_controls,\n'
		'\trender_mode_document_tabs )\n' )
	if 'from document_processing import (' not in text:
		anchor = 'from caches import InMemoryCache, SQLiteCache\n'
		text = text.replace( anchor, anchor + import_block, 1 )

	crawler_start, crawler_end = find_mode_block( text, 'Site Crawler' )
	crawler_block = (
		"elif mode == 'Site Crawler':\n"
		"\trender_web_document_processing( )\n\n" )
	text = text[ :crawler_start ] + crawler_block + text[ crawler_end: ]

	mode_config = [
		( 'Weather', 'weather', 'weather_last_result', 'weather_last_source', 'weather_c2' ),
		( 'Environmental', 'env', 'env_last_result', 'env_last_source', 'enviro_c2' ),
		( 'Astronomical', 'astro', 'astro_last_result', 'astro_last_source', 'astro_c2' ),
		( 'Geological', 'geo', 'geo_last_result', 'geo_last_source', 'geo_c2' ),
	]
	counts: dict[ str, int ] = { }
	for mode_name, prefix, result_key, source_key, right_variable in mode_config:
		start, end = find_mode_block( text, mode_name )
		block = text[ start:end ]
		block, count = add_source_controls( block, prefix, result_key, source_key )
		block = replace_right_pane( block, right_variable, prefix )
		text = text[ :start ] + block + text[ end: ]
		counts[ prefix ] = count

	APP_PATH.write_text( text, encoding='utf-8' )
	return counts


def patch_fetchers( ) -> None:
	text = FETCHERS_PATH.read_text( encoding='utf-8' )
	loader_import = 'from langchain_community.document_loaders import UnstructuredURLLoader\n'
	if loader_import not in text:
		anchor = 'from langchain_community.retrievers import ArxivRetriever, WikipediaRetriever\n'
		text = text.replace( anchor, loader_import + anchor, 1 )

	start_marker = '\tdef fetch( self, url: str, time: int=10 ) -> Result | None:'
	start = text.index( start_marker, text.index( 'class WebFetcher' ) )
	end = text.index( '\n\tdef html_to_text', start )
	method = '''\tdef fetch( self, url: str, time: int=10 ) -> List[ Document ]:
\t\t"""Load a web resource into LangChain documents.

\t\tPurpose:
\t\t\tLoads the requested URL with UnstructuredURLLoader so the result can flow directly
\t\t\tinto chunking, embedding, and vector storage.

\t\tArgs:
\t\t\turl (str): Web resource URL to load.
\t\t\ttime (int): Retained timeout setting for WebFetcher API compatibility.

\t\tReturns:
\t\t\tList[Document]: LangChain documents produced from the requested URL.
\t\t"""
\t\ttry:
\t\t\tthrow_if( 'url', url )
\t\t\tself.url = url
\t\t\tself.timeout = time
\t\t\tloader = UnstructuredURLLoader(
\t\t\t\turls=[ self.url ],
\t\t\t\tcontinue_on_failure=False,
\t\t\t\tmode='single',
\t\t\t\tshow_progress_bar=False )
\t\t\tdocuments = loader.load( )
\t\t\tif not documents:
\t\t\t\traise ValueError( f'No document content was returned for URL: {self.url}' )

\t\t\tfor document in documents:
\t\t\t\tdocument.metadata = dict( document.metadata or { } )
\t\t\t\tdocument.metadata[ 'source' ] = document.metadata.get( 'source', self.url )
\t\t\t\tdocument.metadata[ 'url' ] = document.metadata.get( 'url', self.url )

\t\t\treturn documents
\t\texcept Exception as exc:
\t\t\texception = Error( exc )
\t\t\texception.module = 'fetchers'
\t\t\texception.cause = 'WebFetcher'
\t\t\texception.method = 'fetch( self, url: str, time: int=10 ) -> List[ Document ]'
\t\t\traise exception
'''
	text = text[ :start ] + method + text[ end: ]
	FETCHERS_PATH.write_text( text, encoding='utf-8' )


def patch_requirements( ) -> None:
	lines = REQUIREMENTS_PATH.read_text( encoding='utf-8' ).splitlines( )
	dependencies = [
		'langchain-text-splitters',
		'langchain-openai',
		'langchain-google-genai',
		'langchain-mistralai',
		'langchain-huggingface',
		'langchain-chroma',
		'langchain-pinecone',
		'sentence-transformers',
		'chromadb',
		'pinecone',
		'llama-cpp-python',
		'unstructured',
		'pyreadline3; sys_platform == "win32"',
	]
	for dependency in dependencies:
		if dependency not in lines:
			lines.append( dependency )
	REQUIREMENTS_PATH.write_text( '\n'.join( lines ) + '\n', encoding='utf-8' )


def main( ) -> None:
	counts = patch_app( )
	patch_fetchers( )
	patch_requirements( )
	for prefix in [ 'weather', 'env', 'geo', 'astro' ]:
		if counts.get( prefix, 0 ) == 0:
			raise RuntimeError( f'No source expanders were patched for {prefix}.' )
	print( counts )


if __name__ == '__main__':
	main( )
