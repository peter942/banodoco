from typing import List
import time
import streamlit as st
from shared.constants import AnimationStyleType, AnimationToolType
import time
from ui_components.widgets.sm_animation_style_element import animation_sidebar, individual_frame_settings_element, \
    select_motion_lora_element, select_sd_model_element, video_motion_settings
from ui_components.models import InternalFileObject, InternalShotObject
from ui_components.methods.animation_style_methods import toggle_generate_inference, transform_data, \
    update_session_state_with_animation_details
from ui_components.methods.video_methods import create_single_interpolated_clip
from utils import st_memory
from utils.data_repo.data_repo import DataRepo

default_model = "Deliberate_v2.safetensors"
def sm_video_rendering_page(shot_uuid, img_list: List[InternalFileObject]):
    data_repo = DataRepo()
    shot: InternalShotObject = data_repo.get_shot_from_uuid(shot_uuid)

    settings = {
        'animation_tool': AnimationToolType.ANIMATEDIFF.value,
    }
    shot_meta_data = {}

    with st.container():
        col1, _, _ = st.columns([1.0,1.5, 1.0])

        # ----------- INDIVIDUAL FRAME SETTINGS -----------
        strength_of_frames, distances_to_next_frames,\
            speeds_of_transitions, freedoms_between_frames,\
                individual_prompts, individual_negative_prompts,\
                    motions_during_frames = individual_frame_settings_element(shot_uuid, img_list, col1)

        # ----------- SELECT SD MODEL -----------
        sd_model, model_files = select_sd_model_element(shot_uuid, default_model)
              
        # ----------- SELECT MOTION LORA ------------
        lora_data = select_motion_lora_element(shot_uuid, model_files)
        
        # ----------- OTHER SETTINGS ------------
        strength_of_adherence, overall_positive_prompt, \
            overall_negative_prompt, type_of_motion_context = video_motion_settings(shot_uuid, img_list)
        
        type_of_frame_distribution = "dynamic"
        type_of_key_frame_influence = "dynamic"
        type_of_strength_distribution = "dynamic"
        linear_frame_distribution_value = 16
        linear_key_frame_influence_value = 1.0
        linear_cn_strength_value = 1.0            
        relative_ipadapter_strength = 1.0
        relative_cn_strength = 0.0
        project_settings = data_repo.get_project_setting(shot.project.uuid)
        width = project_settings.width
        height = project_settings.height
        img_dimension = f"{width}x{height}"
        motion_scale = 1.3
        interpolation_style = 'ease-in-out'
        buffer = 4
        amount_of_motion = 1.3

        (dynamic_strength_values, dynamic_key_frame_influence_values, dynamic_frame_distribution_values, 
        context_length, context_stride, context_overlap, multipled_base_end_percent, multipled_base_adapter_strength, 
        prompt_travel,  negative_prompt_travel, motion_scales) = transform_data(
            strength_of_frames, 
            freedoms_between_frames, 
            speeds_of_transitions, 
            distances_to_next_frames, 
            type_of_motion_context, 
            strength_of_adherence,
            individual_prompts, 
            individual_negative_prompts, 
            buffer, 
            motions_during_frames
        )

        settings.update(
            ckpt=sd_model,
            width=width,
            height=height,
            buffer=4,
            motion_scale=motion_scale,
            motion_scales=motion_scales,
            image_dimension=img_dimension,
            output_format="video/h264-mp4",
            prompt=overall_positive_prompt,
            negative_prompt=overall_negative_prompt,
            interpolation_type=interpolation_style,
            stmfnet_multiplier=2,
            relative_ipadapter_strength=relative_ipadapter_strength,
            relative_cn_strength=relative_cn_strength,      
            type_of_strength_distribution=type_of_strength_distribution,
            linear_strength_value=str(linear_cn_strength_value),
            dynamic_strength_values=str(dynamic_strength_values),
            linear_frame_distribution_value=linear_frame_distribution_value,
            dynamic_frame_distribution_values=dynamic_frame_distribution_values,
            type_of_frame_distribution=type_of_frame_distribution,                
            type_of_key_frame_influence=type_of_key_frame_influence,
            linear_key_frame_influence_value=float(linear_key_frame_influence_value),
            dynamic_key_frame_influence_values=dynamic_key_frame_influence_values,
            normalise_speed=True,
            ipadapter_noise=0.3,
            animation_style=AnimationStyleType.CREATIVE_INTERPOLATION.value,
            context_length=context_length,
            context_stride=context_stride,
            context_overlap=context_overlap,
            multipled_base_end_percent=multipled_base_end_percent,
            multipled_base_adapter_strength=multipled_base_adapter_strength,
            individual_prompts=prompt_travel,
            individual_negative_prompts=negative_prompt_travel,
            animation_stype=AnimationStyleType.CREATIVE_INTERPOLATION.value,            
            max_frames=str(dynamic_frame_distribution_values[-1]),
            lora_data=lora_data,
            shot_data=shot_meta_data,
            pil_img_structure_control_image=st.session_state[f"structure_control_image_{shot.uuid}"],   # this is a PIL object
            strength_of_structure_control_image=st.session_state[f"strength_of_structure_control_image_{shot.uuid}"],
        )
        
        position = "generate_vid"
        st.markdown("***")
        st.markdown("##### Generation Settings")

        animate_col_1, _, _ = st.columns([3, 1, 1])
        with animate_col_1:
            variant_count = st.number_input("How many variants?", min_value=1, max_value=5, value=1, step=1, key="variant_count")
            
            if "generate_vid_generate_inference" in st.session_state and st.session_state["generate_vid_generate_inference"]:
                # last keyframe position * 16
                duration = float(dynamic_frame_distribution_values[-1] / 16)
                data_repo.update_shot(uuid=shot_uuid, duration=duration)
                shot_data = update_session_state_with_animation_details(
                    shot_uuid, 
                    img_list, 
                    strength_of_frames, 
                    distances_to_next_frames, 
                    speeds_of_transitions, 
                    freedoms_between_frames, 
                    motions_during_frames, 
                    individual_prompts, 
                    individual_negative_prompts,
                    lora_data,
                    default_model
                )
                settings.update(shot_data=shot_data)
                vid_quality = "full"
                st.success("Generating clip - see status in the Generation Log in the sidebar. Press 'Refresh log' to update.")

                positive_prompt = ""
                append_to_prompt = ""
                for idx, img in enumerate(img_list):
                    if img.location:
                        b =img.inference_params
                        prompt = b.get("prompt", "") if b else ""
                        prompt += append_to_prompt
                        frame_prompt = f"{idx * linear_frame_distribution_value}_" + prompt
                        positive_prompt += ":" + frame_prompt if positive_prompt else frame_prompt
                    else:
                        st.error("Please generate primary images")
                        time.sleep(0.7)
                        st.rerun()
                        
                if f'{shot_uuid}_backlog_enabled' not in st.session_state:
                    st.session_state[f'{shot_uuid}_backlog_enabled'] = False

                create_single_interpolated_clip(
                    shot_uuid,
                    vid_quality,
                    settings,
                    variant_count,
                    st.session_state[f'{shot_uuid}_backlog_enabled']
                )
                
                backlog_update = {f'{shot_uuid}_backlog_enabled': False}
                toggle_generate_inference(position, **backlog_update)
                st.rerun()
            
            btn1, btn2, _  = st.columns([1, 1, 1])
            backlog_no_update = {f'{shot_uuid}_backlog_enabled': False}
            with btn1:
                help = ""
                st.button("Add to queue", key="generate_animation_clip", disabled=False, help=help, \
                    on_click=lambda: toggle_generate_inference(position, **backlog_no_update), type="primary", use_container_width=True)
            
            backlog_update = {f'{shot_uuid}_backlog_enabled': True}
            with btn2:
                backlog_help = "This will add the new video generation in the backlog"
                st.button("Add to backlog", key="generate_animation_clip_backlog", disabled=False, help=backlog_help, \
                    on_click=lambda: toggle_generate_inference(position, **backlog_update), type="secondary")

        # --------------- SIDEBAR ---------------------
        animation_sidebar(
            shot_uuid, 
            img_list, 
            type_of_frame_distribution, 
            dynamic_frame_distribution_values, 
            linear_frame_distribution_value,
            type_of_strength_distribution, 
            dynamic_strength_values, 
            linear_cn_strength_value, 
            type_of_key_frame_influence, 
            dynamic_key_frame_influence_values,
            linear_key_frame_influence_value, 
            strength_of_frames, 
            distances_to_next_frames, 
            speeds_of_transitions, 
            freedoms_between_frames,
            motions_during_frames,
            individual_prompts,
            individual_negative_prompts, 
            default_model
        )
        

