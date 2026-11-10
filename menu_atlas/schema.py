from pydantic import BaseModel, Field

class Item(BaseModel):
    category: str | None = None
    name: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = None
    attributes: list[str] = Field(default_factory=list)

class Menu(BaseModel):
    restaurant: str | None = None
    categories: list[str] = Field(default_factory=list)
    items: list[Item] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
