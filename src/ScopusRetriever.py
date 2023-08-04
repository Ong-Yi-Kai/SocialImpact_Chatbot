"""
Modules retrieves a collection of paper from scopus given a set of keywords
"""
import httpx
from typing import List

class ScopusRetriever:

    def __init__(self, api_key:str):
        """
        :param api_key: valid scopus API key
        """
        self.api_key = api_key

    def search_scidir(self, query:str, count:int, start:int):
        """
        Performs a search query to Elsevier's ScienceDirect Search API V2
        query: str query to elsevier
        apikey: user apikey with Elsevier's, make one at https://dev.elsevier.com/
        count: number of search results to return
        start: start index to search
        Rerturns: Httpx Response object
        """
        headers = {"X-ELS-APIKey":self.api_key,"Accept":"application/json"}
        params = {
            # keywords to search
            "query": query,
            # max number of results to be returned, permitted 10,25,50,100
            "count" : count,
            # result offset
            "start" : start,
            # date range for search
            "date" : "2020-2021"
        }
        # amt of time before error is raised
        timeout = httpx.Timeout(10.0, connect=60.0) # 60s for connect and 10 elsewhere
        # client object to make queries in our case
        client = httpx.Client(timeout=timeout,headers=headers)
        # base URL
        url = f"https://api.elsevier.com/content/search/sciencedirect"
        # builds and send request
        return client.get(url, params=params)

    def get_dois(self, response)->List[str]:
        """
        retrieves the DOI numbers from the reponse
        returns: list of DOI numbers as strings
        """
        dois = []
        data = response.json()
        if response.status_code == 200 and \
                len(data['search-results']['entry']) and \
                'error' not in data['search-results']['entry'][0].keys():
            data = response.json()
            for entry in data['search-results']['entry']:
                doi = entry['prism:doi']
                dois.append(doi)
        return dois

    def retrieve_full_paper(self, paper_doi:str, format:str="text/xml"):
        """
        Performs a search query to elsevier Article (Full Text) Retrieval API
        paper_doi: DOI number corresponding to the paper you want to grab
        :param format: onf od 'text/xml', 'application/json', 'application/pdf','image/pdf',
        'text/plain', 'application/rdf+xml'
        returns: original text corresponding to paper_doi
        """
        headers={
            "X-ELS-APIKey":self.api_key,
            "Accept":format
             }
        timeout = httpx.Timeout(10.0, connect=60.0)
        client = httpx.Client(timeout=timeout,headers=headers)
        url=f"https://api.elsevier.com/content/article/doi/"+paper_doi
        r=client.get(url)
        if r.status_code == 200:
            if format == 'application/json':
                return r.json()['full-text-retrieval-response']['originalText']
            return r

    def filter_text(self,text:str):
        """
        Filters a text to the body, disregarding the references
        text: text to be filtered
        returns: filtered text. If failure then return the original
        """
        # attempt to filter by zoning in from abstract till the end
        abs_idx = text.lower().find('abstract') + 8
        ref_idx = text.lower().rfind('reference')
        if ref_idx > abs_idx and abs_idx > 0 and ref_idx > 0:
            return text[abs_idx:ref_idx]
        return text
