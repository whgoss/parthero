from abc import abstractmethod
from typing import List
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseDTO(BaseModel):
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        use_enum_values=False,
    )

    @abstractmethod
    def from_model(cls, model: BaseModel) -> "BaseDTO":
        pass

    @classmethod
    def from_models(cls, models: List[BaseModel]):
        return [cls.from_model(model) for model in models]

    def __eq__(self, value):
        if self.id and value.id:
            return self.id == value.id
        return super().__eq__(value)