def two_img_realistic_interpolation_page(shot_uuid, img_list):
    if not (img_list and len(img_list) >= 2):
        st.error("You need two images for this interpolation")
        return
    
    data_repo = DataRepo()
    shot = data_repo.get_shot_from_uuid(shot_uuid)
    
    settings = {}
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:                        
        st.image(img_list[0].location, use_column_width=True)
    
    with col3:                        
        st.image(img_list[1].location, use_column_width=True)

    with col2:
        description_of_motion = st_memory.text_area("Describe the motion you want between the frames:", key=f"description_of_motion_{shot.uuid}")
        st.info("This is very important and will likely require some iteration.")
        
    variant_count = 1  # Assuming a default value for variant_count, adjust as necessary
    vid_quality = "full"  # Assuming full quality, adjust as necessary based on your requirements
    position = "dynamiccrafter"

    if f"{position}_generate_inference" in st.session_state and st.session_state[f"{position}_generate_inference"]:

        st.success("Generating clip - see status in the Generation Log in the sidebar. Press 'Refresh log' to update.")
        # Assuming the logic to generate the clip based on two images, the described motion, and fixed duration
        duration = 4  # Fixed duration of 4 seconds
        data_repo.update_shot(uuid=shot.uuid, duration=duration)

        project_settings = data_repo.get_project_setting(shot.project.uuid)
        
        settings.update(
            duration= duration,
            animation_style=AnimationStyleType.DIRECT_MORPHING.value,                   
            output_format="video/h264-mp4",
            width=project_settings.width,
            height=project_settings.height,
            prompt=description_of_motion                
        )

        create_single_interpolated_clip(
            shot_uuid,
            vid_quality,
            settings,
            variant_count,
            st.session_state[f'{shot_uuid}_backlog_enabled']
        )

        backlog_update = {f'{shot_uuid}_backlog_enabled': False}
        toggle_generate_inference(position, **backlog_update)
        st.rerun()
        
        
        # Placeholder for the logic to generate the clip and update session state as needed
        # This should include calling the function that handles the interpolation process with the updated settings

    # Buttons for adding to queue or backlog, assuming these are still relevant
    btn1, btn2, btn3 = st.columns([1, 1, 1])
    backlog_no_update = {f'{shot_uuid}_backlog_enabled': False}
    with btn1:
        st.button("Add to queue", key="generate_animation_clip", disabled=False, help="Generate the interpolation clip based on the two images and described motion.", on_click=lambda: toggle_generate_inference(position, **backlog_no_update), type="primary", use_container_width=True)

    backlog_update = {f'{shot_uuid}_backlog_enabled': True}
    with btn2:
        st.button("Add to backlog", key="generate_animation_clip_backlog", disabled=False, help="Add the 2-Image Realistic Interpolation to the backlog.", on_click=lambda: toggle_generate_inference(position, **backlog_update), type="secondary")
