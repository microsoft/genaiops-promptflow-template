import json
import re
import requests
from promptflow import tool
from promptflow.connections import AzureOpenAIConnection
from promptflow.connections import CognitiveSearchConnection

fieldMap = {
    "id": ["id"],
    "url": ["url", "uri", "link", "document_link"],
    "filepath": ["filepath", "filename"],
    "content": ["content"]
}
titleRegex = re.compile(r"title: (.*)\n")

def getIfString(doc, fieldName):
    try: 
        value = doc.get(fieldName)
        if isinstance(value, str) and len(value) > 0:
            return value
        return None
    except:
        return None

def get_truncated_string(string_value, max_length):
    return string_value[:max_length]

def getTitle(doc):
    max_title_length = 150
    title = getIfString(doc, 'title')
    if title:
        return get_truncated_string(title, max_title_length)
    else:
        title = getIfString(doc, 'content')
        if title: 
            titleMatch = titleRegex.search(title)
            if titleMatch:
                return get_truncated_string(titleMatch.group(1), max_title_length)
            else:
                return None
        else:
            return None

def getChunkId(doc):
    chunk_id = getIfString(doc, 'chunk_id')
    return chunk_id

def getSearchScore(doc):
    try:
        return doc['@search.score']
    except:
        return None

def getQueryList(query):
    try:
        config = json.loads(query)
        return config
    except Exception:
        return [query]

def process_search_docs_response(docs):
    outputs = []
    for doc in docs:
        formattedDoc = {}
        for fieldName in fieldMap.keys():
            for fromFieldName in fieldMap[fieldName]:
                fieldValue = getIfString(doc, fromFieldName)
                if fieldValue:
                    formattedDoc[fieldName] = doc[fromFieldName]
                    break
        formattedDoc['title'] = getTitle(doc)
        formattedDoc['chunk_id'] = getChunkId(doc)
        formattedDoc['search_score'] = getSearchScore(doc)
        outputs.append(formattedDoc)
    return outputs

def get_query_embedding(query, endpoint, api_key, api_version, embedding_model_deployment):
    request_url = f"{endpoint}/openai/deployments/{embedding_model_deployment}/embeddings?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    request_payload = {
        'input': query
    }
    embedding_response = requests.post(request_url, json = request_payload, headers = headers, timeout=None)
    if embedding_response.status_code == 200:
        data_values = embedding_response.json()["data"]
        embeddings_vectors = [data_value["embedding"] for data_value in data_values]
        return embeddings_vectors
    else:
        raise Exception(f"failed to get embedding: {embedding_response.json()}")

def search_query_api(
    endpoint, 
    api_key,
    api_version, 
    index_name, 
    query_type, 
    query, 
    top_k, 
    embeddingModelConnection,
    embeddingModelName = None,
    semantic_configuration_name=None,
    vectorFields=None):
    request_url = f"{endpoint}/indexes/{index_name}/docs/search?api-version={api_version}"
    request_payload = {
        'top': top_k,
        'queryLanguage': 'en-us'
    }
    if query_type == 'simple':
        request_payload['search'] = query
        request_payload['queryType'] = query_type
    elif query_type == 'semantic':
        request_payload['search'] = query
        request_payload['queryType'] = query_type
        request_payload['semanticConfiguration'] = semantic_configuration_name
    elif query_type in ('vector', 'vectorSimpleHybrid', 'vectorSemanticHybrid'):
        if vectorFields and embeddingModelName:
            query_vectors = get_query_embedding(
                query,
                embeddingModelConnection["api_base"],
                embeddingModelConnection["api_key"],
                embeddingModelConnection["api_version"],
                embeddingModelName
            )
            payload_vectors = [{"value": query_vector, "fields": vectorFields, "k": top_k } for query_vector in query_vectors]
            request_payload['vectors'] = payload_vectors

        if query_type == 'vectorSimpleHybrid':
            request_payload['search'] = query
        elif query_type == 'vectorSemanticHybrid':
            request_payload['search'] = query
            request_payload['queryType'] = 'semantic'
            request_payload['semanticConfiguration'] = semantic_configuration_name
    else:
        raise Exception(f"unsupported query type: {query_type}")
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    retrieved_docs = requests.post(request_url, json = request_payload, headers = headers, timeout=None)
    if retrieved_docs.status_code == 200:
        return process_search_docs_response(retrieved_docs.json()["value"])
    else:
        raise Exception(f"failed to query search index : {retrieved_docs.json()}")

@tool
def search(queries: str, searchConnection: CognitiveSearchConnection, indexName: str, queryType: str, topK: int, semanticConfiguration: str, vectorFields: str, embeddingModelConnection: AzureOpenAIConnection, embeddingModelName: str):
    semanticConfiguration = semanticConfiguration if semanticConfiguration != "None" else None
    vectorFields = vectorFields if vectorFields != "None" else None
    embeddingModelName = embeddingModelName if embeddingModelName != None else None
                      
    # Do search.
    allOutputs = [search_query_api(
        searchConnection['api_base'], 
        searchConnection['api_key'], 
        searchConnection['api_version'], 
        indexName,
        queryType,
        query, 
        topK, 
        embeddingModelConnection, 
        embeddingModelName,
        semanticConfiguration,
        vectorFields) for query in getQueryList(queries)]

    includedOutputs = []
    while allOutputs and len(includedOutputs) < topK:
        for output in list(allOutputs):
            if len(output) == 0:
                allOutputs.remove(output)
                continue
            value = output.pop(0)
            if value not in includedOutputs:
                includedOutputs.append(value)
                if len(includedOutputs) >= topK:
                    break
    return includedOutputs
