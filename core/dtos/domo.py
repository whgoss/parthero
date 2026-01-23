from core.dtos.base import BaseDTO


class DomoComposerDTO(BaseDTO):
    domo_uid: str
    first_name: str
    last_name: str
    full_name: str


class DomoWorkDTO(BaseDTO):
    domo_uid: str
    title: str
    formula: str
    duration: str
    remarks: str
    composer: DomoComposerDTO


class DomoSearchResultDTO(BaseDTO):
    composer: str
    title: str
    composer_domo_uid: str
    work_domo_uid: str
