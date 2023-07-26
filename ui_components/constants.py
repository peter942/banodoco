from utils.enum import ExtendedEnum


class WorkflowStageType(ExtendedEnum):
    SOURCE = "source"
    STYLED = "styled"
    

class VideoQuality(ExtendedEnum):
    HIGH = "High-Quality"
    PREVIEW = "Preview"
    LOW = "Low"


# TODO: make proper paths for every file
CROPPED_IMG_LOCAL_PATH = "videos/temp/cropped.png"

MASK_IMG_LOCAL_PATH = "videos/temp/mask.png"
TEMP_MASK_FILE = 'temp_mask_file'