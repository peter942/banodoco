import streamlit as st
from ui_components.common_methods import create_working_assets
from repository.local_repo.csv_repo import update_project_setting
from utils.media_processor.video import resize_video
from moviepy.video.io.VideoFileClip import VideoFileClip
import time

def new_project_page():
    a1, a2 = st.columns(2)
    with a1:
        new_project_name = st.text_input("Project name:", value="")
    with a2:
        st.write("")            
    b1, b2, b3 = st.columns(3)
    with b1:
        width = int(st.selectbox("Select video width:", options=["512","683","704","768","1024"], key="video_width"))
        
    with b2:
        height = int(st.selectbox("Select video height:", options=["512","683","704","768","1024"], key="video_height"))
    with b3:
        st.info("We recommend a small size + then scaling up afterwards.")
    
    guidance_type = st.radio("Select guidance type:", options=["Drawing","Images","Video"], help="You can always change this later.", key="guidance_type", horizontal=True)
    audio_options = ["No audio","Attach new audio"]
    if guidance_type == "Video":
        c1, c2 = st.columns(2)
        with c1:               
            uploaded_video = st.file_uploader("Choose a video file:")
        with c2:
            st.write("")
            st.write("")        
            if uploaded_video is not None:
                audio_options.append("Keep audio from original video")                           
            st.info("This video will be resized to match the dimensions above.")
        if uploaded_video is not None:
            resize_this_video = st.checkbox("Resize video to match video dimensions above", value=True)
    else:
        uploaded_video = None
        resize_this_video = False
        
    audio = st.radio("Audio:", audio_options, key="audio",horizontal=True)
    if uploaded_video is None:
        st.info("You can also keep the audio from your original video - just upload the video above and the option will appear.")                

    default_animation_style = st.radio("Select default animation style:", options=["Interpolation","Direct Morphing"], help="You can always change this later.", key="default_animation_style", horizontal=True)

        
    if audio == "Attach new audio":
        d1, d2 = st.columns([4,5])
        with d1:                
            uploaded_audio = st.file_uploader("Choose a audio file:")
        with d2:
            st.write("")
            st.write("")
            st.info("Make sure that this audio is around the same length as your video.")

            
    
    st.write("")
    if st.button("Create New Project"):                
        new_project_name = new_project_name.replace(" ", "_")                      
        create_working_assets(new_project_name)                    
        update_project_setting("width", width, new_project_name)
        update_project_setting("height", height, new_project_name)  
        
        update_project_setting("default_animation_style", default_animation_style, new_project_name)
        update_project_setting("guidance_type", guidance_type, new_project_name)
        
        
        if uploaded_video is not None:
            video_path = f'videos/{new_project_name}/assets/resources/input_videos/{uploaded_video.name}'
            with open(video_path, 'wb') as f:
                f.write(uploaded_video.getbuffer())
            update_project_setting("input_video", uploaded_video.name, new_project_name)
            if resize_this_video == True:
                resize_video(input_path=video_path,output_path=video_path,width=width,height=height) 
            if audio == "Keep audio from original video":
                clip = VideoFileClip(video_path)                    
                clip.audio.write_audiofile(f'videos/{new_project_name}/assets/resources/audio/extracted_audio.mp3')
                update_project_setting("audio", "extracted_audio.mp3", new_project_name) 
        if audio == "Attach new audio":
            if uploaded_audio is not None:
                with open(os.path.join(f"videos/{new_project_name}/assets/resources/audio",uploaded_audio.name),"wb") as f: 
                    f.write(uploaded_audio.getbuffer())
                update_project_setting("audio", uploaded_audio.name, new_project_name)                
                                                    
        st.session_state["project_name"] = new_project_name            
        st.success("Project created! It should be open now. Click into 'Main Process' to get started")
        time.sleep(1)
        st.experimental_rerun()