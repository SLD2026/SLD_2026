from pydantic import BaseModel
from typing import Optional, List

class CameraCreate(BaseModel):
    camera_id: str
    name: str
    rtsp_url: str
    roi_polygon: Optional[str] = "[]"

class CameraResponse(BaseModel):
    id: int
    camera_id: str
    name: str
    rtsp_url: str
    is_active: bool
    roi_polygon: Optional[str]

    class Config:
        from_attributes = True

class ROIUpdate(BaseModel):
    roi_polygon: str  # JSON string format: [[x1,y1], [x2,y2], ...]