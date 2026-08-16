from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import Literal, Optional


class NameCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class NameOut(BaseModel):
    id: int
    name: str
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    request_admin: bool = Field(default=False)
    request_staff: bool = Field(default=False)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    created_at: datetime


class UserRequestOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    admin_requested: bool
    staff_requested: bool
    created_at: datetime


class UserRoleUpdate(BaseModel):
    role: Literal["client", "staff", "admin"]


class ProductStockUpdate(BaseModel):
    quantity_in_stock: int = Field(ge=0)


class RoleRequestAction(BaseModel):
    request_type: Literal["admin", "staff"]
    action: Literal["approve", "deny"]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: EmailStr
    role: str


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category_id: int
    sku: str = Field(min_length=1, max_length=50)
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    unit: Optional[str] = None
    quantity_in_stock: int = Field(default=0, ge=0)
    reorder_threshold: Optional[int] = Field(default=None, ge=0)
    expiry_date: Optional[date] = None
    requires_prescription: bool = False
    manufacturer: Optional[str] = None
    notes: Optional[str] = None


class ProductUpdate(BaseModel):
    """All fields optional — used for PATCH (e.g. just updating stock)."""
    name: Optional[str] = None
    category_id: Optional[int] = None
    sku: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    unit: Optional[str] = None
    quantity_in_stock: Optional[int] = Field(default=None, ge=0)
    reorder_threshold: Optional[int] = Field(default=None, ge=0)
    expiry_date: Optional[date] = None
    requires_prescription: Optional[bool] = None
    manufacturer: Optional[str] = None
    notes: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    category_id: int
    sku: str
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    unit: Optional[str] = None
    quantity_in_stock: int
    reorder_threshold: Optional[int] = None
    expiry_date: Optional[date] = None
    requires_prescription: bool
    manufacturer: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
