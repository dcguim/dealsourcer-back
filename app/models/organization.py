import json
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict
from pydantic import validator
from datetime import datetime, date

class SeatModel(BaseModel):
    """Model for seat information"""
    model_config = ConfigDict(extra='allow')
    city: Optional[str] = None
    zip_code: Optional[str] = None
    country_code: Optional[str] = None

class AddressModel(BaseModel):
    """Model for address information"""
    model_config = ConfigDict(extra='allow')
    city: Optional[str] = None
    state: Optional[str] = None
    street: Optional[str] = None
    landlord: Optional[str] = None
    zip_code: Optional[str] = None
    city_area: Optional[str] = None
    address_type: Optional[str] = None
    country_code: Optional[str] = None
    house_number: Optional[str] = None
    address_extra: Optional[str] = None
    po_box_number: Optional[str] = None

class PhoneInfoModel(BaseModel):
    """Model for phone information"""
    model_config = ConfigDict(extra='allow')
    extra: Optional[str] = None
    phone_type: Optional[str] = None
    phone_number: Optional[str] = None

class BankInfoModel(BaseModel):
    """Model for bank information"""
    model_config = ConfigDict(extra='allow')
    # Add specific bank info fields if known

class CapitalModel(BaseModel):
    """Model for capital information"""
    model_config = ConfigDict(extra='allow')
    amount: Optional[float] = None
    details: Optional[str] = None
    currency: Optional[str] = None

class RoleModel(BaseModel):
    """Model for roles"""
    model_config = ConfigDict(extra='allow')
    code: Optional[str] = None
    name: Optional[str] = None
    details: Optional[str] = None

class ParticipantNameModel(BaseModel):
    """Model for participant name"""
    model_config = ConfigDict(extra='allow')
    extra: Optional[str] = None
    title: Optional[str] = None
    prefix: Optional[str] = None
    last_name: Optional[str] = None
    birth_name: Optional[str] = None
    first_name: Optional[str] = None
    other_names: Optional[List[str]] = None

class ParticipantModel(BaseModel):
    """Model for participant information"""
    model_config = ConfigDict(extra='allow')
    euid: Optional[str] = None
    name: Optional[Union[str, ParticipantNameModel]] = None
    seat: Optional[SeatModel] = None
    alias: Optional[str] = None
    addresses: Optional[List[AddressModel]] = None
    bank_info: Optional[BankInfoModel] = None
    legal_form: Optional[str] = None
    short_name: Optional[str] = None
    phone_infos: Optional[List[PhoneInfoModel]] = None
    jurisdiction: Optional[str] = None
    register_type: Optional[str] = None
    register_court: Optional[str] = None
    register_number: Optional[str] = None
    # Additional fields for personal participants
    sex: Optional[str] = None
    birth_date: Optional[str] = None
    occupation: Optional[str] = None

class ParticipationModel(BaseModel):
    """Model for participations"""
    model_config = ConfigDict(extra='allow')
    roles: Optional[List[RoleModel]] = None
    participant: Optional[ParticipantModel] = None

class SearchResultModel(BaseModel):
    """Comprehensive model for search results"""
    model_config = ConfigDict(extra='allow')
    
    name: Optional[str] = None
    short_name: Optional[str] = None
    alias: Optional[str] = None
    jurisdiction: Optional[str] = None
    register_type: Optional[str] = None
    register_court: Optional[str] = None
    register_number: Optional[str] = None
    euid: Optional[str] = None
    legal_form: Optional[str] = None
    
    # JSON-encoded fields with custom parsing
    seat: Optional[SeatModel] = None
    addresses: Optional[List[AddressModel]] = None
    phone_infos: Optional[List[PhoneInfoModel]] = None
    bank_info: Optional[BankInfoModel] = None
    capital: Optional[List[CapitalModel]] = None
    participations: Optional[List[ParticipationModel]] = None
    inferences: Optional[List[Dict[str, Any]]] = None
    
    date_founded: Optional[date] = None
    timestamp_of_si: Optional[datetime] = None
    openregisters_id: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    data_path: Optional[str] = None
    textsearch: Optional[str] = None
    
    @validator('seat', 'addresses', 'phone_infos', 'bank_info', 'capital', 'participations', 'inferences', pre=True)
    @classmethod
    def parse_json_field(cls, v):
        if isinstance(v, str):
            # Handle 'null' string or empty string
            if v.lower() == 'null' or v.strip() == '':
                return None
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    @validator('date_founded', pre=True)
    @classmethod
    def parse_date_founded(cls, v):
        if v is None:
            return None
        if isinstance(v, (datetime, date)):
            return v.date() if isinstance(v, datetime) else v
        
        # Try multiple parsing strategies
        date_formats = [
            '%Y-%m-%d',  # ISO format
            '%d.%m.%Y',  # European format
            '%m/%d/%Y',  # US format
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(str(v), fmt).date()
            except (ValueError, TypeError):
                continue
        
        return None

class SearchParams(BaseModel):
    """Search parameters model"""
    name: Optional[str] = None
    description: Optional[str] = None
    jurisdiction: Optional[str] = None
    legal_form: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)

class SearchResponse(BaseModel):
    """Model for the entire search response"""
    results: List[SearchResultModel]
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None

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
    date_founded: Optional[date] = None
    timestamp_of_si: datetime
    capital: Optional[Dict[str, Any]] = None
    participations: Optional[List[Dict[str, Any]]] = None
    inferences: Optional[Dict[str, Any]] = None
    data_path: Optional[str] = None

class OrganizationResponse(Organization):
    """Organization response model with any additional fields"""
    class Config:
        orm_mode = True

class PaginatedResponse(BaseModel):
    """Paginated response model"""
    total: int
    limit: int
    offset: int
    has_more: bool

class StatsResponse(BaseModel):
    """Statistics response model"""
    total_organizations: int
    by_status: List[Dict[str, Any]]
    top_jurisdictions: List[Dict[str, Any]]
    top_legal_forms: List[Dict[str, Any]]
