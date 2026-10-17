from pydantic import BaseModel


class QuizDeleteRequest(BaseModel):
    uuid: str


class QuizDeleteListRequest(BaseModel):
    list_uuid: list[QuizDeleteRequest]


class QuizDeleteResponse(BaseModel):
    excluded: bool
