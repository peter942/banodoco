import time
from typing import List
import streamlit as st
from ui_components.constants import WorkflowStageType
from ui_components.methods.file_methods import generate_pil_image

from ui_components.models import InternalFrameTimingObject, InternalShotObject
from ui_components.widgets.add_key_frame_element import add_key_frame
from ui_components.widgets.frame_movement_widgets import change_frame_position_input, delete_frame_button, jump_to_single_frame_view_button, move_frame_back_button, move_frame_forward_button, replace_image_widget
from utils.data_repo.data_repo import DataRepo

def shot_keyframe_element(shot_uuid, items_per_row, **kwargs):
    data_repo = DataRepo()
    shot: InternalShotObject = data_repo.get_shot_from_uuid(shot_uuid)

    st.title(shot.name)
    timing_list: List[InternalFrameTimingObject] = shot.timing_list

    if st.button("Move shot down", key=f'shot_down_movement_{shot.uuid}'):
        shot_list = data_repo.get_shot_list(shot.project.uuid)
        if shot.shot_idx < len(shot_list):
            data_repo.update_shot(shot_uuid, shot_idx=shot.shot_idx+1)
        else:
            st.error("this is the last shot")
            time.sleep(0.3)
        st.rerun()
    
    if st.button("Move shot up", key=f'shot_up_movement_{shot.uuid}'):
        if shot.shot_idx > 0:
            data_repo.update_shot(shot_uuid, shot_idx=shot.shot_idx-1)
        else:
            st.error("this is the first shot")
            time.sleep(0.3)
        st.rerun()

    grid = st.columns(items_per_row)
    if timing_list and len(timing_list):
        for idx, timing in enumerate(timing_list):
            with grid[idx%items_per_row]:
                if timing.primary_image and timing.primary_image.location:
                    st.image(timing.primary_image.location, use_column_width=True)
                    timeline_view_buttons(idx, shot_uuid, **kwargs)
                else:
                    st.warning("No primary image present")
    else:
        st.warning("No keyframes present")

def shot_video_element(shot_uuid):
    data_repo = DataRepo()
    shot: InternalShotObject = data_repo.get_shot_from_uuid(shot_uuid)

    st.title(shot.name)
    if shot.main_clip and shot.main_clip.location:
        st.video(shot.main_clip.location)
    else:
        st.warning("No video present")
    
    if st.button("Generate video", key=shot.uuid):
        if not (shot.timing_list and len(shot.timing_list) and len(shot.timing_list) > 1):
            st.error("Atleast two frames are required")
            time.sleep(0.3)
            return
        
        # NOTE: @peter let me know if you want me to complete this

        

def timeline_view_buttons(idx, shot_uuid, replace_image_widget_toggle, copy_frame_toggle, move_frames_toggle, delete_frames_toggle, change_position_toggle):
    data_repo = DataRepo()
    shot = data_repo.get_shot_from_uuid(shot_uuid)
    timing_list = shot.timing_list

    if replace_image_widget_toggle:
        replace_image_widget(timing_list[idx].uuid, stage=WorkflowStageType.STYLED.value, options=["Uploaded Frame"])
    
    btn1, btn2, btn3, btn4 = st.columns([1, 1, 1, 1])
    
    if move_frames_toggle:
        with btn1:                                            
            move_frame_back_button(timing_list[idx].uuid, "side-to-side")
        with btn2:   
            move_frame_forward_button(timing_list[idx].uuid, "side-to-side")
    
    if copy_frame_toggle:
        with btn3:
            if st.button("🔁", key=f"copy_frame_{timing_list[idx].uuid}"):
                pil_image = generate_pil_image(timing_list[idx].primary_image.location)
                add_key_frame(pil_image, False, st.session_state['shot_uuid'], timing_list[idx].aux_frame_index+1, refresh_state=False)
                st.rerun()

    if delete_frames_toggle:
        with btn4:
            delete_frame_button(timing_list[idx].uuid)
    
    if change_position_toggle:
        change_frame_position_input(timing_list[idx].uuid, "side-to-side")
    
    jump_to_single_frame_view_button(idx + 1, timing_list, 'timeline_btn_'+str(timing_list[idx].uuid))        
