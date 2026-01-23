import requests
import logging
from typing import Optional
from pydantic import TypeAdapter
from core.dtos.domo import DomoSearchResultDTO, DomoWorkDTO
from parthero.settings import DOMO_ID, DOMO_TOKEN, DOMO_URL, REQUEST_TIMEOUT

logger = logging.getLogger()


def search_for_piece(
    title: str, composer: Optional[str] = None
) -> DomoSearchResultDTO | None:
    domo_search_results = []
    headers = get_domo_headers(title=title, composer=composer)
    try:
        response = requests.get(
            DOMO_URL + "/search", headers=headers, timeout=REQUEST_TIMEOUT
        )
        if response.text and response.status_code == 200:
            adapter = TypeAdapter(list[DomoSearchResultDTO])
            domo_search_results = adapter.validate_json(response.text)
    except Exception:
        logger.error("Error calling DOMO API", exc_info=True)
    finally:
        return domo_search_results


def fetch_piece(domo_id: str) -> DomoWorkDTO | None:
    if not domo_id:
        return None

    domo_work = None
    headers = get_domo_headers(domo_id=domo_id)
    try:
        response = requests.get(
            DOMO_URL + "/fetch", headers=headers, timeout=REQUEST_TIMEOUT
        )
        if response.text and response.status_code == 200:
            domo_work = DomoWorkDTO.model_validate_json(response.text)
    except Exception:
        logger.error("Error calling DOMO API", exc_info=True)
    finally:
        return domo_work


def get_domo_headers(
    domo_id: Optional[str] = None,
    title: Optional[str] = None,
    composer: Optional[str] = None,
) -> dict:
    headers = {
        "accept": "application/json",
        "userId": DOMO_ID,
        "token": DOMO_TOKEN,
    }
    if domo_id:
        headers["work"] = domo_id
    if title:
        headers["work"] = title
    if composer:
        headers["composer"] = composer
    return headers
