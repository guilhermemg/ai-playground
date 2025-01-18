from typing import List, Dict
from pydantic import BaseModel, Field


class UserInput(BaseModel):
    msg: str


# -----------------


class GenChatOutput(BaseModel):
    assistance: str    


class ProductCategory(BaseModel):
    category: str = Field(..., description="The name of the product category")
    products: List[str] = Field(..., description="List of product names in this category")


class FormattedChatOutput(BaseModel):
    assistance: List[ProductCategory] = Field(..., description="List of product categories with their products")


