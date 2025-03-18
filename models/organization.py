from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

class OrganizationBase(BaseModel):
    """Base Organization model with common fields"""
    name: str
    short_name: Optional[str] = None
    alias: Optional[str] = None
    jurisdiction: Optional[str] = None
    register_type: Optional[str] = None
    register_court: Optional[str] = None
    register_number: Optional[str] = None
    euid: Optional[str] = None
    legal_form: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class Organization(OrganizationBase):
    """Complete Organization model including all fields"""
    openregisters_id: str  # Primary key
    seat: Optional[Dict[str, Any]] = None
    addresses: Optional[List[Dict[str, Any]]] = None
    phone_infos: Optional[List[Dict[str, Any]]] = None
    bank_info: Optional[Dict[str, Any]] = None
    date_founded: Optional[datetime] = None
    timestamp_of_si: datetime
    capital: Optional[Dict[str, Any]] = None
    participations: Optional[List[Dict[str, Any]]] = None
    inferences: Optional[Dict[str, Any]] = None
    data_path: Optional[str] = None

class OrganizationResponse(Organization):
    """Organization response model with any additional fields"""
    class Config:
        orm_mode = True

class SearchParams(BaseModel):
    """Search parameters model"""
    name: Optional[str] = None
    description: Optional[str] = None
    jurisdiction: Optional[str] = None
    legal_form: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)

class PaginatedResponse(BaseModel):
    """Paginated response model"""
    total: int
    limit: int
    offset: int
    has_more: bool

class SearchResponse(BaseModel):
    """Search results model"""
    results: List[OrganizationResponse]
    pagination: PaginatedResponse

class StatsResponse(BaseModel):
    """Statistics response model"""
    total_organizations: int
    by_status: List[Dict[str, Any]]
    top_jurisdictions: List[Dict[str, Any]]
    top_legal_forms: List[Dict[str, Any]]
