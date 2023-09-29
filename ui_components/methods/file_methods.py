from io import BytesIO
import io
import json
import os
import tempfile
from typing import Union
from urllib.parse import urlparse
from PIL import Image
import numpy as np
import uuid
import requests
import streamlit as st
from shared.constants import SERVER, InternalFileType, ServerType
from utils.data_repo.data_repo import DataRepo

# depending on the environment it will either save or host the PIL image object
def save_or_host_file(file, path, mime_type='image/png'):
    data_repo = DataRepo()
    # TODO: fix session state management, remove direct access out side the main code
    project_setting = data_repo.get_project_setting(st.session_state['project_uuid'])
    if project_setting:
        file = zoom_and_crop(file, project_setting.width, project_setting.height)
    else:
        # new project
        file = zoom_and_crop(file, 512, 512)

    uploaded_url = None
    if SERVER != ServerType.DEVELOPMENT.value:
        image_bytes = BytesIO()
        file.save(image_bytes, format=mime_type.split('/')[1])
        image_bytes.seek(0)

        uploaded_url = data_repo.upload_file(image_bytes, '.png')
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        file.save(path)

    return uploaded_url

def zoom_and_crop(file, width, height):
    # scaling
    s_x = width / file.width
    s_y = height / file.height
    scale = max(s_x, s_y)
    new_width = int(file.width * scale)
    new_height = int(file.height * scale)
    file = file.resize((new_width, new_height))

    # cropping
    left = (file.width - width) // 2
    top = (file.height - height) // 2
    right = (file.width + width) // 2
    bottom = (file.height + height) // 2
    file = file.crop((left, top, right, bottom))

    return file

def save_or_host_file_bytes(video_bytes, path, ext=".mp4"):
    uploaded_url = None
    if SERVER != ServerType.DEVELOPMENT.value:
        data_repo = DataRepo()
        uploaded_url = data_repo.upload_file(video_bytes, ext)
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(video_bytes)
    
    return uploaded_url

def add_temp_file_to_project(project_uuid, key, hosted_url):
    data_repo = DataRepo()

    file_data = {
        "name": str(uuid.uuid4()) + ".png",
        "type": InternalFileType.IMAGE.value,
        "project_id": project_uuid,
        'hosted_url': hosted_url
    }

    temp_file = data_repo.create_file(**file_data)
    project = data_repo.get_project_from_uuid(project_uuid)
    temp_file_list = project.project_temp_file_list
    temp_file_list.update({key: temp_file.uuid})
    temp_file_list = json.dumps(temp_file_list)
    project_data = {
        'uuid': project_uuid,
        'temp_file_list': temp_file_list
    }
    data_repo.update_project(**project_data)


def generate_temp_file(url, ext=".mp4"):
    response = requests.get(url)
    if not response.ok:
        raise ValueError(f"Could not download video from URL: {url}")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext, mode='wb')
    temp_file.write(response.content)
    temp_file.close()

    return temp_file


def generate_pil_image(img: Union[Image.Image, str, np.ndarray, io.BytesIO]):
    # Check if img is a PIL image
    if isinstance(img, Image.Image):
        pass

    # Check if img is a URL
    elif isinstance(img, str) and bool(urlparse(img).netloc):
        response = requests.get(img)
        img = Image.open(BytesIO(response.content))

    # Check if img is a local file
    elif isinstance(img, str):
        img = Image.open(img)

    # Check if img is a numpy ndarray
    elif isinstance(img, np.ndarray):
        img = Image.fromarray(img)

    # Check if img is a BytesIO stream
    elif isinstance(img, io.BytesIO):
        img = Image.open(img)

    else:
        raise ValueError(
            "Invalid image input. Must be a PIL image, a URL string, a local file path string or a numpy ndarray.")

    return img

def generate_temp_file_from_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(uploaded_file.read())
            return temp_file


def convert_bytes_to_file(file_location_to_save, mime_type, file_bytes, project_uuid, inference_log_id=None, filename=None, tag=""):
    data_repo = DataRepo()

    hosted_url = save_or_host_file_bytes(file_bytes, file_location_to_save, "." + mime_type.split("/")[1])
    file_data = {
        "name": str(uuid.uuid4()) + "." + mime_type.split("/")[1] if not filename else filename,
        "type": InternalFileType.IMAGE.value,
        "project_id": project_uuid,
        "inference_log_id": inference_log_id,
        "tag": tag
    }

    if hosted_url:
        file_data.update({'hosted_url': hosted_url})
    else:
        file_data.update({'local_path': file_location_to_save})

    file = data_repo.create_file(**file_data)

    return file